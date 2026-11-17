"""
traffic_service/resilience/noisy_extractor.py

Telemetry non-ideality simulation framework:
1. NoisyIntersectionStateExtractor: simulates stochastic loop detector dropouts.
2. LossyCorridorCommunicationHub: simulates inter-intersection wireless packet loss.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
import numpy as np

from traffic_service.communication import CorridorCommunicationHub, IntersectionMessage
from traffic_service.state_extractor import (
    IntersectionState,
    IntersectionStateExtractor,
)


@dataclass
class UpstreamInflowRecord:
    """Inter-intersection upstream inflow transmission record."""
    sender_id: str
    outflow_rate_veh_s: float
    timestamp: float


class NoisyIntersectionStateExtractor:
    """
    Non-destructive wrapper around IntersectionStateExtractor.
    Simulates stochastic loop detector dropouts with Last-Observation-Carried-Forward (LOCF)
    fallback and stale sensor fault detection.
    """

    def __init__(
        self,
        base_extractor: IntersectionStateExtractor,
        p_drop: float = 0.0,
        seed: int = 42,
        max_stale_seconds: float = 15.0,
    ) -> None:
        self.base_extractor = base_extractor
        self.p_drop = float(p_drop)
        self.max_stale_seconds = float(max_stale_seconds)
        self.rng = np.random.RandomState(seed)

        # Telemetry tracking: approach -> (last_valid_queue, timestamp)
        self._last_valid_queues: Dict[str, int] = {}
        self._last_valid_timestamps: Dict[str, float] = {}

        # Counters
        self.total_observations: int = 0
        self.dropped_observations: int = 0
        self.stale_fault_count: int = 0

    @property
    def junction_id(self) -> str:
        return self.base_extractor.junction_id

    @property
    def tls_id(self) -> str:
        return self.base_extractor.tls_id

    def extract(self, sim_time: float, step_length: float = 1.0) -> IntersectionState:
        """
        Extracts intersection state, applying stochastic detector dropouts.
        Does not corrupt underlying TraCI or SUMO network state.
        """
        true_state = self.base_extractor.extract(sim_time, step_length=step_length)
        if self.p_drop <= 0.0:
            for app_name, true_q in true_state.approach_queues.items():
                self._last_valid_queues[app_name] = true_q
                self._last_valid_timestamps[app_name] = sim_time
            return true_state

        observed_state = copy.deepcopy(true_state)
        observed_queues: Dict[str, int] = {}

        for app_name, true_q in true_state.approach_queues.items():
            self.total_observations += 1
            is_dropped = bool(self.rng.uniform(0.0, 1.0) < self.p_drop)

            if is_dropped:
                self.dropped_observations += 1
                # Fallback to Last-Observation-Carried-Forward (LOCF) if not stale
                last_time = self._last_valid_timestamps.get(app_name, -999.0)
                if sim_time - last_time <= self.max_stale_seconds and app_name in self._last_valid_queues:
                    observed_queues[app_name] = self._last_valid_queues[app_name]
                else:
                    # Sensor fault condition: stale beyond tolerance; defaults to 0 with fault flag
                    self.stale_fault_count += 1
                    observed_queues[app_name] = 0
            else:
                # Valid observation: update LOCF cache
                observed_queues[app_name] = true_q
                self._last_valid_queues[app_name] = true_q
                self._last_valid_timestamps[app_name] = sim_time

        observed_state.approach_queues = observed_queues
        observed_state.total_queue = sum(observed_queues.values())
        return observed_state


class LossyCorridorCommunicationHub(CorridorCommunicationHub):
    """
    Subclasses CorridorCommunicationHub to inject stochastic packet loss
    and latency into inter-intersection upstream arrival coordination.
    Emergency vehicle broadcasts are protected from loss (safety standard).
    """

    def __init__(
        self,
        corridor_sequence: Optional[List[str]] = None,
        p_loss: float = 0.0,
        seed: int = 42,
        max_packet_age_s: float = 15.0,
    ) -> None:
        super().__init__(corridor_sequence=corridor_sequence)
        self.p_loss = float(p_loss)
        self.max_packet_age_s = float(max_packet_age_s)
        self.rng = np.random.RandomState(seed)

        self.total_packets_sent: int = 0
        self.total_packets_dropped: int = 0
        self.stale_packets_rejected: int = 0
        self._packet_history: Dict[str, UpstreamInflowRecord] = {}
        self._last_sim_time: float = 0.0

    def publish_upstream_inflow(
        self,
        sender_id: str,
        outflow_rate_veh_s: float,
        timestamp: float,
    ) -> None:
        """Publishes upstream discharge packet subject to stochastic packet loss."""
        self._last_sim_time = max(self._last_sim_time, float(timestamp))
        self.total_packets_sent += 1
        if self.p_loss > 0.0 and self.rng.uniform(0.0, 1.0) < self.p_loss:
            self.total_packets_dropped += 1
            return  # Packet dropped in transit

        super().publish_upstream_inflow(
            sender_id=sender_id,
            outflow_rate_veh_s=outflow_rate_veh_s,
            timestamp=timestamp,
        )
        if sender_id in self.corridor_sequence:
            idx = self.corridor_sequence.index(sender_id)
            if idx + 1 < len(self.corridor_sequence):
                downstream_id = self.corridor_sequence[idx + 1]
                self._packet_history[downstream_id] = UpstreamInflowRecord(
                    sender_id=sender_id,
                    outflow_rate_veh_s=outflow_rate_veh_s,
                    timestamp=timestamp,
                )

    def get_expected_inflow(self, receiver_id: str, current_time: Optional[float] = None) -> float:
        """
        Retrieves expected inflow rate with stale packet rejection.
        If the packet is older than max_packet_age_s, it is rejected.
        """
        curr_time = current_time if current_time is not None else self._last_sim_time
        record = self._packet_history.get(receiver_id)
        if record is None:
            return 0.0

        if curr_time - record.timestamp > self.max_packet_age_s:
            self.stale_packets_rejected += 1
            return 0.0  # Discard stale packet

        return record.outflow_rate_veh_s
