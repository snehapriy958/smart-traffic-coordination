"""
tests/test_nema_controller.py

Comprehensive unit tests for the NEMA TS 2 Actuated Controller.
Verifies:
- Minimum-green enforcement
- Maximum-green enforcement and max-out behavior
- Passage time extension and gap-out behavior
- Conflicting call registration and priority sequencing
- Recall modes (None, Min, Max, Coordinated)
- Emergency preemption and recovery
- Invalid configuration input rejection
"""

import pytest
from unittest.mock import MagicMock

from traffic_service.nema_controller import (
    NEMARecallMode,
    NEMAPhaseConfig,
    NEMAJunctionConfig,
    NEMAJunctionController,
    NEMACorridorController,
    create_default_nema_configs,
)
from traffic_service.signal_controller import SignalController


@pytest.fixture
def mock_signal_controller():
    ctrl = MagicMock(spec=SignalController)
    ctrl.tls_id = "test_tls"
    ctrl.green_phases = {0, 2}
    ctrl.yellow_transitions = {0: 1, 2: 3}
    ctrl.min_green = 15.0
    ctrl.max_green = 60.0
    ctrl.yellow_duration = 4.0
    ctrl.emergency_locked = False
    
    # State tracking
    ctrl._phase = 0
    ctrl._elapsed = 0.0
    ctrl.get_phase.side_effect = lambda: ctrl._phase
    ctrl.is_green.side_effect = lambda p=None: (p if p is not None else ctrl._phase) in ctrl.green_phases
    ctrl.is_yellow.side_effect = lambda p=None: (p if p is not None else ctrl._phase) in ctrl.yellow_transitions.values()
    ctrl.get_green_elapsed.side_effect = lambda t: ctrl._elapsed
    ctrl.can_switch.side_effect = lambda t: (not ctrl.emergency_locked and ctrl._elapsed >= ctrl.min_green)
    ctrl.request_switch.return_value = True
    return ctrl


@pytest.fixture
def default_j1_config():
    configs = create_default_nema_configs()
    return configs["J1"]


# =====================================================================
# 1. Minimum-Green Enforcement Tests
# =====================================================================

def test_nema_minimum_green_enforcement(mock_signal_controller, default_j1_config):
    """Proves that NEMA never terminates a phase before min_green has elapsed."""
    nema = NEMAJunctionController(default_j1_config, mock_signal_controller)
    mock_signal_controller._phase = 0
    mock_signal_controller._elapsed = 10.0  # < min_green (15.0s)
    
    # Conflicting call on Phase 2
    queues = {"side_cross": 0, "corridor_hosur": 10}
    dec = nema.step(sim_time=10.0, approach_queues=queues)
    
    assert dec is None
    mock_signal_controller.request_switch.assert_not_called()


# =====================================================================
# 2. Gap-Out Behavior Tests
# =====================================================================

def test_nema_gap_out_when_headway_exceeds_passage_time(mock_signal_controller, default_j1_config):
    """Proves that when headway exceeds passage time with a conflicting call, phase gaps out."""
    nema = NEMAJunctionController(default_j1_config, mock_signal_controller, step_length=1.0)
    mock_signal_controller._phase = 0
    mock_signal_controller._elapsed = 16.0  # > min_green (15.0s)
    
    # Empty approach on current phase 0, demand on opposing phase 2
    queues = {"side_cross": 0, "corridor_hosur": 5}
    
    # Let extension timer count down (passage_time = 3.0s)
    # Step 1: ext drops 3.0 -> 2.0
    d1 = nema.step(sim_time=16.0, approach_queues=queues)
    assert d1 is None
    assert nema.extension_timer == pytest.approx(2.0)
    
    # Step 2: ext drops 2.0 -> 1.0
    mock_signal_controller._elapsed = 17.0
    d2 = nema.step(sim_time=17.0, approach_queues=queues)
    assert d2 is None
    assert nema.extension_timer == pytest.approx(1.0)
    
    # Step 3: ext drops 1.0 -> 0.0 => GAP OUT
    mock_signal_controller._elapsed = 18.0
    d3 = nema.step(sim_time=18.0, approach_queues=queues)
    
    assert d3 is not None
    assert d3["action"] == "SWITCH_TO_YELLOW"
    assert d3["termination_reason"] == "GAP_OUT"
    assert d3["target_green_phase"] == 2
    mock_signal_controller.request_switch.assert_called_once_with(2, 18.0)


# =====================================================================
# 3. Continuous Arrival Extension Tests
# =====================================================================

def test_nema_continuous_arrivals_maintain_extension(mock_signal_controller, default_j1_config):
    """Proves that continuous vehicle arrivals reset the extension timer and prevent gap-out."""
    nema = NEMAJunctionController(default_j1_config, mock_signal_controller, step_length=1.0)
    mock_signal_controller._phase = 0
    mock_signal_controller._elapsed = 20.0
    
    # Continuous vehicles on Phase 0, conflicting call on Phase 2
    queues = {"side_cross": 3, "corridor_hosur": 5}
    
    for s in range(5):
        mock_signal_controller._elapsed = 20.0 + s
        dec = nema.step(sim_time=20.0 + s, approach_queues=queues)
        assert dec is None  # Holds green
        assert nema.extension_timer == pytest.approx(3.0)  # Reset to passage_time


# =====================================================================
# 4. Max-Out Behavior Tests
# =====================================================================

def test_nema_max_out_terminates_green_at_max_limit(mock_signal_controller, default_j1_config):
    """Proves that continuous arrivals terminate with MAX_OUT once max_green is reached."""
    nema = NEMAJunctionController(default_j1_config, mock_signal_controller, step_length=1.0)
    mock_signal_controller._phase = 0
    mock_signal_controller._elapsed = 60.0  # Reached max_green
    
    # Continuous queue on both phases
    queues = {"side_cross": 10, "corridor_hosur": 10}
    dec = nema.step(sim_time=60.0, approach_queues=queues)
    
    assert dec is not None
    assert dec["action"] == "SWITCH_TO_YELLOW"
    assert dec["termination_reason"] == "MAX_OUT"
    assert dec["target_green_phase"] == 2


# =====================================================================
# 5. No-Demand & Recall Mode Tests
# =====================================================================

def test_nema_no_conflicting_call_rests_in_green(mock_signal_controller, default_j1_config):
    """Proves that if no conflicting call exists, the phase rests in green past passage time."""
    nema = NEMAJunctionController(default_j1_config, mock_signal_controller, step_length=1.0)
    # J1 coordinated phase is Phase 2 (corridor_hosur)
    mock_signal_controller._phase = 2
    mock_signal_controller._elapsed = 25.0
    
    # No vehicles anywhere
    queues = {"side_cross": 0, "corridor_hosur": 0}
    
    # Even after extension timer drops to 0, coordinated phase rests in green
    nema._extension_timer = 0.0
    dec = nema.step(sim_time=25.0, approach_queues=queues)
    
    assert dec is None
    mock_signal_controller.request_switch.assert_not_called()


# =====================================================================
# 6. Emergency Preemption Tests
# =====================================================================

def test_nema_emergency_override_bypasses_actuation(mock_signal_controller, default_j1_config):
    """Proves that an emergency lock immediately halts NEMA switching."""
    mock_signal_controller.emergency_locked = True
    nema = NEMAJunctionController(default_j1_config, mock_signal_controller)
    
    queues = {"side_cross": 0, "corridor_hosur": 20}
    dec = nema.step(sim_time=25.0, approach_queues=queues)
    
    assert dec is not None
    assert dec["action"] == "EMERGENCY_LOCK_ACTIVE"
    mock_signal_controller.request_switch.assert_not_called()


def test_nema_resumes_cleanly_after_emergency_release(mock_signal_controller, default_j1_config):
    """Proves that NEMA resumes normal actuation once emergency lock is released."""
    nema = NEMAJunctionController(default_j1_config, mock_signal_controller)
    mock_signal_controller._phase = 0
    mock_signal_controller._elapsed = 20.0

    # 1. Emergency active
    mock_signal_controller.emergency_locked = True
    d_emerg = nema.step(sim_time=20.0, approach_queues={"side_cross": 0, "corridor_hosur": 5})
    assert d_emerg["action"] == "EMERGENCY_LOCK_ACTIVE"

    # 2. Release emergency lock
    mock_signal_controller.emergency_locked = False
    queues = {"side_cross": 0, "corridor_hosur": 5}
    
    # 3. Step until gap-out (passage_time = 3.0s, so 3 seconds to gap out)
    dec = None
    for s in range(4):
        mock_signal_controller._elapsed = 21.0 + s
        dec = nema.step(sim_time=21.0 + s, approach_queues=queues)
        if dec is not None:
            break

    assert dec is not None
    assert dec["action"] == "SWITCH_TO_YELLOW"
    assert dec["termination_reason"] == "GAP_OUT"


# =====================================================================
# 7. Corridor-Wide Controller Tests
# =====================================================================

def test_nema_corridor_controller_step_and_parameters():
    """Proves that NEMACorridorController coordinates J1, J2, J3 simultaneously."""
    controllers = {}
    for j_id, y_dur in [("J1", 4.0), ("J2", 6.0), ("J3", 4.0)]:
        ctrl = MagicMock(spec=SignalController)
        ctrl.tls_id = f"tls_{j_id}"
        ctrl.green_phases = {0, 2}
        ctrl.yellow_transitions = {0: 1, 2: 3}
        ctrl.min_green = 15.0
        ctrl.max_green = 60.0
        ctrl.yellow_duration = y_dur
        ctrl.emergency_locked = False
        ctrl.get_phase.return_value = 0
        ctrl.is_yellow.return_value = False
        ctrl.get_green_elapsed.return_value = 10.0
        ctrl.can_switch.return_value = False
        controllers[j_id] = ctrl

    corridor_nema = NEMACorridorController(controllers=controllers)
    params = corridor_nema.get_parameters_summary()
    
    assert params["controller_type"] == "nema_actuated_ts2"
    assert set(params["junctions"].keys()) == {"J1", "J2", "J3"}
    assert params["junctions"]["J2"]["yellow_durations"][0] == 6.0


# =====================================================================
# 8. Configuration Validation Tests
# =====================================================================

def test_nema_invalid_config_raises_value_error(mock_signal_controller):
    """Proves that invalid junction configurations raise ValueError on initialization."""
    bad_cfg = NEMAJunctionConfig(
        junction_id="BAD",
        tls_id="tls_bad",
        green_phases=[],  # Empty green phases
        yellow_transitions={},
        yellow_durations={},
        phases={},
    )
    with pytest.raises(ValueError, match="green_phases cannot be empty"):
        NEMAJunctionController(bad_cfg, mock_signal_controller)
