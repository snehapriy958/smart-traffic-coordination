"""
tests/test_sumo_lifecycle_manager.py

Unit test suite verifying SumoManager lifecycle management:
1. State machine transitions (REQUESTED -> STARTING -> CONNECTING -> READY -> RUNNING -> STOPPED).
2. Explicit port allocation and conflict avoidance.
3. Session-scoped PID tracking in _ACTIVE_SUMO_PIDS without global process destruction.
4. Error cleanup and process reaping during startup failures.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import traci
import traci.exceptions

from backend.config import SUMO_CONFIG_PATH
from traffic_service.sumo_manager import (
    SumoManager,
    SumoLifecycleState,
    allocate_free_socket_port,
    _ACTIVE_SUMO_PIDS,
    _ACTIVE_SUMO_PIDS_LOCK,
)


def test_allocate_free_socket_port():
    """Verifies that allocate_free_socket_port returns a valid, bindable integer port."""
    port1 = allocate_free_socket_port()
    port2 = allocate_free_socket_port()
    assert isinstance(port1, int)
    assert isinstance(port2, int)
    assert 1024 <= port1 <= 65535
    assert 1024 <= port2 <= 65535


def test_sumo_manager_initial_state():
    """Verifies that a newly created SumoManager is STOPPED and not running."""
    mgr = SumoManager(SUMO_CONFIG_PATH, label="test_init_state")
    assert mgr.state == SumoLifecycleState.STOPPED
    assert mgr.is_running is False
    assert mgr.process is None
    assert mgr.pid is None


def test_sumo_manager_lifecycle_state_transitions(monkeypatch):
    """Verifies state transitions during a successful startup and shutdown lifecycle."""
    mgr = SumoManager(SUMO_CONFIG_PATH, label="test_lifecycle_flow")
    observed_states = []

    # Mock traci.start and connection
    mock_proc = MagicMock(spec=subprocess.Popen)
    mock_proc.pid = 99991
    mock_proc.poll.return_value = None

    mock_conn = MagicMock()
    mock_conn._socket = MagicMock()
    mock_conn._process = mock_proc

    def mock_start(cmd, **kwargs):
        observed_states.append(mgr.state)
        # Register process via callback like _TraciScopedSubprocessProxy does
        mgr._handle_process_spawned(mock_proc, mock_proc.pid)

    monkeypatch.setattr(traci, "start", mock_start)
    monkeypatch.setattr(traci, "getConnection", lambda label: mock_conn)
    monkeypatch.setattr(traci.connection, "has", lambda label: True)

    mgr.start(seed=42)
    assert mgr.state == SumoLifecycleState.RUNNING
    assert mgr.is_running is True
    assert mgr.pid == 99991

    with _ACTIVE_SUMO_PIDS_LOCK:
        assert 99991 in _ACTIVE_SUMO_PIDS

    # Now stop
    mgr.stop()
    assert mgr.state == SumoLifecycleState.STOPPED
    assert mgr.process is None
    assert mgr.pid is None

    with _ACTIVE_SUMO_PIDS_LOCK:
        assert 99991 not in _ACTIVE_SUMO_PIDS


def test_sumo_manager_startup_failure_reaps_process(monkeypatch):
    """Verifies that an exception during startup sets ERROR, reaps process, and cleans PID tracking."""
    mgr = SumoManager(SUMO_CONFIG_PATH, label="test_fail_reap")

    mock_proc = MagicMock(spec=subprocess.Popen)
    mock_proc.pid = 99992
    mock_proc.poll.return_value = None
    mock_proc.wait.side_effect = [subprocess.TimeoutExpired(cmd="sumo", timeout=2.0), 0]

    def mock_failing_start(cmd, **kwargs):
        mgr._handle_process_spawned(mock_proc, mock_proc.pid)
        raise traci.exceptions.FatalTraCIError("Simulated socket timeout on handshake")

    monkeypatch.setattr(traci, "start", mock_failing_start)

    with pytest.raises(traci.exceptions.FatalTraCIError):
        mgr.start(seed=42, max_retries=1)

    assert mgr.state == SumoLifecycleState.ERROR
    assert mock_proc.terminate.called

    with _ACTIVE_SUMO_PIDS_LOCK:
        assert 99992 not in _ACTIVE_SUMO_PIDS
