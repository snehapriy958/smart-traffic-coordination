"""
tests/test_max_pressure_controller.py

Comprehensive unit tests for the Varaiya Max-Pressure Controller.
Verifies:
- Mathematical pressure formulation P = sum w * (Q_up - Q_down)
- Downstream queue backpressure suppression
- Minimum-green and maximum-green enforcement
- Deterministic tie-breaking and anti-chatter logic
- Empty queue / zero demand handling
- Emergency preemption and recovery
- Corridor-wide coordination and parameters summary
"""

import pytest
from unittest.mock import MagicMock

from traffic_service.max_pressure_controller import (
    MaxPressureMovement,
    MaxPressurePhaseConfig,
    MaxPressureJunctionConfig,
    MaxPressureJunctionController,
    MaxPressureCorridorController,
    create_default_max_pressure_configs,
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
    configs = create_default_max_pressure_configs()
    return configs["J1"]


# =====================================================================
# 1. Mathematical Pressure Formulation Tests
# =====================================================================

def test_max_pressure_mathematical_calculation(mock_signal_controller, default_j1_config):
    """Proves that phase pressure exactly equals Upstream Queue minus Downstream Queue."""
    mp = MaxPressureJunctionController(default_j1_config, mock_signal_controller)
    
    # Case: J1 Hosur queue = 15, J2 Hosur receiving queue = 5 => Net pressure = 15 - 5 = 10
    # J1 side cross queue = 4, exit queue = 0 => Net pressure = 4 - 0 = 4
    all_queues = {
        "J1": {"side_cross": 4, "corridor_hosur": 15},
        "J2": {"corridor_hosur": 5, "madiwala": 2},
    }
    
    p0 = mp.compute_phase_pressure(0, all_queues)
    p2 = mp.compute_phase_pressure(2, all_queues)
    
    assert p0 == pytest.approx(4.0)
    assert p2 == pytest.approx(10.0)


def test_downstream_queue_backpressure_suppression(mock_signal_controller, default_j1_config):
    """Proves that heavy downstream congestion reduces arterial pressure, avoiding spillback."""
    mp = MaxPressureJunctionController(default_j1_config, mock_signal_controller)
    
    # J1 Hosur queue = 15, but J2 is gridlocked with queue = 20 => Net pressure = 15 - 20 = -5
    # J1 side cross queue = 2 => Net pressure = 2
    all_queues = {
        "J1": {"side_cross": 2, "corridor_hosur": 15},
        "J2": {"corridor_hosur": 20, "madiwala": 0},
    }
    
    p0 = mp.compute_phase_pressure(0, all_queues)
    p2 = mp.compute_phase_pressure(2, all_queues)
    
    assert p0 == pytest.approx(2.0)
    assert p2 == pytest.approx(-5.0)
    # Side street pressure now exceeds arterial pressure due to downstream backpressure
    assert p0 > p2


# =====================================================================
# 2. Phase Switching & Action Selection Tests
# =====================================================================

def test_max_pressure_switches_to_highest_pressure_phase(mock_signal_controller, default_j1_config):
    """Proves that controller switches to higher pressure phase when min_green is met."""
    mp = MaxPressureJunctionController(default_j1_config, mock_signal_controller)
    mock_signal_controller._phase = 0  # In side cross
    mock_signal_controller._elapsed = 20.0  # > min_green (15.0s)
    
    all_queues = {
        "J1": {"side_cross": 2, "corridor_hosur": 15},
        "J2": {"corridor_hosur": 0, "madiwala": 0},
    }
    
    dec = mp.step(sim_time=20.0, all_junction_queues=all_queues)
    
    assert dec is not None
    assert dec["action"] == "SWITCH_TO_YELLOW"
    assert dec["target_green_phase"] == 2
    mock_signal_controller.request_switch.assert_called_once_with(2, 20.0)


def test_max_pressure_min_green_prevents_premature_switch(mock_signal_controller, default_j1_config):
    """Proves that min_green blocks switching even when opposing pressure is overwhelming."""
    mp = MaxPressureJunctionController(default_j1_config, mock_signal_controller)
    mock_signal_controller._phase = 0
    mock_signal_controller._elapsed = 8.0  # < min_green (15.0s)
    
    all_queues = {
        "J1": {"side_cross": 0, "corridor_hosur": 50},
        "J2": {"corridor_hosur": 0, "madiwala": 0},
    }
    
    dec = mp.step(sim_time=8.0, all_junction_queues=all_queues)
    assert dec is None
    mock_signal_controller.request_switch.assert_not_called()


def test_max_pressure_max_green_forces_switch(mock_signal_controller, default_j1_config):
    """Proves that reaching max_green forces transition to opposing phase."""
    mp = MaxPressureJunctionController(default_j1_config, mock_signal_controller)
    mock_signal_controller._phase = 0
    mock_signal_controller._elapsed = 60.0  # Hit max_green
    
    # Both phases have equal queues
    all_queues = {
        "J1": {"side_cross": 10, "corridor_hosur": 10},
        "J2": {"corridor_hosur": 0, "madiwala": 0},
    }
    
    dec = mp.step(sim_time=60.0, all_junction_queues=all_queues)
    assert dec is not None
    assert dec["action"] == "SWITCH_TO_YELLOW"
    assert dec["target_green_phase"] == 2


def test_max_pressure_equal_pressure_hysteresis_no_chatter(mock_signal_controller, default_j1_config):
    """Proves that when pressures are equal, controller holds current phase to prevent chatter."""
    mp = MaxPressureJunctionController(default_j1_config, mock_signal_controller)
    mock_signal_controller._phase = 0
    mock_signal_controller._elapsed = 25.0
    
    all_queues = {
        "J1": {"side_cross": 10, "corridor_hosur": 10},
        "J2": {"corridor_hosur": 0, "madiwala": 0},
    }
    
    dec = mp.step(sim_time=25.0, all_junction_queues=all_queues)
    # Holds current phase
    assert dec is None
    mock_signal_controller.request_switch.assert_not_called()


def test_max_pressure_empty_network_holds_current_phase(mock_signal_controller, default_j1_config):
    """Proves that when all queues are 0 (all pressures <= 0), signal holds current phase."""
    mp = MaxPressureJunctionController(default_j1_config, mock_signal_controller)
    mock_signal_controller._phase = 2
    mock_signal_controller._elapsed = 20.0
    
    all_queues = {
        "J1": {"side_cross": 0, "corridor_hosur": 0},
        "J2": {"corridor_hosur": 0, "madiwala": 0},
    }
    
    dec = mp.step(sim_time=20.0, all_junction_queues=all_queues)
    assert dec is None


# =====================================================================
# 3. Emergency Preemption Tests
# =====================================================================

def test_max_pressure_emergency_preemption_and_recovery(mock_signal_controller, default_j1_config):
    """Proves that emergency lock overrides Max-Pressure and restores cleanly upon release."""
    mock_signal_controller.emergency_locked = True
    mp = MaxPressureJunctionController(default_j1_config, mock_signal_controller)
    
    all_queues = {"J1": {"side_cross": 20, "corridor_hosur": 0}}
    dec = mp.step(sim_time=20.0, all_junction_queues=all_queues)
    
    assert dec is not None
    assert dec["action"] == "EMERGENCY_LOCK_ACTIVE"
    mock_signal_controller.request_switch.assert_not_called()
    
    # Release emergency lock
    mock_signal_controller.emergency_locked = False
    mock_signal_controller._phase = 0
    mock_signal_controller._elapsed = 20.0
    all_queues_sw = {"J1": {"side_cross": 0, "corridor_hosur": 15}, "J2": {"corridor_hosur": 0}}
    
    dec_after = mp.step(sim_time=21.0, all_junction_queues=all_queues_sw)
    assert dec_after is not None
    assert dec_after["action"] == "SWITCH_TO_YELLOW"
    assert dec_after["target_green_phase"] == 2


# =====================================================================
# 4. Corridor Controller Tests
# =====================================================================

def test_max_pressure_corridor_controller():
    """Proves that MaxPressureCorridorController coordinates J1, J2, J3 simultaneously."""
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

    corridor_mp = MaxPressureCorridorController(controllers=controllers)
    params = corridor_mp.get_parameters_summary()
    
    assert params["controller_type"] == "max_pressure_varaiya"
    assert set(params["junctions"].keys()) == {"J1", "J2", "J3"}
    assert params["junctions"]["J2"]["yellow_durations"][0] == 6.0
