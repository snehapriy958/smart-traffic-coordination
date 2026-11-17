"""
traffic_service/sumo_manager.py

Robust SUMO subprocess and TraCI lifecycle management.
Ensures safe startup, stepping, and clean shutdown across runs and seeds.
"""

from __future__ import annotations

import inspect
import logging
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

import traci
import traci.main

from common.sumo_env import require_sumo_env, SumoEnvironment

logger = logging.getLogger("sumo_manager")

# Narrowly-scoped lock ensuring serialized TraCI module proxying during startup
_traci_startup_lock = threading.Lock()

# Process-scoped PID tracking for safe session lifecycle management
_ACTIVE_SUMO_PIDS: set[int] = set()
_ACTIVE_SUMO_PIDS_LOCK = threading.Lock()


class SumoLifecycleState(str, Enum):
    """Explicit lifecycle states for SUMO process and TraCI connection."""
    REQUESTED = "REQUESTED"
    STARTING = "STARTING"
    CONNECTING = "CONNECTING"
    READY = "READY"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


def allocate_free_socket_port(host: str = "127.0.0.1") -> int:
    """Finds and allocates an available TCP loopback port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, 0))
        return int(s.getsockname()[1])


class _TraciScopedSubprocessProxy:
    """
    Scoped module proxy for traci.main.subprocess.
    Preserves sys.modules['subprocess'] and subprocess.Popen globally,
    intercepting Popen calls strictly within traci.main and filtering
    for the target SUMO command.
    """

    def __init__(
        self,
        real_module: Any,
        expected_config_path: str,
        on_process_spawned: Optional[Callable[[subprocess.Popen, Optional[int]], None]] = None,
    ) -> None:
        self._real_module = real_module
        self._expected_config = expected_config_path
        self._on_process_spawned = on_process_spawned
        self.captured_process: Optional[subprocess.Popen] = None
        self.captured_pid: Optional[int] = None

    def Popen(self, *args: Any, **kwargs: Any) -> subprocess.Popen:
        proc = self._real_module.Popen(*args, **kwargs)

        # Inspect command line to ensure only the intended SUMO command is captured
        cmd_args = args[0] if args else kwargs.get("args", [])
        cmd_str = " ".join(cmd_args) if isinstance(cmd_args, (list, tuple)) else str(cmd_args)

        is_sumo = "sumo" in cmd_str.lower() or self._expected_config.lower() in cmd_str.lower()
        if is_sumo:
            self.captured_process = proc
            if hasattr(proc, "pid"):
                self.captured_pid = proc.pid
            logger.info(f"Captured spawned SUMO process via scoped proxy: PID {self.captured_pid}")
            if self._on_process_spawned:
                try:
                    self._on_process_spawned(proc, self.captured_pid)
                except Exception as cb_err:
                    logger.warning(f"Error in on_process_spawned callback: {cb_err}")
        else:
            logger.debug(f"Ignoring non-SUMO subprocess spawned during proxy window: {cmd_str[:60]}")
        return proc

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real_module, name)


class SumoManager:
    """Manages starting, stepping, and closing the SUMO simulator via TraCI."""

    def __init__(
        self,
        sumocfg_path: Path | str,
        gui: bool = False,
        step_length: float = 1.0,
        label: str = "default",
        on_process_spawned: Optional[Callable[[subprocess.Popen, Optional[int]], None]] = None,
    ) -> None:
        self.sumocfg_path = Path(sumocfg_path).resolve()
        if not self.sumocfg_path.is_file():
            raise FileNotFoundError(f"SUMO configuration file not found: {self.sumocfg_path}")
        self.gui = gui
        self.step_length = step_length
        self.label = label
        self.on_process_spawned = on_process_spawned
        self.env: SumoEnvironment = require_sumo_env()
        self.state: SumoLifecycleState = SumoLifecycleState.STOPPED
        self._is_running: bool = False
        self._process: Optional[subprocess.Popen] = None
        self._pid: Optional[int] = None

    @property
    def is_running(self) -> bool:
        has_conn = False
        try:
            has_conn = traci.connection.has(self.label)
        except Exception:
            has_conn = traci.isLoaded()
        return self._is_running and has_conn

    @property
    def process(self) -> Optional[subprocess.Popen]:
        """Returns the subprocess.Popen handle for the active SUMO instance, if available."""
        return self._process

    @property
    def pid(self) -> Optional[int]:
        """Returns the OS PID for the active SUMO instance, if available."""
        return self._pid

    def _handle_process_spawned(self, proc: subprocess.Popen, pid: Optional[int]) -> None:
        """Internal callback invoked by _TraciScopedSubprocessProxy when SUMO is spawned."""
        self._process = proc
        self._pid = pid
        if pid:
            with _ACTIVE_SUMO_PIDS_LOCK:
                _ACTIVE_SUMO_PIDS.add(pid)
        if self.on_process_spawned:
            try:
                self.on_process_spawned(proc, pid)
            except Exception as cb_err:
                logger.warning(f"Error in on_process_spawned callback: {cb_err}")

    def _reap_process_handle(self, process: Optional[subprocess.Popen], pid: Optional[int]) -> None:
        """Process-scoped termination and reaping of a specific SUMO subprocess handle."""
        if process is None:
            return
        target_pid = pid or getattr(process, "pid", None)
        try:
            if process.poll() is None:
                try:
                    return_code = process.wait(timeout=2.0)
                    logger.debug(
                        "SUMO exited cleanly after TraCI close (PID %s, return code %s).",
                        target_pid,
                        return_code,
                    )
                except subprocess.TimeoutExpired:
                    logger.warning(
                        "SUMO PID %s did not exit within 2.0s after TraCI close; terminating.",
                        target_pid,
                    )
                    process.terminate()
                    try:
                        process.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        logger.error(
                            "SUMO PID %s did not exit after terminate; killing as fallback.",
                            target_pid,
                        )
                        process.kill()
                        process.wait()
        except Exception as exc:
            logger.warning("Error while reaping SUMO process PID %s: %s", target_pid, exc)
        finally:
            if target_pid:
                with _ACTIVE_SUMO_PIDS_LOCK:
                    _ACTIVE_SUMO_PIDS.discard(target_pid)

    @classmethod
    def cleanup_session_processes(cls) -> None:
        """
        Reaps all active SUMO processes tracked in this Python session.
        Strictly targets tracked PIDs; never executes global process termination.
        """
        with _ACTIVE_SUMO_PIDS_LOCK:
            pids = list(_ACTIVE_SUMO_PIDS)

        for p in pids:
            try:
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(p), "/T"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                else:
                    os.kill(p, signal.SIGTERM)
            except Exception as exc:
                logger.debug(f"Could not kill tracked SUMO process PID {p}: {exc}")
            finally:
                with _ACTIVE_SUMO_PIDS_LOCK:
                    _ACTIVE_SUMO_PIDS.discard(p)

    def start(
        self,
        seed: int = 42,
        additional_args: Sequence[str] | None = None,
        max_retries: int = 3,
    ) -> None:
        """Starts the SUMO process and initializes the TraCI connection with bounded retries."""
        self.state = SumoLifecycleState.REQUESTED

        binary = str(self.env.sumo_gui_binary if self.gui else self.env.sumo_binary)
        cmd = [
            binary,
            "-c", str(self.sumocfg_path),
            "--step-length", str(self.step_length),
            "--seed", str(seed),
            "--step-log.period", "0",
            "--no-step-log", "true",
            "--time-to-teleport", "300",
        ]
        if additional_args:
            cmd.extend(additional_args)

        last_error: Optional[Exception] = None

        for attempt in range(max_retries):
            self.state = SumoLifecycleState.STARTING

            # Clean any existing connection with this label before attempt
            try:
                if hasattr(traci, "connection") and traci.connection.has(self.label):
                    con = None
                    try:
                        con = traci.getConnection(self.label)
                        con.close(wait=False)
                    except Exception:
                        pass
                    if hasattr(traci.connection, "_connections"):
                        traci.connection._connections.pop(self.label, None)
                        if con is not None and traci.connection._connections.get("") == con:
                            traci.connection._connections.pop("", None)
            except Exception:
                pass

            if traci.isLoaded():
                try:
                    traci.close(wait=False)
                except Exception:
                    pass

            chosen_port = allocate_free_socket_port()
            start_kwargs: dict[str, Any] = {"label": self.label}
            try:
                sig = inspect.signature(traci.start)
                if "port" in sig.parameters:
                    start_kwargs["port"] = chosen_port
            except Exception:
                pass

            self.state = SumoLifecycleState.CONNECTING
            orig_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(15.0)

            proxy: Optional[_TraciScopedSubprocessProxy] = None
            try:
                with _traci_startup_lock:
                    original_module = traci.main.subprocess
                    proxy = _TraciScopedSubprocessProxy(
                        real_module=original_module,
                        expected_config_path=str(self.sumocfg_path),
                        on_process_spawned=self._handle_process_spawned,
                    )
                    traci.main.subprocess = proxy
                    try:
                        traci.start(cmd, **start_kwargs)
                    finally:
                        traci.main.subprocess = original_module
                        if proxy.captured_process is not None:
                            self._process = proxy.captured_process
                            self._pid = proxy.captured_pid

                try:
                    con = traci.getConnection(self.label)
                    if hasattr(con, "_socket") and con._socket:
                        con._socket.settimeout(None)
                    con_proc = getattr(con, "_process", None)
                    if con_proc is not None:
                        self._process = con_proc
                        self._pid = getattr(con_proc, "pid", self._pid)
                        if self._pid:
                            with _ACTIVE_SUMO_PIDS_LOCK:
                                _ACTIVE_SUMO_PIDS.add(self._pid)
                    logger.info(f"SUMO connection confirmed: PID {self._pid} (label: '{self.label}')")
                except Exception as exc:
                    logger.debug(f"Could not retrieve TraCI connection process handle: {exc}")

                self._is_running = True
                self.state = SumoLifecycleState.READY
                self.state = SumoLifecycleState.RUNNING
                return

            except Exception as exc:
                last_error = exc
                self.state = SumoLifecycleState.ERROR
                logger.warning(
                    f"SUMO startup attempt {attempt + 1}/{max_retries} failed on port {chosen_port}: {exc}"
                )
                # Process-scoped cleanup on failure
                proc_to_reap = self._process or (proxy.captured_process if proxy else None)
                pid_to_reap = self._pid or (proxy.captured_pid if proxy else None)
                self._reap_process_handle(proc_to_reap, pid_to_reap)
                self._process = None
                self._pid = None

                try:
                    if hasattr(traci, "connection") and traci.connection.has(self.label):
                        traci.connection._connections.pop(self.label, None)
                except Exception:
                    pass

                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
            finally:
                socket.setdefaulttimeout(orig_timeout)

        if last_error is not None:
            raise last_error
        raise RuntimeError(
            f"Failed to initialize SUMO / TraCI after {max_retries} attempts."
        )

    def step(self) -> float:
        """Advances the simulation by one step and returns the current simulation time."""
        if not self.is_running:
            raise RuntimeError("Cannot advance step: SUMO is not currently running.")
        traci.simulationStep()
        return traci.simulation.getTime()

    def get_time(self) -> float:
        """Returns the current simulation time in seconds."""
        if not self.is_running:
            return 0.0
        return traci.simulation.getTime()

    def stop(self) -> None:
        """Closes the TraCI connection cleanly."""
        self.state = SumoLifecycleState.STOPPED
        process = self._process
        target_pid = self._pid

        try:
            if hasattr(traci, "connection") and traci.connection.has(self.label):
                con = None
                try:
                    con = traci.getConnection(self.label)
                    con.close(wait=False)
                except Exception:
                    pass
                if hasattr(traci.connection, "_connections"):
                    traci.connection._connections.pop(self.label, None)
                    if con is not None and traci.connection._connections.get("") == con:
                        traci.connection._connections.pop("", None)
        except Exception:
            pass

        if traci.isLoaded():
            try:
                traci.close(wait=False)
            except Exception as exc:
                logger.debug("TraCI global close fallback failed: %s", exc)

        self._reap_process_handle(process, target_pid)
        self._is_running = False
        self._process = None
        self._pid = None

    def __enter__(self) -> SumoManager:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
