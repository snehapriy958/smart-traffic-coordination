"""
tests/test_phase3_resilience.py

Comprehensive automated test suite for Phase 3:
1. DetailedCorridorMetricsCollector & Cross-Street Equity (Gini, PTI, Buffer Index)
2. Telemetry Non-Ideality (Noisy Loop Detectors & Lossy Communication Hub)
3. Physical Mid-Block Incident Manager & Shockwave Recovery
4. Multi-Modal Transit Signal Priority (BMTC Bus Green Extension & Safety Caps)
"""

import math
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from traffic_service.resilience.detailed_collector import (
    DetailedCorridorMetricsCollector,
    ApproachMetrics,
    VehicleTripRecord,
    VEHICLE_PASSENGER_OCCUPANCY,
    FREE_FLOW_TRAVEL_TIME_REFERENCE_S,
    calculate_gini_coefficient,
)
from traffic_service.resilience.noisy_extractor import (
    NoisyIntersectionStateExtractor,
    LossyCorridorCommunicationHub,
    UpstreamInflowRecord,
)
from traffic_service.resilience.incident_manager import (
    MidBlockIncidentManager,
    IncidentSummary,
)
from traffic_service.resilience.transit_priority import (
    TransitSignalPriorityManager,
    TSPEvent,
    TSPSummary,
)
from traffic_service.signal_controller import SignalController
from traffic_service.state_extractor import IntersectionState, EmissionSnapshot


# =====================================================================
# 1. Equity & Reliability Mathematical Tests (Gini, PTI, Buffer Index)
# =====================================================================

def test_gini_coefficient_perfect_equality():
    """Equal delays across all approaches must yield Gini = 0.0."""
    values = [25.0, 25.0, 25.0, 25.0]
    gini = calculate_gini_coefficient(values)
    assert gini == 0.0


def test_gini_coefficient_extreme_inequality():
    """Extreme inequality (all delay on 1 approach of 4) must yield Gini ~ 0.75."""
    values = [0.0, 0.0, 0.0, 100.0]
    gini = calculate_gini_coefficient(values)
    # G = (3 * 100 * 2) / (2 * 4 * 100) = 600 / 800 = 0.75
    assert abs(gini - 0.75) < 1e-4


def test_gini_coefficient_edge_cases():
    """Zero values, empty lists, and negative inputs must be safely handled."""
    assert calculate_gini_coefficient([]) == 0.0
    assert calculate_gini_coefficient([0.0, 0.0, 0.0]) == 0.0
    with pytest.raises(ValueError):
        calculate_gini_coefficient([-5.0, 10.0])


def test_passenger_occupancy_constants():
    """IRC/CMP passenger occupancy mappings must match authoritative urban constants."""
    assert VEHICLE_PASSENGER_OCCUPANCY["bmtc_bus"] == 45.0
    assert VEHICLE_PASSENGER_OCCUPANCY["car"] == 1.5
    assert VEHICLE_PASSENGER_OCCUPANCY["motorcycle"] == 1.2
    assert VEHICLE_PASSENGER_OCCUPANCY["heavy_vehicle"] == 1.1
    assert VEHICLE_PASSENGER_OCCUPANCY["ambulance"] == 2.0


def test_detailed_collector_metrics_calculation():
    """Verifies Riemann delay integral, percentile travel times, PTI and Buffer Index."""
    collector = DetailedCorridorMetricsCollector(
        entry_edge="172853382#2",
        exit_edge="40696223#1",
        step_length=1.0,
    )

    # Synthetic vehicle trip records
    trip_times = [28.0, 30.0, 35.0, 40.0, 45.0, 50.0, 60.0, 75.0, 90.0, 120.0]
    for i, tt in enumerate(trip_times):
        rec = VehicleTripRecord(
            veh_id=f"veh_{i}",
            vtype="car",
            vclass="passenger",
            occupancy=1.5,
            entry_time=100.0 + i * 10,
            exit_time=100.0 + i * 10 + tt,
            travel_time_s=tt,
            delay_s=max(0.0, tt - 27.5),
            passenger_delay_s=max(0.0, tt - 27.5) * 1.5,
        )
        collector.individual_completed_trips.append(rec)
        collector._completed_travel_times.append(tt)

    summary = collector.compute_detailed_summary()
    rel = summary["reliability"]
    assert rel["completed_trip_count"] == 10
    assert rel["travel_time_mean_s"] == pytest.approx(float(np.mean(trip_times)), rel=1e-2)
    p95_expected = float(np.percentile(trip_times, 95))
    assert rel["travel_time_p95_s"] == pytest.approx(p95_expected, rel=1e-2)

    # Planning Time Index: T_95 / T_free_flow (reference = 27.5)
    expected_pti = p95_expected / 27.5
    assert rel["planning_time_index_pti"] == pytest.approx(expected_pti, rel=1e-2)

    # Buffer Index: ((T_95 - T_mean) / T_mean) * 100
    expected_bi = ((p95_expected - np.mean(trip_times)) / np.mean(trip_times)) * 100.0
    assert rel["buffer_index_bi_percent"] == pytest.approx(expected_bi, rel=1e-2)


# =====================================================================
# 2. Telemetry Non-Ideality Tests (Noisy Extractor & Lossy Comm Hub)
# =====================================================================

def test_noisy_extractor_clean_passthrough():
    """p_drop = 0.0 must preserve exact observations without loss."""
    mock_base = MagicMock()
    mock_state = IntersectionState(
        junction_id="J1",
        tls_id="tls_1",
        simulation_time=100.0,
        current_phase=2,
        phase_duration=45.0,
        phase_elapsed=20.0,
        time_to_switch=25.0,
        approach_queues={"corridor_hosur": 8, "side_cross": 4},
        total_queue=12,
        average_speed_kmh=22.5,
        total_waiting_time=60.0,
        vehicle_count=15,
        emissions=EmissionSnapshot(co2_mg_s=100.0, fuel_ml_s=0.5),
    )
    mock_base.extract.return_value = mock_state
    mock_base.junction_id = "J1"
    mock_base.tls_id = "tls_1"

    extractor = NoisyIntersectionStateExtractor(base_extractor=mock_base, p_drop=0.0)
    observed = extractor.extract(sim_time=100.0)

    assert observed.approach_queues == {"corridor_hosur": 8, "side_cross": 4}
    assert observed.total_queue == 12
    assert extractor.total_observations == 0
    assert extractor.dropped_observations == 0


def test_noisy_extractor_locf_fallback_and_stale_fault():
    """p_drop = 1.0 must use LOCF fallback up to max_stale_seconds, then report fault."""
    mock_base = MagicMock()
    mock_state_1 = IntersectionState(
        junction_id="J1",
        tls_id="tls_1",
        simulation_time=100.0,
        current_phase=2,
        phase_duration=45.0,
        phase_elapsed=10.0,
        time_to_switch=30.0,
        approach_queues={"corridor_hosur": 10},
        total_queue=10,
        average_speed_kmh=20.0,
        total_waiting_time=50.0,
        vehicle_count=10,
        emissions=EmissionSnapshot(),
    )
    mock_base.extract.return_value = mock_state_1
    mock_base.junction_id = "J1"
    mock_base.tls_id = "tls_1"

    extractor = NoisyIntersectionStateExtractor(
        base_extractor=mock_base,
        p_drop=0.0,  # Initially clean to prime LOCF cache
        max_stale_seconds=15.0,
    )
    # Prime cache at t = 100.0s
    obs1 = extractor.extract(sim_time=100.0)
    assert obs1.approach_queues["corridor_hosur"] == 10

    # Switch to 100% dropout
    extractor.p_drop = 1.0

    # At t = 110.0s (elapsed = 10s <= 15s): LOCF should return previous value 10
    obs2 = extractor.extract(sim_time=110.0)
    assert obs2.approach_queues["corridor_hosur"] == 10
    assert extractor.dropped_observations == 1

    # At t = 126.0s (elapsed = 26s > 15s): Stale sensor fault, queue defaults to 0
    obs3 = extractor.extract(sim_time=126.0)
    assert obs3.approach_queues["corridor_hosur"] == 0
    assert extractor.stale_fault_count == 1


def test_lossy_communication_hub_packet_loss_and_stale_rejection():
    """Lossy hub drops packets at p_loss and rejects packets older than max_packet_age_s."""
    hub = LossyCorridorCommunicationHub(
        corridor_sequence=["J1", "J2", "J3"],
        p_loss=0.0,
        max_packet_age_s=15.0,
    )

    # Clean transmission J1 -> J2
    hub.publish_upstream_inflow("J1", outflow_rate_veh_s=1.2, timestamp=100.0)
    assert hub.get_expected_inflow("J2", current_time=105.0) == 1.2
    assert hub.total_packets_sent == 1
    assert hub.total_packets_dropped == 0

    # Stale transmission: at t = 120.0s (age = 20s > 15s)
    inflow_stale = hub.get_expected_inflow("J2", current_time=120.0)
    assert inflow_stale == 0.0
    assert hub.stale_packets_rejected == 1

    # 100% packet loss test
    hub.p_loss = 1.0
    hub.publish_upstream_inflow("J2", outflow_rate_veh_s=2.5, timestamp=130.0)
    assert hub.total_packets_dropped == 1
    # J3 must not have received the dropped packet
    assert hub.get_expected_inflow("J3", current_time=130.0) == 0.0


# =====================================================================
# 3. Mid-Block Incident Manager & Shockwave Recovery Tests
# =====================================================================

@patch("traci.lane.setDisallowed")
@patch("traci.lane.setMaxSpeed")
@patch("traci.edge.getLastStepHaltingNumber")
@patch("traci.edge.getLastStepOccupancy")
def test_incident_manager_activation_and_clearance(mock_occ, mock_halt, mock_speed, mock_disallowed):
    """Incident manager closes lane at 300s, reopens at 600s, and computes summary."""
    mock_halt.return_value = 5
    mock_occ.return_value = 0.35

    mgr = MidBlockIncidentManager(
        edge_id="172853382#3",
        target_lane_index=0,
        start_time=300.0,
        end_time=600.0,
        normal_speed=16.67,
    )

    # 1. Before incident: t = 200s
    mgr.update(sim_time=200.0)
    assert not mgr.is_active
    mock_disallowed.assert_not_called()

    # 2. At incident onset: t = 300s
    mgr.update(sim_time=300.0)
    assert mgr.is_active
    mock_disallowed.assert_called_with("172853382#3_0", ["all"])
    mock_speed.assert_called_with("172853382#3_0", 0.0)

    # 3. At incident end: t = 600s
    mgr.update(sim_time=600.0)
    assert not mgr.is_active
    mock_disallowed.assert_called_with("172853382#3_0", [])
    mock_speed.assert_called_with("172853382#3_0", 16.67)


def test_incident_recovery_time_computation():
    """Incident recovery time measures seconds from t_end until sustained baseline recovery."""
    mgr = MidBlockIncidentManager(start_time=300.0, end_time=600.0)

    # Pre-incident: baseline corridor queue ~ 4 veh
    for t in range(100, 300):
        mgr.history.append({
            "time": float(t),
            "incident_active": 0,
            "corridor_queue": 4,
            "j1_queue": 2,
            "j2_queue": 2,
        })

    # During incident: corridor queue surges ~ 14 veh
    for t in range(300, 600):
        mgr.history.append({
            "time": float(t),
            "incident_active": 1,
            "corridor_queue": 14,
            "j1_queue": 8,
            "j2_queue": 6,
        })

    # Post-incident: queue takes 40s to clear back to <= 6 veh
    for t in range(600, 640):
        mgr.history.append({
            "time": float(t),
            "incident_active": 0,
            "corridor_queue": 10,
            "j1_queue": 5,
            "j2_queue": 5,
        })
    # Sustained baseline queue (10 steps) from t = 640 to 655
    for t in range(640, 660):
        mgr.history.append({
            "time": float(t),
            "incident_active": 0,
            "corridor_queue": 4,
            "j1_queue": 2,
            "j2_queue": 2,
        })

    summary = mgr.compute_summary()
    assert summary.pre_incident_mean_queue == 4.0
    assert summary.during_incident_mean_queue == 14.0
    assert summary.queue_increase_ratio == 3.5
    assert summary.recovered is True
    # Sustained at t = 649 (10 consecutive steps: 640..649); recovery time = 649 - 9 - 600 = 40.0s
    assert summary.recovery_time_s == 40.0


# =====================================================================
# 4. Multi-Modal Transit Signal Priority (TSP) Tests
# =====================================================================

def test_tsp_disabled_by_default():
    """TransitSignalPriorityManager must do nothing when enabled is False."""
    mock_ctrl = MagicMock(spec=SignalController)
    tsp = TransitSignalPriorityManager(controllers={"J1": mock_ctrl}, enabled=False)

    events = tsp.update(sim_time=100.0)
    assert len(events) == 0
    assert len(tsp.events) == 0


@patch("traci.lane.getLastStepVehicleIDs")
@patch("traci.lane.getLength")
@patch("traci.vehicle.getVehicleClass")
@patch("traci.vehicle.getLanePosition")
@patch("traci.vehicle.getSpeed")
@patch("traci.trafficlight.getNextSwitch")
@patch("traci.trafficlight.setPhaseDuration")
def test_tsp_grants_bus_extension_within_bounds(
    mock_set_duration, mock_switch, mock_speed, mock_pos, mock_vclass, mock_len, mock_veh_ids
):
    """BMTC bus within 150m with ETA <= 5s gets +5s extension up to max_green."""
    mock_ctrl = MagicMock(spec=SignalController)
    mock_ctrl.tls_id = "1617743335"
    mock_ctrl.emergency_locked = False
    mock_ctrl.get_phase.return_value = 2  # Active corridor green phase
    mock_ctrl.is_green.return_value = True
    mock_ctrl.get_green_elapsed.return_value = 20.0  # > min_green (15s), < max_green (60s)

    # Bus on corridor lane: length = 150m, pos = 120m -> dist = 30m, speed = 10m/s -> ETA = 3.0s <= 5.0s
    mock_veh_ids.return_value = ["bus_101"]
    mock_len.return_value = 150.0
    mock_vclass.return_value = "bus"
    mock_pos.return_value = 120.0
    mock_speed.return_value = 10.0
    mock_switch.return_value = 105.0  # curr_remaining = 5.0s

    tsp = TransitSignalPriorityManager(
        controllers={"J1": mock_ctrl},
        extension_seconds=5.0,
        max_green=60.0,
        enabled=True,
    )

    events = tsp.update(sim_time=100.0)
    assert len(events) == 1
    evt = events[0]
    assert evt.granted is True
    assert evt.bus_id == "bus_101"
    assert evt.extended_seconds == 5.0
    # New remaining = min(5 + 5, 60 - 20) = 10.0s
    mock_set_duration.assert_called_with("1617743335", 10.0)


@patch("traci.lane.getLastStepVehicleIDs")
@patch("traci.lane.getLength")
@patch("traci.vehicle.getVehicleClass")
@patch("traci.vehicle.getTypeID")
@patch("traci.trafficlight.getNextSwitch")
def test_tsp_rejects_non_bus_vehicles(
    mock_switch, mock_type, mock_vclass, mock_len, mock_veh_ids
):
    """Passenger cars, motorcycles, and trucks must never trigger green extensions."""
    mock_ctrl = MagicMock(spec=SignalController)
    mock_ctrl.emergency_locked = False
    mock_ctrl.get_phase.return_value = 2
    mock_ctrl.is_green.return_value = True
    mock_ctrl.get_green_elapsed.return_value = 25.0

    mock_veh_ids.return_value = ["car_123"]
    mock_len.return_value = 150.0
    mock_vclass.return_value = "passenger"
    mock_type.return_value = "car"

    tsp = TransitSignalPriorityManager(controllers={"J1": mock_ctrl}, enabled=True)
    events = tsp.update(sim_time=100.0)
    assert len(events) == 0
    assert len(tsp.assisted_buses) == 0


def test_tsp_emergency_lock_inhibition():
    """When emergency lock is active, TSP must be completely blocked."""
    mock_ctrl = MagicMock(spec=SignalController)
    mock_ctrl.emergency_locked = True  # Emergency active
    mock_ctrl.get_phase.return_value = 2
    mock_ctrl.is_green.return_value = True

    tsp = TransitSignalPriorityManager(controllers={"J1": mock_ctrl}, enabled=True)
    events = tsp.update(sim_time=100.0)
    assert len(events) == 0
    assert tsp.emergency_blocks == 1
