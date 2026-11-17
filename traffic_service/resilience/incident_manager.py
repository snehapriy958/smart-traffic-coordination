"""
traffic_service/resilience/incident_manager.py

Reproducible physical mid-block incident manager for SUMO corridors.
Simulates a lane obstruction on connector 172853382#3 between J1 and J2.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np
import traci

logger = logging.getLogger("incident_manager")


@dataclass
class IncidentSummary:
    """Quantitative summary of incident impact and recovery dynamics."""
    edge_id: str
    target_lane_id: str
    incident_start_s: float
    incident_end_s: float
    incident_duration_s: float
    pre_incident_mean_queue: float
    during_incident_mean_queue: float
    post_incident_mean_queue: float
    peak_queue_during_incident: int
    queue_increase_ratio: float
    recovered: bool
    recovery_time_s: Optional[float]  # Time in seconds after t_end to return to baseline queue
    spillback_detected_at_j1: bool


class MidBlockIncidentManager:
    """
    Manages a deterministic, physical lane-closure incident on the J1 -> J2 connector.
    Closes lane 0 of edge 172853382#3 during [start_time, end_time], reducing link capacity
    from 2 lanes to 1 lane, and evaluates shockwave recovery dynamics.
    """

    def __init__(
        self,
        edge_id: str = "172853382#3",
        target_lane_index: int = 0,
        start_time: float = 300.0,
        end_time: float = 600.0,
        normal_speed: float = 16.67,
    ) -> None:
        self.edge_id = edge_id
        self.target_lane_index = target_lane_index
        self.target_lane_id = f"{edge_id}_{target_lane_index}"
        self.start_time = float(start_time)
        self.end_time = float(end_time)
        self.normal_speed = float(normal_speed)

        self.is_active: bool = False
        self.activation_time: Optional[float] = None
        self.deactivation_time: Optional[float] = None

        # Queue history tracking across epochs
        self.history: List[Dict[str, float]] = []

    def update(self, sim_time: float, states: Optional[Dict[str, Any]] = None) -> None:
        """
        Step function called every simulation second to manage incident state
        and log spatial queue dynamics.
        """
        # 1. Activate incident
        if self.start_time <= sim_time < self.end_time and not self.is_active:
            try:
                # Disallow all vehicle classes from using the target lane
                traci.lane.setDisallowed(self.target_lane_id, ["all"])
                traci.lane.setMaxSpeed(self.target_lane_id, 0.0)
                self.is_active = True
                self.activation_time = sim_time
                logger.warning(
                    f"[{sim_time:.1f}s] INCIDENT ACTIVATED: Closed lane {self.target_lane_id} "
                    f"on connector {self.edge_id} (capacity reduced by 50%)."
                )
            except traci.TraCIException as exc:
                logger.error(f"Failed to activate incident on {self.target_lane_id}: {exc!r}")

        # 2. Deactivate incident
        elif sim_time >= self.end_time and self.is_active:
            try:
                # Restore full lane permissions and speed
                traci.lane.setDisallowed(self.target_lane_id, [])
                traci.lane.setMaxSpeed(self.target_lane_id, self.normal_speed)
                self.is_active = False
                self.deactivation_time = sim_time
                logger.warning(
                    f"[{sim_time:.1f}s] INCIDENT CLEARED: Reopened lane {self.target_lane_id} "
                    f"on connector {self.edge_id} (capacity restored to 100%)."
                )
            except traci.TraCIException as exc:
                logger.error(f"Failed to clear incident on {self.target_lane_id}: {exc!r}")

        # 3. Log spatial queue metrics
        try:
            connector_q = traci.edge.getLastStepHaltingNumber(self.edge_id)
            connector_occ = traci.edge.getLastStepOccupancy(self.edge_id)
        except traci.TraCIException:
            connector_q = 0
            connector_occ = 0.0

        j1_q = 0
        j2_q = 0
        if states:
            j1_q = states.get("J1").total_queue if states.get("J1") else 0
            j2_q = states.get("J2").total_queue if states.get("J2") else 0

        self.history.append({
            "time": sim_time,
            "incident_active": 1 if self.is_active else 0,
            "connector_queue": connector_q,
            "connector_occupancy": connector_occ,
            "j1_queue": j1_q,
            "j2_queue": j2_q,
            "corridor_queue": j1_q + j2_q,
        })

    def compute_summary(self) -> IncidentSummary:
        """Computes quantitative incident performance and recovery time."""
        if not self.history:
            return IncidentSummary(
                edge_id=self.edge_id,
                target_lane_id=self.target_lane_id,
                incident_start_s=self.start_time,
                incident_end_s=self.end_time,
                incident_duration_s=self.end_time - self.start_time,
                pre_incident_mean_queue=0.0,
                during_incident_mean_queue=0.0,
                post_incident_mean_queue=0.0,
                peak_queue_during_incident=0,
                queue_increase_ratio=1.0,
                recovered=False,
                recovery_time_s=None,
                spillback_detected_at_j1=False,
            )

        pre_rows = [r for r in self.history if 100.0 <= r["time"] < self.start_time]
        during_rows = [r for r in self.history if self.start_time <= r["time"] < self.end_time]
        post_rows = [r for r in self.history if r["time"] >= self.end_time]

        pre_q = float(np.mean([r["corridor_queue"] for r in pre_rows])) if pre_rows else 0.0
        during_q = float(np.mean([r["corridor_queue"] for r in during_rows])) if during_rows else 0.0
        post_q = float(np.mean([r["corridor_queue"] for r in post_rows])) if post_rows else 0.0
        peak_during = int(np.max([r["corridor_queue"] for r in during_rows])) if during_rows else 0

        # Queue increase ratio
        q_ratio = round(during_q / max(1.0, pre_q), 2)

        # Spillback detection at J1: J1 queue exceeds 15 vehicles during incident
        spillback_j1 = any(r["j1_queue"] >= 15 for r in during_rows)

        # Recovery time definition:
        # First timestamp post-incident (t >= end_time) where corridor queue drops to within
        # baseline threshold: max(pre_q * 1.15, pre_q + 2.0) and sustains it for >= 10 steps.
        recovered = False
        recovery_time_s: Optional[float] = None
        recovery_threshold = max(pre_q * 1.15, pre_q + 2.0)

        consecutive_recovered_steps = 0
        for r in post_rows:
            if r["corridor_queue"] <= recovery_threshold:
                consecutive_recovered_steps += 1
                if consecutive_recovered_steps >= 10:
                    recovered = True
                    # Recovery time measured from incident end (600s) to onset of sustained recovery
                    recovery_time_s = round(r["time"] - 9.0 - self.end_time, 1)
                    break
            else:
                consecutive_recovered_steps = 0

        return IncidentSummary(
            edge_id=self.edge_id,
            target_lane_id=self.target_lane_id,
            incident_start_s=self.start_time,
            incident_end_s=self.end_time,
            incident_duration_s=self.end_time - self.start_time,
            pre_incident_mean_queue=round(pre_q, 2),
            during_incident_mean_queue=round(during_q, 2),
            post_incident_mean_queue=round(post_q, 2),
            peak_queue_during_incident=peak_during,
            queue_increase_ratio=q_ratio,
            recovered=recovered,
            recovery_time_s=recovery_time_s,
            spillback_detected_at_j1=spillback_j1,
        )
