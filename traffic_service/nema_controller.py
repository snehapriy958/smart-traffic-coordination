"""
traffic_service/nema_controller.py

NEMA TS 2 Actuated Traffic Signal Controller.
Implements vehicle-actuated phase operation with:
- Minimum green enforcement (G_min)
- Vehicle passage time / extension timer (gap-out logic)
- Maximum green safety limits (G_max / max-out logic)
- Conflicting call registration and priority sequencing
- Recall modes (None, Min, Max, Coordinated arterial recall)
- Mandatory yellow clearance transitions and emergency preemption integration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .signal_controller import SignalController

logger = logging.getLogger(__name__)


class NEMARecallMode(str, Enum):
    """NEMA Phase Recall Modes."""
    NONE = "NONE"                # Drops green when gap-out occurs and conflicting call exists
    MIN = "MIN"                  # Automatically recalls phase to minimum green each cycle
    MAX = "MAX"                  # Forces phase to run to maximum green each cycle
    COORDINATED = "COORDINATED"  # Rest in green on coordinated phase if no conflicting calls


@dataclass(frozen=True)
class NEMAPhaseConfig:
    """Configuration for an individual actuated phase."""
    phase_id: int
    approach_name: str
    min_green: float = 15.0
    max_green: float = 60.0
    passage_time: float = 3.0    # Vehicle extension timer (seconds)
    recall_mode: NEMARecallMode = NEMARecallMode.NONE


@dataclass(frozen=True)
class NEMAJunctionConfig:
    """Configuration for a multi-phase NEMA actuated intersection."""
    junction_id: str
    tls_id: str
    green_phases: List[int]
    yellow_transitions: Dict[int, int]
    yellow_durations: Dict[int, float]
    phases: Dict[int, NEMAPhaseConfig]
    coordinated_phase: Optional[int] = None


class NEMAJunctionController:
    """
    Controls an individual traffic light using NEMA TS 2 actuated logic.
    Maintains vehicle extension timers, detects gap-out/max-out conditions,
    and requests safe transitions via SignalController.
    """

    def __init__(
        self,
        config: NEMAJunctionConfig,
        signal_controller: SignalController,
        step_length: float = 1.0,
    ) -> None:
        self.config = config
        self.signal_controller = signal_controller
        self.step_length = step_length
        self.junction_id = config.junction_id

        # Validate phase configurations
        if not config.green_phases:
            raise ValueError(f"Junction {config.junction_id}: green_phases cannot be empty.")
        for p in config.green_phases:
            if p not in config.phases:
                raise ValueError(f"Junction {config.junction_id}: missing NEMAPhaseConfig for phase {p}.")
            if p not in config.yellow_transitions:
                raise ValueError(f"Junction {config.junction_id}: missing yellow transition for phase {p}.")
            if p not in config.yellow_durations:
                raise ValueError(f"Junction {config.junction_id}: missing yellow duration for phase {p}.")

        # Runtime actuation state
        self._extension_timer: float = 0.0
        self._last_active_phase: Optional[int] = None
        self._phase_start_time: float = 0.0
        self._last_termination_reason: Optional[str] = None
        self._conflicting_calls: Dict[int, bool] = {p: False for p in config.green_phases}

    @property
    def extension_timer(self) -> float:
        """Remaining passage time extension in seconds."""
        return self._extension_timer

    @property
    def last_termination_reason(self) -> Optional[str]:
        """Reason for the last phase switch: 'GAP_OUT', 'MAX_OUT', 'RECALL', 'FORCE_OFF'."""
        return self._last_termination_reason

    def register_actuation(self, phase_id: int) -> None:
        """Simulates detector actuation, resetting extension timer to passage time."""
        if phase_id in self.config.phases:
            p_cfg = self.config.phases[phase_id]
            self._extension_timer = p_cfg.passage_time

    def get_phase_config(self, phase_id: int) -> Optional[NEMAPhaseConfig]:
        """Returns the configuration for the specified phase."""
        return self.config.phases.get(phase_id)

    def step(
        self,
        sim_time: float,
        approach_queues: Dict[str, int],
        vehicle_counts: Optional[Dict[str, int]] = None,
        active_detections: Optional[Dict[str, bool]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Advances NEMA actuation logic by one simulation step.

        Parameters:
        - sim_time: Current simulation timestamp (seconds).
        - approach_queues: {approach_name: queue_count}
        - vehicle_counts: {approach_name: active_approaching_vehicle_count}
        - active_detections: {approach_name: bool_has_vehicle_presence}

        Returns:
        - Telemetry dict if a state decision was executed, or None.
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

        # 2. If signal is currently clearing yellow, allow clearance without intervention
        if self.signal_controller.is_yellow(curr_phase):
            return None

        # 3. Verify signal is in a valid configured green phase
        if curr_phase not in self.config.phases:
            return None

        p_cfg = self.config.phases[curr_phase]

        # Reset timers on phase onset
        if self._last_active_phase != curr_phase:
            self._last_active_phase = curr_phase
            self._phase_start_time = sim_time
            self._extension_timer = p_cfg.passage_time
            self._last_termination_reason = None

        elapsed = self.signal_controller.get_green_elapsed(sim_time)

        # 4. Detect Vehicle Actuations on Current Phase Approach
        has_detection = False
        if active_detections and active_detections.get(p_cfg.approach_name, False):
            has_detection = True
        elif approach_queues.get(p_cfg.approach_name, 0) > 0:
            has_detection = True
        elif vehicle_counts and vehicle_counts.get(p_cfg.approach_name, 0) > 0:
            has_detection = True

        if has_detection:
            # Vehicle detected: extend green by passage time
            self._extension_timer = p_cfg.passage_time
        else:
            # No vehicle: decrement extension timer
            self._extension_timer = max(0.0, self._extension_timer - self.step_length)

        # 5. Register Conflicting Calls on Other Green Phases
        other_phases = [p for p in self.config.green_phases if p != curr_phase]
        has_conflicting_call = False
        target_phase: Optional[int] = None

        for op in other_phases:
            op_cfg = self.config.phases[op]
            op_queue = approach_queues.get(op_cfg.approach_name, 0)
            op_count = vehicle_counts.get(op_cfg.approach_name, 0) if vehicle_counts else 0
            op_presence = active_detections.get(op_cfg.approach_name, False) if active_detections else False

            # Call registered if queue > 0, vehicles approaching, or recall mode is MIN/MAX
            call_registered = (
                op_queue > 0
                or op_count > 0
                or op_presence
                or op_cfg.recall_mode in (NEMARecallMode.MIN, NEMARecallMode.MAX)
            )
            self._conflicting_calls[op] = call_registered
            if call_registered and target_phase is None:
                has_conflicting_call = True
                target_phase = op

        # 6. Minimum Green Guarantee: Cannot terminate phase before min_green
        if elapsed < p_cfg.min_green:
            return None

        # 7. Check Switching Capability
        if not self.signal_controller.can_switch(sim_time):
            return None

        # 8. Evaluate NEMA Phase Termination Conditions
        should_switch = False
        termination_reason = "HOLD"

        if has_conflicting_call and target_phase is not None:
            if elapsed >= p_cfg.max_green:
                # Maximum Green Reached: MAX_OUT
                should_switch = True
                termination_reason = "MAX_OUT"
            elif self._extension_timer <= 1e-6:
                # Extension Expired: GAP_OUT
                should_switch = True
                termination_reason = "GAP_OUT"
        else:
            # No conflicting call registered
            if p_cfg.recall_mode == NEMARecallMode.MAX and elapsed >= p_cfg.max_green:
                # Max Recall without conflicting vehicles
                should_switch = True
                termination_reason = "MAX_RECALL"
                target_phase = other_phases[0] if other_phases else curr_phase
            elif self.config.coordinated_phase == curr_phase:
                # Coordinated phase rests in green
                termination_reason = "REST_IN_GREEN"
            elif self._extension_timer <= 1e-6 and p_cfg.recall_mode == NEMARecallMode.NONE:
                # Side street with no vehicles and no call: return to coordinated phase
                if self.config.coordinated_phase is not None and self.config.coordinated_phase != curr_phase:
                    should_switch = True
                    target_phase = self.config.coordinated_phase
                    termination_reason = "REST_ON_COORDINATED"

        # 9. Execute Transition if Required
        if should_switch and target_phase is not None and target_phase != curr_phase:
            switched = self.signal_controller.request_switch(target_phase, sim_time)
            if switched:
                self._last_termination_reason = termination_reason
                logger.info(
                    f"[NEMA ACTUATION] Junction={self.junction_id} | SimTime={sim_time:.1f}s | "
                    f"Phase {curr_phase} -> {target_phase} | Reason={termination_reason} | "
                    f"Elapsed={elapsed:.1f}s (Min={p_cfg.min_green:.1f}s, Max={p_cfg.max_green:.1f}s, Ext={self._extension_timer:.1f}s)"
                )
                return {
                    "junction_id": self.junction_id,
                    "sim_time": sim_time,
                    "action": "SWITCH_TO_YELLOW",
                    "from_phase": curr_phase,
                    "target_green_phase": target_phase,
                    "termination_reason": termination_reason,
                    "elapsed_green_s": elapsed,
                    "min_green_s": p_cfg.min_green,
                    "max_green_s": p_cfg.max_green,
                    "extension_timer_s": self._extension_timer,
                }

        return None


class NEMACorridorController:
    """
    Coordinates NEMA TS 2 actuated control across all corridor intersections (J1, J2, J3).
    """

    def __init__(
        self,
        controllers: Dict[str, SignalController],
        configs: Optional[Dict[str, NEMAJunctionConfig]] = None,
        step_length: float = 1.0,
    ) -> None:
        self.controllers = controllers
        self.step_length = step_length
        self.junctions = ["J1", "J2", "J3"]
        self.configs = configs or create_default_nema_configs()

        self.junction_controllers: Dict[str, NEMAJunctionController] = {}
        for j_id in self.junctions:
            if j_id in self.controllers and j_id in self.configs:
                self.junction_controllers[j_id] = NEMAJunctionController(
                    config=self.configs[j_id],
                    signal_controller=self.controllers[j_id],
                    step_length=self.step_length,
                )

    def step(
        self,
        sim_time: float,
        states: Dict[str, Any],  # junction_id -> IntersectionState
    ) -> Dict[str, Any]:
        """Advances NEMA controllers for all junctions using current simulation state observations."""
        decisions: Dict[str, Any] = {}
        for j_id, jc in self.junction_controllers.items():
            state = states.get(j_id)
            if state is not None:
                queues = state.approach_queues
                counts = getattr(state, "approach_vehicle_counts", {})
                dec = jc.step(
                    sim_time=sim_time,
                    approach_queues=queues,
                    vehicle_counts=counts,
                )
                if dec is not None:
                    decisions[j_id] = dec
        return decisions

    def get_parameters_summary(self) -> Dict[str, Any]:
        """Returns structured NEMA timing configuration summary."""
        summary = {}
        for j_id, jc in self.junction_controllers.items():
            summary[j_id] = {
                "junction_id": j_id,
                "coordinated_phase": jc.config.coordinated_phase,
                "phases": {
                    p_id: {
                        "approach": p_cfg.approach_name,
                        "min_green": p_cfg.min_green,
                        "max_green": p_cfg.max_green,
                        "passage_time": p_cfg.passage_time,
                        "recall_mode": p_cfg.recall_mode.value,
                    }
                    for p_id, p_cfg in jc.config.phases.items()
                },
                "yellow_durations": jc.config.yellow_durations,
            }
        return {"controller_type": "nema_actuated_ts2", "junctions": summary}


def create_default_nema_configs() -> Dict[str, NEMAJunctionConfig]:
    """
    Factory creating verified NEMA actuated configs for the Silk Board corridor.

    Junction Mapping:
    - J1: Phase 0 (side_cross, NONE recall), Phase 2 (corridor_hosur, COORDINATED recall)
    - J2: Phase 0 (corridor_hosur, COORDINATED recall), Phase 2 (madiwala, NONE recall)
    - J3: Phase 0 (side_cross, NONE recall), Phase 2 (corridor_hosur, COORDINATED recall)

    Parameters:
    - Min Green: 15.0s (IRC:93 / SignalController safety invariant)
    - Max Green: 60.0s (SignalController safety invariant)
    - Passage Time: 3.0s (Standard vehicle headway clearance)
    - Yellow Clearance: J1=4.0s, J2=6.0s, J3=4.0s (Matching SUMO net ground truth)
    """
    return {
        "J1": NEMAJunctionConfig(
            junction_id="J1",
            tls_id="1617743335",
            green_phases=[0, 2],
            yellow_transitions={0: 1, 2: 3},
            yellow_durations={0: 4.0, 2: 4.0},
            phases={
                0: NEMAPhaseConfig(
                    phase_id=0,
                    approach_name="side_cross",
                    min_green=15.0,
                    max_green=60.0,
                    passage_time=3.0,
                    recall_mode=NEMARecallMode.NONE,
                ),
                2: NEMAPhaseConfig(
                    phase_id=2,
                    approach_name="corridor_hosur",
                    min_green=15.0,
                    max_green=60.0,
                    passage_time=3.0,
                    recall_mode=NEMARecallMode.COORDINATED,
                ),
            },
            coordinated_phase=2,
        ),
        "J2": NEMAJunctionConfig(
            junction_id="J2",
            tls_id="GS_cluster_10282769895_10775075568_11964440742_11964440743",
            green_phases=[0, 2],
            yellow_transitions={0: 1, 2: 3},
            yellow_durations={0: 6.0, 2: 6.0},
            phases={
                0: NEMAPhaseConfig(
                    phase_id=0,
                    approach_name="corridor_hosur",
                    min_green=15.0,
                    max_green=60.0,
                    passage_time=3.0,
                    recall_mode=NEMARecallMode.COORDINATED,
                ),
                2: NEMAPhaseConfig(
                    phase_id=2,
                    approach_name="madiwala",
                    min_green=15.0,
                    max_green=60.0,
                    passage_time=3.0,
                    recall_mode=NEMARecallMode.NONE,
                ),
            },
            coordinated_phase=0,
        ),
        "J3": NEMAJunctionConfig(
            junction_id="J3",
            tls_id="6970466614",
            green_phases=[0, 2],
            yellow_transitions={0: 1, 2: 3},
            yellow_durations={0: 4.0, 2: 4.0},
            phases={
                0: NEMAPhaseConfig(
                    phase_id=0,
                    approach_name="side_cross",
                    min_green=15.0,
                    max_green=60.0,
                    passage_time=3.0,
                    recall_mode=NEMARecallMode.NONE,
                ),
                2: NEMAPhaseConfig(
                    phase_id=2,
                    approach_name="corridor_hosur",
                    min_green=15.0,
                    max_green=60.0,
                    passage_time=3.0,
                    recall_mode=NEMARecallMode.COORDINATED,
                ),
            },
            coordinated_phase=2,
        ),
    }
