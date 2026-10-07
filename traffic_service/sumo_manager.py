"""
traffic_service/sumo_manager.py

Robust SUMO subprocess and TraCI lifecycle management.
Ensures safe startup, stepping, and clean shutdown across runs and seeds.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

import traci

from common.sumo_env import require_sumo_env, SumoEnvironment


class SumoManager:
    """Manages starting, stepping, and closing the SUMO simulator via TraCI."""

    def __init__(self, sumocfg_path: Path | str, gui: bool = False, step_length: float = 1.0) -> None:
        self.sumocfg_path = Path(sumocfg_path).resolve()
        if not self.sumocfg_path.is_file():
            raise FileNotFoundError(f"SUMO configuration file not found: {self.sumocfg_path}")
        self.gui = gui
        self.step_length = step_length
        self.env: SumoEnvironment = require_sumo_env()
        self._is_running: bool = False

    @property
    def is_running(self) -> bool:
        return self._is_running and traci.isLoaded()

    def start(self, seed: int = 42, additional_args: Sequence[str] | None = None) -> None:
        """Starts the SUMO process and initializes the TraCI connection."""
        if traci.isLoaded():
            try:
                traci.close()
            except Exception:
                pass

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

        traci.start(cmd)
        self._is_running = True

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
        if traci.isLoaded():
            try:
                traci.close()
            except Exception:
                pass
        self._is_running = False

    def __enter__(self) -> SumoManager:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
