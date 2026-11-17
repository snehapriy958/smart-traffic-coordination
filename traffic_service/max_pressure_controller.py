"""
traffic_service/max_pressure_controller.py

Varaiya Max-Pressure Traffic Signal Controller.
Implements network-level queue-differential feedback control:
  Pressure(phase) = Upstream Queue Contribution - Downstream Queue Contribution
Provably stabilizes queue networks and maximizes network throughput while respecting
civil engineering safety constraints (min_green, max_green, yellow clearance, emergency preemption).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .signal_controller import SignalController

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MaxPressureMovement:
    """Represents an origin-destination movement served by a green phase."""
    upstream_junction: str
    upstream_approach: str
    downstream_junction: Optional[str] = None
    downstream_approach: Optional[str] = None
    weight: float = 1.0  # Movement saturation flow or service priority weight


@dataclass(frozen=True)
class MaxPressurePhaseConfig:
    """Configuration of a signal phase in Max-Pressure control."""
    phase_id: int
    movements: List[MaxPressureMovement]
    min_green: float = 15.0
    max_green: float = 60.0


@dataclass(frozen=True)
class MaxPressureJunctionConfig:
    """Junction-level configuration for Max-Pressure controller."""
    junction_id: str
    tls_id: str
    green_phases: List[int]
    yellow_transitions: Dict[int, int]
    yellow_durations: Dict[int, float]
    phases: Dict[int, MaxPressurePhaseConfig]
    default_priority_phase: int = 0


class MaxPressureJunctionController:
    """
    Evaluates queue pressure for each phase at an individual intersection
    and selects the maximum-pressure phase while enforcing min_green and max_green.
    """

    def __init__(
        self,
        config: MaxPressureJunctionConfig,
        signal_controller: SignalController,
        step_length: float = 1.0,
    ) -> None:
        self.config = config
        self.signal_controller = signal_controller
        self.step_length = step_length
        self.junction_id = config.junction_id

        # Validate configuration
        if not config.green_phases:
            raise ValueError(f"Junction {config.junction_id}: green_phases cannot be empty.")
        for p in config.green_phases:
            if p not in config.phases:
                raise ValueError(f"Junction {config.junction_id}: missing MaxPressurePhaseConfig for phase {p}.")
            if p not in config.yellow_transitions:
                raise ValueError(f"Junction {config.junction_id}: missing yellow transition for phase {p}.")
            if p not in config.yellow_durations:
                raise ValueError(f"Junction {config.junction_id}: missing yellow duration for phase {p}.")

        self._last_phase: Optional[int] = None
        self._last_pressure_evaluations: Dict[int, float] = {}

    @property
    def last_pressures(self) -> Dict[int, float]:
        """Returns the most recent calculated phase pressures."""
        return self._last_pressure_evaluations

    def compute_phase_pressure(
        self,
        phase_id: int,
        all_junction_queues: Dict[str, Dict[str, int]],
    ) -> float:
        """
        Calculates the net pressure for phase_id:
        Pressure = sum_{m in phase} weight * (Q_upstream - Q_downstream)
        """
        p_cfg = self.config.phases.get(phase_id)
        if not p_cfg:
            return 0.0

        total_pressure = 0.0
        for mov in p_cfg.movements:
            # Upstream queue
            up_q_dict = all_junction_queues.get(mov.upstream_junction, {})
            up_q = float(up_q_dict.get(mov.upstream_approach, 0))

            # Downstream queue
            down_q = 0.0
            if mov.downstream_junction and mov.downstream_approach:
                down_q_dict = all_junction_queues.get(mov.downstream_junction, {})
                down_q = float(down_q_dict.get(mov.downstream_approach, 0))

            # Max-Pressure gradient
            pressure = mov.weight * (up_q - down_q)
            total_pressure += pressure

        return total_pressure

    def step(
        self,
        sim_time: float,
        all_junction_queues: Dict[str, Dict[str, int]],
    ) -> Optional[Dict[str, Any]]:
        """
        Executes Max-Pressure control decision at timestamp sim_time.

        Parameters:
        - sim_time: Simulation timestamp in seconds.
        - all_junction_queues: {junction_id: {approach_name: queue_count}}

        Returns:
        - Telemetry dict if a switch transition was requested, else None.
        """
        # 1. Emergency Preemption Check
        if self.signal_controller.emergency_locked:
            return {
                "junction_id": self.junction_id,
                "sim_time": sim_time,
                "action": "EMERGENCY_LOCK_ACTIVE",
                "current_phase": self.signal_controller.get_phase(),
                "reason": "Emergency vehicle priority override active",
            }

        curr_phase = self.signal_controller.get_phase()

        # 2. Allow Yellow Clearance to Complete Uninterrupted
        if self.signal_controller.is_yellow(curr_phase):
            return None

        # 3. Check Green Phase
        if curr_phase not in self.config.phases:
            return None

        p_cfg = self.config.phases[curr_phase]
        elapsed = self.signal_controller.get_green_elapsed(sim_time)

        # 4. Compute Pressures for All Configured Green Phases
        pressures: Dict[int, float] = {}
        for p in self.config.green_phases:
            pressures[p] = self.compute_phase_pressure(p, all_junction_queues)
        self._last_pressure_evaluations = pressures

        # 5. Determine Target Maximum-Pressure Phase
        # Tie-breaking rules:
        # 1) If an opposing phase has strictly greater pressure: candidate for switch.
        # 2) If pressures are equal, favor the current phase (hysteresis / anti-chatter).
        # 3) If all pressures are <= 0, favor the current phase or default priority phase.
        max_p = max(pressures.values())
        curr_p_val = pressures[curr_phase]

        # Candidate target phase
        if max_p <= 0.0:
            target_phase = curr_phase  # Rest in current phase if network is empty
        elif max_p > curr_p_val:
            # Pick phase with highest pressure (lowest index for deterministic tie)
            candidates = [p for p, val in pressures.items() if math.isclose(val, max_p, abs_tol=1e-5)]
            target_phase = min(candidates)
        else:
            target_phase = curr_phase

        # 6. Minimum Green Protection: CANNOT switch before min_green
        if elapsed < p_cfg.min_green:
            return None

        # 7. Check Switching Capability
        if not self.signal_controller.can_switch(sim_time):
            return None

        # 8. Maximum Green Forced Switch (Anti-Starvation Bound)
        if elapsed >= p_cfg.max_green:
            other_phases = [p for p in self.config.green_phases if p != curr_phase]
            if other_phases:
                # Force switch to best opposing phase
                opposing_pressures = {p: pressures[p] for p in other_phases}
                best_opposing_p = max(opposing_pressures.values())
                candidates = [p for p, val in opposing_pressures.items() if math.isclose(val, best_opposing_p, abs_tol=1e-5)]
                target_phase = min(candidates)

        # 9. Execute Transition if Target Phase Differs from Current Phase
        if target_phase != curr_phase:
            switched = self.signal_controller.request_switch(target_phase, sim_time)
            if switched:
                logger.info(
                    f"[MAX-PRESSURE] Junction={self.junction_id} | SimTime={sim_time:.1f}s | "
                    f"Switched {curr_phase} (P={curr_p_val:.1f}) -> {target_phase} (P={pressures[target_phase]:.1f}) | "
                    f"Elapsed={elapsed:.1f}s | AllPressures={pressures}"
                )
                return {
                    "junction_id": self.junction_id,
                    "sim_time": sim_time,
                    "action": "SWITCH_TO_YELLOW",
                    "from_phase": curr_phase,
                    "target_green_phase": target_phase,
                    "current_phase_pressure": curr_p_val,
                    "target_phase_pressure": pressures[target_phase],
                    "all_pressures": pressures,
                    "elapsed_green_s": elapsed,
                    "reason": "Max-Pressure gradient satisfied",
                }

        return None


class MaxPressureCorridorController:
    """
    Coordinates Max-Pressure signal control across the Silk Board corridor (J1, J2, J3).
    Collects network-wide approach queues and dispatches pressure decisions at each junction.
    """

    def __init__(
        self,
        controllers: Dict[str, SignalController],
        configs: Optional[Dict[str, MaxPressureJunctionConfig]] = None,
        step_length: float = 1.0,
    ) -> None:
        self.controllers = controllers
        self.step_length = step_length
        self.junctions = ["J1", "J2", "J3"]
        self.configs = configs or create_default_max_pressure_configs()

        self.junction_controllers: Dict[str, MaxPressureJunctionController] = {}
        for j_id in self.junctions:
            if j_id in self.controllers and j_id in self.configs:
                self.junction_controllers[j_id] = MaxPressureJunctionController(
                    config=self.configs[j_id],
                    signal_controller=self.controllers[j_id],
                    step_length=self.step_length,
                )

    def step(
        self,
        sim_time: float,
        states: Dict[str, Any],  # junction_id -> IntersectionState
    ) -> Dict[str, Any]:
        """
        Advances Max-Pressure controllers for all junctions using current corridor queue state.
        """
        # Assemble global queue matrix: {junction_id: {approach_name: count}}
        all_queues: Dict[str, Dict[str, int]] = {}
        for j_id, state in states.items():
            all_queues[j_id] = state.approach_queues

        decisions: Dict[str, Any] = {}
        for j_id, jc in self.junction_controllers.items():
            dec = jc.step(sim_time=sim_time, all_junction_queues=all_queues)
            if dec is not None:
                decisions[j_id] = dec
        return decisions

    def get_parameters_summary(self) -> Dict[str, Any]:
        """Returns structured configuration summary of the Max-Pressure controller."""
        summary = {}
        for j_id, jc in self.junction_controllers.items():
            summary[j_id] = {
                "junction_id": j_id,
                "phases": {
                    p_id: {
                        "movements": [
                            {
                                "upstream": f"{m.upstream_junction}:{m.upstream_approach}",
                                "downstream": f"{m.downstream_junction}:{m.downstream_approach}" if m.downstream_junction else "EXIT",
                                "weight": m.weight,
                            }
                            for m in p_cfg.movements
                        ],
                        "min_green": p_cfg.min_green,
                        "max_green": p_cfg.max_green,
                    }
                    for p_id, p_cfg in jc.config.phases.items()
                },
                "yellow_durations": jc.config.yellow_durations,
            }
        return {"controller_type": "max_pressure_varaiya", "junctions": summary}


def create_default_max_pressure_configs() -> Dict[str, MaxPressureJunctionConfig]:
    """
    Factory creating verified Max-Pressure configs for the Bengaluru Silk Board corridor.

    Network Flow Topology:
    - J1:
      - Phase 0 (side_cross): Upstream J1:side_cross -> Downstream Exit (Q_down = 0)
      - Phase 2 (corridor_hosur): Upstream J1:corridor_hosur -> Downstream J2:corridor_hosur
    - J2:
      - Phase 0 (corridor_hosur): Upstream J2:corridor_hosur -> Downstream J3:corridor_hosur
      - Phase 2 (madiwala): Upstream J2:madiwala -> Downstream Exit (Q_down = 0)
    - J3:
      - Phase 0 (side_cross): Upstream J3:side_cross -> Downstream Exit (Q_down = 0)
      - Phase 2 (corridor_hosur): Upstream J3:corridor_hosur -> Downstream Corridor Exit (Q_down = 0)

    Safety Parameters:
    - Min Green: 15.0s (SignalController safety invariant)
    - Max Green: 60.0s (SignalController safety invariant)
    - Yellow Durations: J1=4.0s, J2=6.0s, J3=4.0s (SUMO network ground truth)
    """
    return {
        "J1": MaxPressureJunctionConfig(
            junction_id="J1",
            tls_id="1617743335",
            green_phases=[0, 2],
            yellow_transitions={0: 1, 2: 3},
            yellow_durations={0: 4.0, 2: 4.0},
            phases={
                0: MaxPressurePhaseConfig(
                    phase_id=0,
                    movements=[
                        MaxPressureMovement(
                            upstream_junction="J1",
                            upstream_approach="side_cross",
                            downstream_junction=None,
                            downstream_approach=None,
                            weight=1.0,
                        )
                    ],
                    min_green=15.0,
                    max_green=60.0,
                ),
                2: MaxPressurePhaseConfig(
                    phase_id=2,
                    movements=[
                        MaxPressureMovement(
                            upstream_junction="J1",
                            upstream_approach="corridor_hosur",
                            downstream_junction="J2",
                            downstream_approach="corridor_hosur",
                            weight=1.0,
                        )
                    ],
                    min_green=15.0,
                    max_green=60.0,
                ),
            },
            default_priority_phase=2,
        ),
        "J2": MaxPressureJunctionConfig(
            junction_id="J2",
            tls_id="GS_cluster_10282769895_10775075568_11964440742_11964440743",
            green_phases=[0, 2],
            yellow_transitions={0: 1, 2: 3},
            yellow_durations={0: 6.0, 2: 6.0},
            phases={
                0: MaxPressurePhaseConfig(
                    phase_id=0,
                    movements=[
                        MaxPressureMovement(
                            upstream_junction="J2",
                            upstream_approach="corridor_hosur",
                            downstream_junction="J3",
                            downstream_approach="corridor_hosur",
                            weight=1.0,
                        )
                    ],
                    min_green=15.0,
                    max_green=60.0,
                ),
                2: MaxPressurePhaseConfig(
                    phase_id=2,
                    movements=[
                        MaxPressureMovement(
                            upstream_junction="J2",
                            upstream_approach="madiwala",
                            downstream_junction=None,
                            downstream_approach=None,
                            weight=1.0,
                        )
                    ],
                    min_green=15.0,
                    max_green=60.0,
                ),
            },
            default_priority_phase=0,
        ),
        "J3": MaxPressureJunctionConfig(
            junction_id="J3",
            tls_id="6970466614",
            green_phases=[0, 2],
            yellow_transitions={0: 1, 2: 3},
            yellow_durations={0: 4.0, 2: 4.0},
            phases={
                0: MaxPressurePhaseConfig(
                    phase_id=0,
                    movements=[
                        MaxPressureMovement(
                            upstream_junction="J3",
                            upstream_approach="side_cross",
                            downstream_junction=None,
                            downstream_approach=None,
                            weight=1.0,
                        )
                    ],
                    min_green=15.0,
                    max_green=60.0,
                ),
                2: MaxPressurePhaseConfig(
                    phase_id=2,
                    movements=[
                        MaxPressureMovement(
                            upstream_junction="J3",
                            upstream_approach="corridor_hosur",
                            downstream_junction=None,
                            downstream_approach=None,
                            weight=1.0,
                        )
                    ],
                    min_green=15.0,
                    max_green=60.0,
                ),
            },
            default_priority_phase=2,
        ),
    }
