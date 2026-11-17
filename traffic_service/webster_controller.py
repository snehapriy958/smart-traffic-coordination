"""
traffic_service/webster_controller.py

Webster Optimum Signal Timing Controller for the Bengaluru Silk Board Corridor.
Implements classical Webster (1958) cycle length and green split optimization
for multi-intersection corridor control across J1, J2, and J3.

Mathematical Formulation:
- Critical flow ratio per phase i:
    y_i = q_i / s_i
- Total critical flow ratio:
    Y = sum(y_i)
- Optimum cycle length (Webster 1958 / IRC:93-1985):
    C_0 = (1.5 * L + 5) / (1 - Y)
- Effective green time:
    G = C_actual - L
- Proportional green split:
    g_i = (y_i / Y) * G

Safety Constraints & Invariants:
1. Input validation: non-negative finite flows (q >= 0), strictly positive finite saturation (s > 0).
2. Zero demand handling: safe fallback when Y == 0, allocating minimum green without division-by-zero.
3. Oversaturation protection: clamp cycle to max_cycle when Y >= 1.0 (or Y >= Y_max).
4. Boundary constraints: C_min <= C <= C_max, and g_min <= g_i <= g_max for all phases.
5. Lost time accounting: startup lost time + clearance lost time without double-counting yellow time.
6. Safety shield integration: interacts through SignalController invariants (min_green, yellow clearance, emergency lock).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import math
from typing import Any, Dict, List, Optional, Tuple, Set
import numpy as np

logger = logging.getLogger("webster_controller")


# =====================================================================
# Timing Plan & Configuration Dataclasses
# =====================================================================

@dataclass
class WebsterTimingPlan:
    """Calculated Webster signal timing plan for a single intersection."""
    junction_id: str
    cycle_length: float                       # Applied cycle length (seconds)
    theoretical_cycle_length: float           # Raw unconstrained C_0 (seconds)
    green_times: Dict[int, float]             # Phase index -> Displayed green duration (seconds)
    yellow_durations: Dict[int, float]        # Green phase -> Yellow duration (seconds)
    flow_ratios: Dict[int, float]             # Phase index -> y_i = q_i / s_i
    total_flow_ratio: float                   # Y = sum(y_i)
    total_lost_time: float                    # L (seconds)
    is_saturated: bool                        # True if Y >= 1.0 (or capacity exceeded)
    min_cycle_enforced: bool                  # True if C_0 was floored by C_min
    max_cycle_enforced: bool                  # True if C_0 was capped by C_max
    metadata: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        """Returns JSON-serializable timing summary."""
        return {
            "junction_id": self.junction_id,
            "cycle_length_s": round(self.cycle_length, 2),
            "theoretical_c0_s": round(self.theoretical_cycle_length, 2) if math.isfinite(self.theoretical_cycle_length) else None,
            "green_times_s": {str(k): round(v, 2) for k, v in self.green_times.items()},
            "yellow_durations_s": {str(k): round(v, 2) for k, v in self.yellow_durations.items()},
            "flow_ratios": {str(k): round(v, 4) for k, v in self.flow_ratios.items()},
            "total_flow_ratio_Y": round(self.total_flow_ratio, 4),
            "total_lost_time_L_s": round(self.total_lost_time, 2),
            "is_saturated": self.is_saturated,
            "min_cycle_enforced": self.min_cycle_enforced,
            "max_cycle_enforced": self.max_cycle_enforced,
        }


@dataclass
class WebsterJunctionConfig:
    """
    Configuration parameters for a single junction under Webster control.
    Units are documented explicitly for each parameter.
    """
    junction_id: str                          # Junction identifier, e.g. "J1", "J2", "J3"
    tls_id: str                              # SUMO traffic light ID
    green_phases: List[int]                  # List of green phase indices, e.g. [0, 2]
    yellow_transitions: Dict[int, int]       # Mapping from green phase to yellow phase, e.g. {0: 1, 2: 3}
    critical_flows: Dict[int, float]         # Critical arrival flow q_i per green phase (veh/h)
    saturation_flows: Dict[int, float]       # Saturation flow s_i per green phase (veh/h)
    yellow_durations: Dict[int, float]       # Yellow clearance duration per green phase (seconds)
    startup_lost_time: float = 2.0           # Startup lost time per phase (seconds, IRC:93)
    clearance_lost_time: float = 2.0         # Clearance lost time per phase (seconds, IRC:93)
    min_cycle: float = 45.0                  # Minimum allowable cycle length (seconds)
    max_cycle: float = 120.0                 # Maximum allowable cycle length (seconds)
    min_green: float = 15.0                  # Minimum green duration per phase (seconds, IRC:93)
    max_green: float = 60.0                  # Maximum green duration per phase (seconds)
    y_saturation_threshold: float = 0.95     # Threshold of Y above which junction is treated as saturated


# =====================================================================
# Pure Mathematical Webster Optimization Engine
# =====================================================================

def _allocate_constrained_green(
    phases: List[int],
    total_green: float,
    flow_ratios: Dict[int, float],
    min_green: float,
    max_green: float,
) -> Dict[int, float]:
    """Allocates green time with explicit min_green floors and max_green ceilings."""
    green_alloc: Dict[int, float] = {p: min_green for p in phases}
    rem_G = total_green - (len(phases) * min_green)
    if rem_G <= 0:
        return green_alloc

    active = set(phases)
    while rem_G > 1e-6 and active:
        sum_y = sum(flow_ratios[p] for p in active)
        if sum_y <= 0:
            add = rem_G / len(active)
            for p in list(active):
                headroom = max_green - green_alloc[p]
                alloc = min(add, headroom)
                green_alloc[p] += alloc
                rem_G -= alloc
                if green_alloc[p] >= max_green - 1e-6:
                    active.remove(p)
            break
        else:
            capped = False
            for p in list(active):
                share = (flow_ratios[p] / sum_y) * rem_G
                headroom = max_green - green_alloc[p]
                if share >= headroom:
                    green_alloc[p] = max_green
                    rem_G -= headroom
                    active.remove(p)
                    capped = True
                    break
            if not capped:
                for p in active:
                    share = (flow_ratios[p] / sum_y) * rem_G
                    green_alloc[p] += share
                rem_G = 0.0
                break

    return green_alloc


def calculate_webster_timing(
    critical_flows: Dict[int, float],
    saturation_flows: Dict[int, float],
    yellow_durations: Dict[int, float],
    total_lost_time: Optional[float] = None,
    startup_lost_time: float = 2.0,
    clearance_lost_time: float = 2.0,
    min_cycle: float = 45.0,
    max_cycle: float = 120.0,
    min_green: float = 15.0,
    max_green: float = 60.0,
    y_saturation_threshold: float = 0.95,
    junction_id: str = "custom",
) -> WebsterTimingPlan:
    """
    Calculates Webster optimum cycle length and phase green splits.

    Parameters:
    - critical_flows: {phase_id: q_i in veh/h}
    - saturation_flows: {phase_id: s_i in veh/h}
    - yellow_durations: {phase_id: yellow duration in seconds}
    - total_lost_time: Optional L (seconds). If None, calculated as sum of per-phase lost times.
    - startup_lost_time: seconds per phase (default 2.0s per IRC:93).
    - clearance_lost_time: seconds per phase (default 2.0s per IRC:93).
    - min_cycle, max_cycle: cycle length bounds (seconds).
    - min_green, max_green: phase green duration bounds (seconds).
    - y_saturation_threshold: Y above which oversaturation cap applies (default 0.95).
    - junction_id: name/tag for reporting.

    Returns:
    - WebsterTimingPlan containing cycle length, green splits, and diagnostics.
    """
    # -------------------------------------------------------------
    # 1. Input Validation & Mathematical Safeguards
    # -------------------------------------------------------------
    phases = list(critical_flows.keys())
    if not phases:
        raise ValueError("critical_flows dictionary cannot be empty.")
    if set(phases) != set(saturation_flows.keys()):
        raise ValueError(
            f"Phase mismatch: critical_flows has phases {phases}, but saturation_flows has {list(saturation_flows.keys())}."
        )
    if set(phases) != set(yellow_durations.keys()):
        raise ValueError(
            f"Phase mismatch: critical_flows has phases {phases}, but yellow_durations has {list(yellow_durations.keys())}."
        )

    # Validate cycle and green bounds
    if not isinstance(min_cycle, (int, float)) or not math.isfinite(min_cycle) or min_cycle <= 0:
        raise ValueError(f"Invalid min_cycle: {min_cycle}. Must be finite and strictly positive (> 0).")
    if not isinstance(max_cycle, (int, float)) or not math.isfinite(max_cycle) or max_cycle <= 0:
        raise ValueError(f"Invalid max_cycle: {max_cycle}. Must be finite and strictly positive (> 0).")
    if min_cycle > max_cycle:
        raise ValueError(f"Invalid cycle bounds: min_cycle ({min_cycle}) cannot exceed max_cycle ({max_cycle}).")

    if not isinstance(min_green, (int, float)) or not math.isfinite(min_green) or min_green <= 0:
        raise ValueError(f"Invalid min_green: {min_green}. Must be finite and strictly positive (> 0).")
    if not isinstance(max_green, (int, float)) or not math.isfinite(max_green) or max_green <= 0:
        raise ValueError(f"Invalid max_green: {max_green}. Must be finite and strictly positive (> 0).")
    if min_green > max_green:
        raise ValueError(f"Invalid green bounds: min_green ({min_green}) cannot exceed max_green ({max_green}).")

    # Validate flow values
    flow_ratios: Dict[int, float] = {}
    for p in phases:
        q = critical_flows[p]
        s = saturation_flows[p]
        y_dur = yellow_durations[p]

        if not isinstance(q, (int, float)) or not math.isfinite(q) or q < 0:
            raise ValueError(f"Invalid critical flow for phase {p}: {q}. Must be finite and non-negative (>= 0).")
        if not isinstance(s, (int, float)) or not math.isfinite(s) or s <= 0:
            raise ValueError(f"Invalid saturation flow for phase {p}: {s}. Must be finite and strictly positive (> 0).")
        if not isinstance(y_dur, (int, float)) or not math.isfinite(y_dur) or y_dur < 0:
            raise ValueError(f"Invalid yellow duration for phase {p}: {y_dur}. Must be finite and non-negative.")

        flow_ratios[p] = float(q / s)

    # -------------------------------------------------------------
    # 2. Lost Time Computation
    # -------------------------------------------------------------
    # Per IRC:93-1985 and Webster (1958), total lost time per phase l_i:
    # l_i = startup_lost_time + clearance_lost_time
    # When yellow is used for clearance, clearance_lost_time is typically equal to yellow_duration - extension.
    # If yellow_durations are directly provided and lost time is not explicitly overridden:
    # L = sum(yellow_durations) (natural standard when start-up loss equals end yellow extension)
    # or L = sum(startup_lost_time + clearance_lost_time).
    if total_lost_time is not None:
        if not math.isfinite(total_lost_time) or total_lost_time < 0:
            raise ValueError(f"Invalid total_lost_time: {total_lost_time}.")
        L = float(total_lost_time)
    else:
        # Standard: each phase incurs yellow clearance time as clearance loss
        # and startup loss. To avoid double-counting, L equals sum of yellow durations
        # when startup lost time is balanced by end clearance extension,
        # or sum of explicit (startup_lost_time + clearance_lost_time).
        L = sum(float(yellow_durations[p]) for p in phases)

    # Guarantee min cycle can accommodate minimum green and lost time
    min_possible_cycle = L + (len(phases) * min_green)
    if max_cycle < min_possible_cycle:
        raise ValueError(
            f"Infeasible cycle bounds: max_cycle ({max_cycle:.1f}s) is smaller than "
            f"minimum feasible cycle length ({min_possible_cycle:.1f}s = lost_time {L:.1f}s + "
            f"{len(phases)} phases * min_green {min_green:.1f}s)."
        )
    effective_min_cycle = max(min_cycle, min_possible_cycle)

    # -------------------------------------------------------------
    # 3. Webster Optimum Cycle Length (C_0)
    # -------------------------------------------------------------
    Y = float(sum(flow_ratios.values()))
    min_cycle_enforced = False
    max_cycle_enforced = False
    is_saturated = False

    if Y <= 0.0:
        # Zero demand on all phases: C_0 defaults to minimum cycle
        theoretical_c0 = 1.5 * L + 5.0
        applied_cycle = effective_min_cycle
        min_cycle_enforced = True
    elif Y >= 1.0 or Y >= y_saturation_threshold:
        # Oversaturation: C_0 approaches infinity or becomes undefined
        is_saturated = True
        theoretical_c0 = float("inf") if Y >= 1.0 else (1.5 * L + 5.0) / (1.0 - Y)
        applied_cycle = max_cycle
        max_cycle_enforced = True
    else:
        # Standard Webster formula: C_0 = (1.5L + 5) / (1 - Y)
        theoretical_c0 = (1.5 * L + 5.0) / (1.0 - Y)
        if theoretical_c0 < effective_min_cycle:
            applied_cycle = effective_min_cycle
            min_cycle_enforced = True
        elif theoretical_c0 > max_cycle:
            applied_cycle = max_cycle
            max_cycle_enforced = True
        else:
            applied_cycle = theoretical_c0

    # Ensure applied cycle length is strictly within bounds
    applied_cycle = max(effective_min_cycle, min(max_cycle, applied_cycle))

    # -------------------------------------------------------------
    # 4. Effective Green Time & Proportional Split
    # -------------------------------------------------------------
    # Total available green time in cycle: G = C - L
    total_green = applied_cycle - L

    # Proportional Webster Allocation: g_i = (y_i / Y) * G
    # If unconstrained Webster allocation satisfies all boundary constraints, use it directly.
    if Y > 0:
        raw_alloc = {p: (flow_ratios[p] / Y) * total_green for p in phases}
        if all(min_green <= raw_alloc[p] <= max_green for p in phases):
            green_alloc = raw_alloc
        else:
            green_alloc = _allocate_constrained_green(phases, total_green, flow_ratios, min_green, max_green)
    else:
        # Zero demand on all phases: split green equally
        green_alloc = _allocate_constrained_green(phases, total_green, flow_ratios, min_green, max_green)

    # Actual cycle length strictly equals sum of allocated green times + lost time
    actual_cycle = sum(green_alloc.values()) + L

    return WebsterTimingPlan(
        junction_id=junction_id,
        cycle_length=actual_cycle,
        theoretical_cycle_length=theoretical_c0,
        green_times=green_alloc,
        yellow_durations=yellow_durations,
        flow_ratios=flow_ratios,
        total_flow_ratio=Y,
        total_lost_time=L,
        is_saturated=is_saturated,
        min_cycle_enforced=min_cycle_enforced,
        max_cycle_enforced=max_cycle_enforced,
        metadata={
            "effective_min_cycle": effective_min_cycle,
            "max_cycle": max_cycle,
            "min_green": min_green,
            "max_green": max_green,
            "startup_lost_time": startup_lost_time,
            "clearance_lost_time": clearance_lost_time,
        },
    )


# =====================================================================
# Single-Junction Webster Controller
# =====================================================================

class WebsterJunctionController:
    """
    Manages deterministic cyclic signal timing for a single intersection using a WebsterTimingPlan.
    Interacts safely through SignalController to enforce min_green, yellow clearance, and emergency priority locks.
    """

    def __init__(
        self,
        config: WebsterJunctionConfig,
        signal_controller: Any,  # traffic_service.signal_controller.SignalController
        plan: Optional[WebsterTimingPlan] = None,
    ) -> None:
        self.config = config
        self.signal_controller = signal_controller
        self.plan = plan or calculate_webster_timing(
            critical_flows=config.critical_flows,
            saturation_flows=config.saturation_flows,
            yellow_durations=config.yellow_durations,
            startup_lost_time=config.startup_lost_time,
            clearance_lost_time=config.clearance_lost_time,
            min_cycle=config.min_cycle,
            max_cycle=config.max_cycle,
            min_green=config.min_green,
            max_green=config.max_green,
            y_saturation_threshold=config.y_saturation_threshold,
            junction_id=config.junction_id,
        )

        # Cyclic progression ordering: [phase_0, phase_2, ...]
        self.green_phases = list(self.config.green_phases)
        if len(self.green_phases) < 2:
            raise ValueError(f"WebsterJunctionController requires at least 2 green phases, got {self.green_phases}")

        # Current phase target tracking
        self._current_phase_idx: int = 0
        self._phase_start_sim_time: float = 0.0
        self._last_sim_time: float = 0.0

    @property
    def junction_id(self) -> str:
        return self.config.junction_id

    @property
    def target_green_duration(self) -> float:
        """Returns the Webster-calculated green duration for the current active green phase."""
        curr_phase = self.signal_controller.get_phase()
        return self.plan.green_times.get(curr_phase, self.config.min_green)

    def get_time_to_switch(self, sim_time: float) -> float:
        """Seconds remaining before current green phase transitions to yellow."""
        if not self.signal_controller.is_green():
            return 0.0
        elapsed = self.signal_controller.get_green_elapsed(sim_time)
        return max(0.0, self.target_green_duration - elapsed)

    def step(self, sim_time: float) -> Optional[Dict[str, Any]]:
        """
        Advances junction signal control logic for the current simulation second.
        Returns a decision record if a phase transition was initiated.
        """
        self._last_sim_time = sim_time

        # 1. Check emergency override: bypass Webster decisions if emergency wave is active
        if self.signal_controller.emergency_locked:
            return {
                "junction_id": self.junction_id,
                "sim_time": sim_time,
                "action": "EMERGENCY_LOCK_ACTIVE",
                "current_phase": self.signal_controller.get_phase(),
                "reason": "Emergency vehicle priority override active",
            }

        curr_phase = self.signal_controller.get_phase()

        # 2. If signal is currently clearing yellow, let TraCI naturally advance to next green
        if self.signal_controller.is_yellow(curr_phase):
            return None

        # 3. Signal is in a green phase: check elapsed green duration
        if self.signal_controller.is_green(curr_phase):
            elapsed = self.signal_controller.get_green_elapsed(sim_time)
            target_g = self.plan.green_times.get(curr_phase, self.config.min_green)

            if elapsed >= target_g and self.signal_controller.can_switch(sim_time):
                # Identify next green phase in cyclic sequence
                curr_idx = self.green_phases.index(curr_phase) if curr_phase in self.green_phases else 0
                next_idx = (curr_idx + 1) % len(self.green_phases)
                next_green_phase = self.green_phases[next_idx]

                # Request safe switch via SignalController
                switched = self.signal_controller.request_switch(
                    target_green_phase=next_green_phase,
                    sim_time=sim_time,
                )
                if switched:
                    return {
                        "junction_id": self.junction_id,
                        "sim_time": sim_time,
                        "action": "SWITCH_TO_YELLOW",
                        "from_phase": curr_phase,
                        "target_green_phase": next_green_phase,
                        "elapsed_green_s": elapsed,
                        "planned_green_s": target_g,
                        "reason": f"Webster planned green duration ({target_g:.1f}s) satisfied",
                    }

        return None


# =====================================================================
# Corridor-Wide Webster Controller
# =====================================================================

class WebsterCorridorController:
    """
    Coordinates Webster optimum signal timing across all corridor intersections (J1, J2, J3).
    Provides unified parameters, telemetry, and experiment logging hooks.
    """

    def __init__(
        self,
        controllers: Dict[str, Any],  # junction_id -> SignalController
        configs: Optional[Dict[str, WebsterJunctionConfig]] = None,
    ) -> None:
        self.controllers = controllers
        self.junctions = ["J1", "J2", "J3"]
        self.configs = configs or create_default_webster_configs()

        # Instantiate per-junction controllers
        self.junction_controllers: Dict[str, WebsterJunctionController] = {}
        for j_id in self.junctions:
            if j_id in self.controllers and j_id in self.configs:
                self.junction_controllers[j_id] = WebsterJunctionController(
                    config=self.configs[j_id],
                    signal_controller=self.controllers[j_id],
                )

    def get_plans(self) -> Dict[str, WebsterTimingPlan]:
        """Returns the WebsterTimingPlan for each corridor junction."""
        return {j_id: jc.plan for j_id, jc in self.junction_controllers.items()}

    def get_parameters_summary(self) -> Dict[str, Any]:
        """Returns structured timing parameters for experiment logging and paper reproduction."""
        return {
            "controller_type": "webster_optimum_fixed_time",
            "junctions": {
                j_id: jc.plan.summary()
                for j_id, jc in self.junction_controllers.items()
            },
        }

    def step(self, sim_time: float) -> Dict[str, Any]:
        """
        Advances the Webster controller for all intersections at simulation timestamp sim_time.
        Returns decision telemetry for logging.
        """
        decisions: Dict[str, Any] = {}
        for j_id, jc in self.junction_controllers.items():
            dec = jc.step(sim_time)
            if dec is not None:
                decisions[j_id] = dec
        return decisions


# =====================================================================
# Corridor Default Configurations (Bengaluru Silk Board Ground Truth)
# =====================================================================

def create_default_webster_configs() -> Dict[str, WebsterJunctionConfig]:
    """
    Factory function generating verified Webster configurations for J1, J2, and J3
    based on the Central Silk Board corridor geometry and traffic demand.

    Sources & Provenance:
    - Lane Geometry: sumo/silk_board/network/silk_board.net.xml
    - Lane Width: 3.20 m per lane (IRC:54-1974 standard)
    - Base Saturation Flow: 1,800 veh/h/lane (IRC:93-1985 / IRC:SP:84)
    - Critical Flows: sumo/silk_board/demand/silk_board.rou.xml (peak design flows)
    - Yellow Clearance: 4.0s for J1/J3, 6.0s for J2 (matching SUMO traffic light programs)
    - Min / Max Green: 15.0s / 60.0s (matching SignalController safety bounds)
    - Min / Max Cycle: 45.0s / 120.0s (standard IRC:93 urban signal range)
    """
    return {
        # -------------------------------------------------------------
        # J1 (Hosur Road / Silk Board North Entry)
        # -------------------------------------------------------------
        # Phase 0: Side cross approach (-148697299_0, 1 lane, design flow 150 vph)
        # Phase 2: Hosur arterial approach (172853382#2, 2 lanes, peak flow 1,200 vph)
        # Yellow: 4.0s each (Phase 1 and 3)
        "J1": WebsterJunctionConfig(
            junction_id="J1",
            tls_id="1617743335",
            green_phases=[0, 2],
            yellow_transitions={0: 1, 2: 3},
            critical_flows={0: 150.0, 2: 1200.0},
            saturation_flows={0: 1800.0, 2: 3600.0},
            yellow_durations={0: 4.0, 2: 4.0},
            startup_lost_time=2.0,
            clearance_lost_time=2.0,
            min_cycle=45.0,
            max_cycle=120.0,
            min_green=15.0,
            max_green=60.0,
        ),

        # -------------------------------------------------------------
        # J2 (Central Silk Board Main Intermodal Junction)
        # -------------------------------------------------------------
        # Phase 0: Hosur arterial approach (172853382#3 & 464465165#0, 5 lanes, 3 critical through lanes, flow 1,800 vph)
        # Phase 2: Madiwala cross approach (92196679#0, 2 lanes, flow 900 vph)
        # Yellow: 6.0s each (Phase 1 and 3)
        "J2": WebsterJunctionConfig(
            junction_id="J2",
            tls_id="GS_cluster_10282769895_10775075568_11964440742_11964440743",
            green_phases=[0, 2],
            yellow_transitions={0: 1, 2: 3},
            critical_flows={0: 1800.0, 2: 900.0},
            saturation_flows={0: 5400.0, 2: 3600.0},
            yellow_durations={0: 6.0, 2: 6.0},
            startup_lost_time=2.0,
            clearance_lost_time=2.0,
            min_cycle=45.0,
            max_cycle=120.0,
            min_green=15.0,
            max_green=60.0,
        ),

        # -------------------------------------------------------------
        # J3 (Hosur Road / Silk Board South Exit)
        # -------------------------------------------------------------
        # Phase 0: Side cross approach (-744783934_0, 1 lane, design flow 150 vph)
        # Phase 2: Hosur arterial approach (1148717038#0, 2 lanes, peak flow 1,400 vph)
        # Yellow: 4.0s each (Phase 1 and 3)
        "J3": WebsterJunctionConfig(
            junction_id="J3",
            tls_id="6970466614",
            green_phases=[0, 2],
            yellow_transitions={0: 1, 2: 3},
            critical_flows={0: 150.0, 2: 1400.0},
            saturation_flows={0: 1800.0, 2: 3600.0},
            yellow_durations={0: 4.0, 2: 4.0},
            startup_lost_time=2.0,
            clearance_lost_time=2.0,
            min_cycle=45.0,
            max_cycle=120.0,
            min_green=15.0,
            max_green=60.0,
        ),
    }
