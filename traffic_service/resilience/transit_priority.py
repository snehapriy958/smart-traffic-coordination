"""
traffic_service/resilience/transit_priority.py

Transit Signal Priority (TSP) manager for multi-modal corridor operations.
Detects approaching BMTC buses and grants conditional green extensions (+5.0s)
while strictly respecting maximum-green bounds (<=60.0s), yellow clearance integrity,
and yielding unconditional priority to emergency vehicles.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
import traci

from traffic_service.signal_controller import SignalController

logger = logging.getLogger("transit_priority")


@dataclass
class TSPEvent:
    """Record of a Transit Signal Priority evaluation event."""
    sim_time: float
    junction_id: str
    phase: int
    bus_id: str
    distance_to_stop_m: float
    bus_speed_mps: float
    eta_s: float
    granted: bool
    reason: str
    extended_seconds: float = 0.0


@dataclass
class TSPSummary:
    """Aggregated Transit Signal Priority performance metrics."""
    total_requests: int
    granted_requests: int
    rejected_requests: int
    grant_rate: float
    total_extended_time_s: float
    emergency_preemptions_blocked_tsp: int
    max_green_bound_hits: int
    buses_assisted: List[str] = field(default_factory=list)


class TransitSignalPriorityManager:
    """
    Conditional green-extension Transit Signal Priority (TSP) controller for BMTC buses.
    
    Operating Rules:
    1. Disabled by default; selectively enabled for multi-modal evaluation experiments.
    2. Eligible vehicles: strictly BMTC buses (vClass == 'bus' or type contains 'bus').
    3. Spatial window: bus distance to stop line <= detection_distance_m (150m).
    4. Temporal window: bus ETA to stop line <= max_bus_eta_s (5.0s).
    5. Phase status: active phase must be green and elapsed >= min_green (15.0s).
    6. Safety bounds: maximum green duration strictly capped at max_green (60.0s).
    7. Clearance integrity: yellow clearance transitions are never modified, delayed, or truncated.
    8. Emergency precedence: EmergencyWaveCoordinator and emergency_locked controllers
       take unconditional precedence; TSP is immediately inhibited if emergency locks are active.
    """

    def __init__(
        self,
        controllers: Dict[str, SignalController],
        approach_lanes: Optional[Dict[str, Dict[str, List[str]]]] = None,
        green_phases: Optional[Dict[str, Set[int]]] = None,
        corridor_priority_phases: Optional[Dict[str, int]] = None,
        detection_distance_m: float = 150.0,
        max_bus_eta_s: float = 5.0,
        extension_seconds: float = 5.0,
        min_green_before_tsp: float = 15.0,
        max_green: float = 60.0,
        enabled: bool = False,
    ) -> None:
        self.controllers = controllers
        self.approach_lanes = approach_lanes or {
            "J1": {
                "corridor_hosur": ["172853382#2_0", "172853382#2_1"],
                "side_cross": ["-148697299_0"],
            },
            "J2": {
                "corridor_hosur": [
                    "172853382#3_0",
                    "172853382#3_1",
                    "464465165#0_0",
                    "464465165#0_1",
                    "464465165#0_2",
                ],
                "madiwala": ["92196679#0_0", "92196679#0_1"],
            },
            "J3": {
                "corridor_hosur": ["1148717038#0_0", "1148717038#0_1"],
                "side_cross": ["-744783934_0"],
            },
        }
        self.green_phases = green_phases or {
            "J1": {0, 2},
            "J2": {0, 2},
            "J3": {0, 2},
        }
        self.corridor_priority_phases = corridor_priority_phases or {
            "J1": 2,
            "J2": 0,
            "J3": 2,
        }
        # Mapping: junction -> (phase -> list of approach lanes)
        self.phase_lanes: Dict[str, Dict[int, List[str]]] = {
            "J1": {
                0: self.approach_lanes["J1"]["side_cross"],
                2: self.approach_lanes["J1"]["corridor_hosur"],
            },
            "J2": {
                0: self.approach_lanes["J2"]["corridor_hosur"],
                2: self.approach_lanes["J2"]["madiwala"],
            },
            "J3": {
                0: self.approach_lanes["J3"]["side_cross"],
                2: self.approach_lanes["J3"]["corridor_hosur"],
            },
        }

        self.detection_distance_m = float(detection_distance_m)
        self.max_bus_eta_s = float(max_bus_eta_s)
        self.extension_seconds = float(extension_seconds)
        self.min_green_before_tsp = float(min_green_before_tsp)
        self.max_green = float(max_green)
        self.enabled = bool(enabled)

        # Telemetry & Event logging
        self.events: List[TSPEvent] = []
        self.assisted_buses: Set[str] = set()
        self.total_extended_time_s: float = 0.0
        self.emergency_blocks: int = 0
        self.max_green_blocks: int = 0

    def reset(self) -> None:
        """Resets all metrics and event history."""
        self.events.clear()
        self.assisted_buses.clear()
        self.total_extended_time_s = 0.0
        self.emergency_blocks = 0
        self.max_green_blocks = 0

    def is_bus(self, veh_id: str) -> bool:
        """Verifies if a vehicle is an authorized transit bus."""
        try:
            vclass = traci.vehicle.getVehicleClass(veh_id)
            if vclass == "bus":
                return True
            type_id = traci.vehicle.getTypeID(veh_id).lower()
            return "bus" in type_id
        except traci.TraCIException:
            return False

    def update(self, sim_time: float) -> List[TSPEvent]:
        """
        Step function called every simulation second.
        Evaluates active green phases and approaching transit buses.
        """
        if not self.enabled:
            return []

        granted_this_step: List[TSPEvent] = []

        for j_id, ctrl in self.controllers.items():
            # 1. Emergency safety preemption check
            if ctrl.emergency_locked:
                self.emergency_blocks += 1
                continue

            curr_phase = ctrl.get_phase()
            if not ctrl.is_green(curr_phase):
                continue

            elapsed = ctrl.get_green_elapsed(sim_time)
            if elapsed < self.min_green_before_tsp:
                continue

            # Cannot extend past max_green
            if elapsed >= self.max_green:
                self.max_green_blocks += 1
                continue

            # Check active lanes for approaching buses
            active_lanes = self.phase_lanes.get(j_id, {}).get(curr_phase, [])
            if not active_lanes:
                continue

            eligible_bus: Optional[Dict[str, Any]] = None
            for lane_id in active_lanes:
                try:
                    veh_ids = traci.lane.getLastStepVehicleIDs(lane_id)
                    lane_length = traci.lane.getLength(lane_id)
                except traci.TraCIException:
                    continue

                for veh_id in veh_ids:
                    if not self.is_bus(veh_id):
                        continue

                    try:
                        pos = traci.vehicle.getLanePosition(veh_id)
                        speed = traci.vehicle.getSpeed(veh_id)
                    except traci.TraCIException:
                        continue

                    dist = max(0.0, lane_length - pos)
                    if 0.0 < dist <= self.detection_distance_m:
                        effective_speed = max(speed, 2.0)
                        eta = dist / effective_speed
                        if eta <= self.max_bus_eta_s:
                            eligible_bus = {
                                "bus_id": veh_id,
                                "distance": dist,
                                "speed": speed,
                                "eta": eta,
                                "lane_id": lane_id,
                            }
                            break
                if eligible_bus is not None:
                    break

            if eligible_bus is not None:
                # Bus is eligible for TSP extension
                bus_id = eligible_bus["bus_id"]
                dist = eligible_bus["distance"]
                speed = eligible_bus["speed"]
                eta = eligible_bus["eta"]

                try:
                    next_switch = traci.trafficlight.getNextSwitch(ctrl.tls_id)
                    curr_remaining = max(0.0, next_switch - sim_time)
                    max_allowed_remaining = max(0.0, self.max_green - elapsed)
                    new_remaining = min(curr_remaining + self.extension_seconds, max_allowed_remaining)
                    added_time = new_remaining - curr_remaining

                    if added_time > 0.0:
                        traci.trafficlight.setPhaseDuration(ctrl.tls_id, new_remaining)
                        ctrl.hold_transit_priority(added_time, sim_time)
                        self.total_extended_time_s += added_time
                        self.assisted_buses.add(bus_id)
                        evt = TSPEvent(
                            sim_time=sim_time,
                            junction_id=j_id,
                            phase=curr_phase,
                            bus_id=bus_id,
                            distance_to_stop_m=round(dist, 2),
                            bus_speed_mps=round(speed, 2),
                            eta_s=round(eta, 2),
                            granted=True,
                            reason="GREEN_EXTENSION_GRANTED",
                            extended_seconds=round(added_time, 2),
                        )
                        self.events.append(evt)
                        granted_this_step.append(evt)
                        logger.info(
                            f"[TSP GRANTED] SimTime={sim_time:.1f}s | Junction={j_id} | Phase={curr_phase} | "
                            f"Bus={bus_id} (dist={dist:.1f}m, eta={eta:.1f}s) | "
                            f"Extension=+{added_time:.1f}s (new_remaining={new_remaining:.1f}s)"
                        )
                    else:
                        self.max_green_blocks += 1
                        evt = TSPEvent(
                            sim_time=sim_time,
                            junction_id=j_id,
                            phase=curr_phase,
                            bus_id=bus_id,
                            distance_to_stop_m=round(dist, 2),
                            bus_speed_mps=round(speed, 2),
                            eta_s=round(eta, 2),
                            granted=False,
                            reason="MAX_GREEN_CEILING_REACHED",
                            extended_seconds=0.0,
                        )
                        self.events.append(evt)
                except traci.TraCIException as exc:
                    logger.error(f"Error granting TSP at {j_id}: {exc!r}")

        return granted_this_step

    def compute_summary(self) -> TSPSummary:
        """Aggregates comprehensive transit priority performance statistics."""
        total_reqs = len(self.events)
        granted_reqs = sum(1 for e in self.events if e.granted)
        rejected_reqs = total_reqs - granted_reqs
        grant_rate = round(granted_reqs / total_reqs, 4) if total_reqs > 0 else 0.0

        return TSPSummary(
            total_requests=total_reqs,
            granted_requests=granted_reqs,
            rejected_requests=rejected_reqs,
            grant_rate=grant_rate,
            total_extended_time_s=round(self.total_extended_time_s, 2),
            emergency_preemptions_blocked_tsp=self.emergency_blocks,
            max_green_bound_hits=self.max_green_blocks,
            buses_assisted=sorted(list(self.assisted_buses)),
        )
