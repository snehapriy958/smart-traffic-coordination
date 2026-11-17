"""
traffic_service/resilience/detailed_collector.py

Detailed corridor and approach telemetry collector.
Captures per-vehicle individual trip records, per-approach delays,
passenger-hours of delay, and equity distributions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np
import traci

from traffic_service.corridor_metrics import (
    CorridorMetricsCollector,
    CorridorMetricsSummary,
    FUEL_DENSITY_MG_PER_LITER,
    FUEL_DENSITY_MG_PER_ML,
)
from traffic_service.state_extractor import IntersectionState

# Ground-truth kinematic free-flow travel time (empirically verified on empty network with green signals)
FREE_FLOW_TRAVEL_TIME_CAR_S: float = 27.0
FREE_FLOW_TRAVEL_TIME_BUS_S: float = 33.0
FREE_FLOW_TRAVEL_TIME_REFERENCE_S: float = 27.5

# Standard urban passenger occupancy assumptions (IRC / CMP Bengaluru standards)
VEHICLE_PASSENGER_OCCUPANCY: Dict[str, float] = {
    "motorcycle": 1.2,
    "car": 1.5,
    "passenger": 1.5,
    "bmtc_bus": 45.0,
    "bus": 45.0,
    "heavy_vehicle": 1.1,
    "truck": 1.1,
    "ambulance": 2.0,
    "emergency": 2.0,
}


@dataclass
class VehicleTripRecord:
    """Individual vehicle corridor transit record."""
    veh_id: str
    vtype: str
    vclass: str
    occupancy: float
    entry_time: float
    exit_time: float
    travel_time_s: float
    delay_s: float
    passenger_delay_s: float


@dataclass
class ApproachMetrics:
    """Per-approach microscopic performance metrics."""
    junction_id: str
    approach_name: str
    lanes: List[str]
    cumulative_delay_veh_s: float = 0.0
    queue_history: List[int] = field(default_factory=list)
    mean_queue: float = 0.0
    max_queue: int = 0
    p95_queue: float = 0.0
    completed_vehicles: int = 0


def calculate_gini_coefficient(values: List[float]) -> float:
    """
    Calculates the Gini coefficient for a non-negative population of values:
    G = sum_i sum_j |y_i - y_j| / (2 * n * sum_i y_i)
    Returns 0.0 if all values are zero or list is empty.
    """
    arr = np.array(values, dtype=float)
    if len(arr) == 0:
        return 0.0
    if np.any(arr < 0):
        raise ValueError("Gini coefficient requires non-negative values.")
    sum_val = np.sum(arr)
    if sum_val == 0.0:
        return 0.0
    n = len(arr)
    diffs = np.abs(arr[:, None] - arr[None, :])
    gini = float(np.sum(diffs) / (2.0 * n * sum_val))
    return round(gini, 6)


class DetailedCorridorMetricsCollector(CorridorMetricsCollector):
    """
    Extends CorridorMetricsCollector to record per-vehicle transit records,
    per-approach Riemann delay accumulation, passenger-hours of delay,
    and side-street equity distributions.
    """

    def __init__(
        self,
        entry_edge: str = "172853382#2",
        exit_edge: str = "40696223#1",
        step_length: float = 1.0,
        approach_lanes: Optional[Dict[str, Dict[str, List[str]]]] = None,
    ) -> None:
        super().__init__(entry_edge=entry_edge, exit_edge=exit_edge, step_length=step_length)

        # Default corridor approach mapping if not supplied
        self.approach_lanes_map = approach_lanes or {
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

        # Initialize approach metrics trackers
        self.approaches: Dict[str, Dict[str, ApproachMetrics]] = {}
        for j_id, app_dict in self.approach_lanes_map.items():
            self.approaches[j_id] = {}
            for app_name, lanes in app_dict.items():
                self.approaches[j_id][app_name] = ApproachMetrics(
                    junction_id=j_id,
                    approach_name=app_name,
                    lanes=lanes,
                )

        # Per-vehicle tracking: veh_id -> metadata dict
        self._vehicle_metadata: Dict[str, Dict[str, Any]] = {}
        self.individual_completed_trips: List[VehicleTripRecord] = []

    def record_step(
        self,
        sim_time: float,
        states: Dict[str, IntersectionState],
        emergency_duration: float = 0.0,
    ) -> None:
        """Records per-step detailed metrics and updates base collector."""
        # Query entering vehicles to capture type, class, and occupancy
        try:
            entry_vehs = traci.edge.getLastStepVehicleIDs(self.entry_edge)
        except traci.TraCIException:
            entry_vehs = []

        for v_id in entry_vehs:
            if v_id not in self._vehicle_metadata:
                try:
                    vtype = traci.vehicle.getTypeID(v_id)
                    vclass = traci.vehicle.getVehicleClass(v_id)
                except traci.TraCIException:
                    vtype = "car"
                    vclass = "passenger"

                # Map occupancy
                occupancy = VEHICLE_PASSENGER_OCCUPANCY.get(
                    vtype,
                    VEHICLE_PASSENGER_OCCUPANCY.get(vclass, 1.5),
                )
                self._vehicle_metadata[v_id] = {
                    "vtype": vtype,
                    "vclass": vclass,
                    "occupancy": occupancy,
                    "entry_time": sim_time,
                }

        # Check exiting vehicles to finalize trip records
        try:
            exit_vehs = traci.edge.getLastStepVehicleIDs(self.exit_edge)
        except traci.TraCIException:
            exit_vehs = []

        for v_id in exit_vehs:
            if v_id in self._vehicle_metadata and v_id in self._trip_entry_times:
                meta = self._vehicle_metadata.pop(v_id)
                t_in = meta["entry_time"]
                tt = max(1.0, sim_time - t_in)
                free_flow_ref = (
                    FREE_FLOW_TRAVEL_TIME_BUS_S
                    if meta["vclass"] == "bus"
                    else FREE_FLOW_TRAVEL_TIME_CAR_S
                )
                delay_s = max(0.0, tt - free_flow_ref)
                p_delay_s = delay_s * meta["occupancy"]

                self.individual_completed_trips.append(
                    VehicleTripRecord(
                        veh_id=v_id,
                        vtype=meta["vtype"],
                        vclass=meta["vclass"],
                        occupancy=meta["occupancy"],
                        entry_time=t_in,
                        exit_time=sim_time,
                        travel_time_s=tt,
                        delay_s=delay_s,
                        passenger_delay_s=p_delay_s,
                    )
                )

        # Record approach queues and accumulate Riemann delays
        for j_id, j_state in states.items():
            if j_id in self.approaches:
                for app_name, app_metrics in self.approaches[j_id].items():
                    q = j_state.approach_queues.get(app_name, 0)
                    app_metrics.queue_history.append(q)
                    app_metrics.cumulative_delay_veh_s += q * self.step_length

        # Call base record_step
        super().record_step(sim_time=sim_time, states=states, emergency_duration=emergency_duration)

    def compute_detailed_summary(
        self,
        emergency_duration: Optional[float] = None,
        emergency_cleared: bool = False,
    ) -> Dict[str, Any]:
        """Produces a comprehensive multi-modal, equity, and reliability summary."""
        base_summary = super().compute_summary(
            emergency_duration=emergency_duration,
            emergency_cleared=emergency_cleared,
        )

        # 1. Travel Time Reliability Metrics (from individual completed trips)
        travel_times = [tr.travel_time_s for tr in self.individual_completed_trips]
        if travel_times:
            tt_arr = np.array(travel_times, dtype=float)
            tt_mean = float(np.mean(tt_arr))
            tt_std = float(np.std(tt_arr, ddof=1)) if len(tt_arr) > 1 else 0.0
            tt_median = float(np.median(tt_arr))
            tt_p90 = float(np.percentile(tt_arr, 90))
            tt_p95 = float(np.percentile(tt_arr, 95))
            tt_p99 = float(np.percentile(tt_arr, 99))
            pti = round(tt_p95 / FREE_FLOW_TRAVEL_TIME_REFERENCE_S, 4)
            bi = round(((tt_p95 - tt_mean) / tt_mean) * 100.0, 2)
        else:
            tt_mean = base_summary.mean_corridor_travel_time_s or 0.0
            tt_std = 0.0
            tt_median = tt_mean
            tt_p90 = tt_mean
            tt_p95 = tt_mean
            tt_p99 = tt_mean
            pti = round(tt_mean / FREE_FLOW_TRAVEL_TIME_REFERENCE_S, 4)
            bi = 0.0

        # 2. Multi-Modal Passenger-Delay Breakdown
        vehicle_delays = [tr.delay_s for tr in self.individual_completed_trips]
        passenger_delays = [tr.passenger_delay_s for tr in self.individual_completed_trips]

        total_veh_delay_s = float(sum(vehicle_delays))
        total_pax_delay_s = float(sum(passenger_delays))
        veh_hours_of_delay = round(total_veh_delay_s / 3600.0, 4)
        pax_hours_of_delay = round(total_pax_delay_s / 3600.0, 4)

        # By vehicle class
        class_pax_delays: Dict[str, float] = {}
        for tr in self.individual_completed_trips:
            class_pax_delays[tr.vclass] = class_pax_delays.get(tr.vclass, 0.0) + tr.passenger_delay_s

        # 3. Approach-Level Metrics & Equity Analysis
        approach_summary: Dict[str, Dict[str, Any]] = {}
        approach_delay_list: List[float] = []

        for j_id, app_dict in self.approaches.items():
            approach_summary[j_id] = {}
            for app_name, app_metrics in app_dict.items():
                qh = np.array(app_metrics.queue_history, dtype=float) if app_metrics.queue_history else np.array([0])
                app_metrics.mean_queue = round(float(np.mean(qh)), 2)
                app_metrics.max_queue = int(np.max(qh))
                app_metrics.p95_queue = round(float(np.percentile(qh, 95)), 2)

                approach_summary[j_id][app_name] = {
                    "cumulative_delay_veh_s": round(app_metrics.cumulative_delay_veh_s, 2),
                    "mean_queue": app_metrics.mean_queue,
                    "max_queue": app_metrics.max_queue,
                    "p95_queue": app_metrics.p95_queue,
                }
                approach_delay_list.append(app_metrics.cumulative_delay_veh_s)

        # Cross-Street Equity: Gini Coefficient across the 6 corridor approaches
        delay_gini = calculate_gini_coefficient(approach_delay_list)

        # Cross-street vs. Arterial delay ratio
        arterial_delay = sum(
            approach_summary[j]["corridor_hosur"]["cumulative_delay_veh_s"]
            for j in ["J1", "J2", "J3"]
        )
        side_street_delay = (
            approach_summary["J1"]["side_cross"]["cumulative_delay_veh_s"]
            + approach_summary["J2"]["madiwala"]["cumulative_delay_veh_s"]
            + approach_summary["J3"]["side_cross"]["cumulative_delay_veh_s"]
        )
        side_to_arterial_ratio = round(side_street_delay / max(1.0, arterial_delay), 4)

        return {
            # Standard metrics
            "simulation_duration_s": base_summary.simulation_duration,
            "total_corridor_trips_completed": base_summary.total_corridor_trips_completed,
            "mean_corridor_travel_time_s": round(tt_mean, 2),
            "mean_corridor_speed_kmh": round(base_summary.mean_corridor_speed_kmh, 2),
            "cumulative_delay_veh_s": round(base_summary.cumulative_delay_veh_s, 2),
            "mean_corridor_queue": round(base_summary.mean_corridor_queue, 2),
            "max_corridor_queue": base_summary.max_corridor_queue,
            "total_co2_kg": round(base_summary.total_co2_kg, 4),
            "total_nox_g": round(base_summary.total_nox_g, 4),
            "total_fuel_liters": round(base_summary.total_fuel_liters, 4),
            "emergency_traversal_duration_s": base_summary.emergency_traversal_duration_s,
            "emergency_cleared": base_summary.emergency_cleared,
            # Travel Time Reliability
            "reliability": {
                "travel_time_mean_s": round(tt_mean, 2),
                "travel_time_std_s": round(tt_std, 2),
                "travel_time_median_s": round(tt_median, 2),
                "travel_time_p90_s": round(tt_p90, 2),
                "travel_time_p95_s": round(tt_p95, 2),
                "travel_time_p99_s": round(tt_p99, 2),
                "free_flow_reference_s": FREE_FLOW_TRAVEL_TIME_REFERENCE_S,
                "planning_time_index_pti": pti,
                "buffer_index_bi_percent": bi,
                "completed_trip_count": len(travel_times),
            },
            # Multi-Modal & Transit
            "multi_modal": {
                "vehicle_hours_of_delay_vhd": veh_hours_of_delay,
                "passenger_hours_of_delay_phd": pax_hours_of_delay,
                "passenger_delay_by_class_hours": {
                    k: round(v / 3600.0, 4) for k, v in class_pax_delays.items()
                },
                "average_occupancy_per_completed_vehicle": round(
                    float(np.mean([tr.occupancy for tr in self.individual_completed_trips])), 2
                ) if self.individual_completed_trips else 1.5,
            },
            # Equity & Approach Breakdown
            "equity": {
                "cross_street_delay_gini": delay_gini,
                "approach_delay_gini_coefficient": delay_gini,
                "total_arterial_delay_veh_s": round(arterial_delay, 2),
                "total_side_street_delay_veh_s": round(side_street_delay, 2),
                "side_to_arterial_delay_ratio": side_to_arterial_ratio,
                "approaches": approach_summary,
            },
        }
