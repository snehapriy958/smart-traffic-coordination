"""
backend/simulation_service.py

Thread-safe background simulation orchestrator.
Bridges FastAPI with MultiIntersectionSimulation and TraCI.
Manages simulation lifecycle (start, pause, resume, stop, reset),
broadcasts telemetry, records decisions, and persists metrics to SQLite.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.config import BASE_DIR, SUMO_CONFIG_PATH, SUMO_STEP_LENGTH
from backend.database import SessionLocal
from backend.models import (
    EmergencyEventRecord,
    SignalDecisionRecord,
    SimulationRun,
    TrafficMetricRecord,
)
from backend.schemas import (
    DecisionItemSchema,
    EmergencyApproachingSchema,
    EmergencyEventItemSchema,
    EmergencyResponse,
    EmissionSchema,
    JunctionStateSchema,
    SignalInfoSchema,
    SimulationStatusResponse,
    TrafficLiveResponse,
    TrafficMetricsResponse,
)
from backend.websocket_manager import ws_manager
from traffic_service.multi_intersection_simulation import MultiIntersectionSimulation
from traffic_service.state_extractor import IntersectionState

logger = logging.getLogger("simulation_service")


class SimulationService:
    """Singleton service managing background SUMO simulation lifecycle and telemetry."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sim: Optional[MultiIntersectionSimulation] = None
        self._thread: Optional[threading.Thread] = None

        self._running: bool = False
        self._paused: bool = False
        self._stop_requested: bool = False

        self._mode: str = "coordinated"
        self._seed: int = 42
        self._duration: int = 600
        self._step_length: float = SUMO_STEP_LENGTH
        self._decision_interval: float = 5.0
        self._enable_emergency: bool = True
        self._gui: bool = False

        self._current_sim_time: float = 0.0
        self._current_run_id: Optional[int] = None
        self._current_run_uuid: Optional[str] = None
        self._error_message: Optional[str] = None

        # In-memory telemetry cache
        self._latest_states: Dict[str, IntersectionState] = {}
        self._decisions_log: List[DecisionItemSchema] = []
        self._emergency_events: List[EmergencyEventItemSchema] = []
        self._cached_metrics: Dict[str, Any] = {}

        # Loop reference for async websocket broadcasting
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # Pre-seed decisions log with initial notice
        self._decisions_log.append(
            DecisionItemSchema(
                simulation_time=0.0,
                junction_id="SYSTEM",
                current_phase=0,
                target_phase=None,
                action="INITIALIZE",
                reason="System ready for simulation initialization.",
                is_override=False,
                timestamp=datetime.utcnow().isoformat(),
            )
        )

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Sets the running asyncio event loop for threadsafe coroutine scheduling."""
        self.loop = loop

    # ------------------------------------------------------------------
    # Lifecycle Controls
    # ------------------------------------------------------------------

    def start_simulation(
        self,
        mode: str = "coordinated",
        duration: int = 600,
        seed: int = 42,
        step_length: float = 1.0,
        decision_interval: float = 5.0,
        enable_emergency: bool = True,
        gui: bool = False,
    ) -> Tuple[bool, str]:
        """Starts a new simulation run in the background thread."""
        with self._lock:
            if self._running:
                return False, "Simulation is already running. Please stop or reset first."

            self._mode = mode.lower()
            self._duration = duration
            self._seed = seed
            self._step_length = step_length
            self._decision_interval = decision_interval
            self._enable_emergency = enable_emergency
            self._gui = gui

            self._paused = False
            self._stop_requested = False
            self._error_message = None
            self._current_sim_time = 0.0
            self._latest_states = {}
            self._decisions_log = []
            self._emergency_events = []

            run_uuid = f"run_{uuid.uuid4().hex[:12]}"
            self._current_run_uuid = run_uuid

            # Create Database Record
            db = SessionLocal()
            try:
                run_rec = SimulationRun(
                    run_uuid=run_uuid,
                    mode=self._mode,
                    status="RUNNING",
                    seed=self._seed,
                    duration_requested=self._duration,
                    duration_simulated=0.0,
                    started_at=datetime.utcnow(),
                )
                db.add(run_rec)
                db.commit()
                db.refresh(run_rec)
                self._current_run_id = run_rec.id
            except Exception as exc:
                db.rollback()
                logger.error(f"Failed to create simulation run record: {exc}")
                self._current_run_id = None
            finally:
                db.close()

            # Record Start Decision
            self._record_decision(
                sim_time=0.0,
                junction_id="SYSTEM",
                current_phase=0,
                target_phase=None,
                action="START",
                reason=f"Started {self._mode.upper()} simulation (Seed: {self._seed}, Duration: {self._duration}s).",
            )

            # Spawn Worker Thread
            self._running = True
            self._thread = threading.Thread(
                target=self._run_simulation_worker,
                daemon=True,
                name="SumoSimulationWorker",
            )
            self._thread.start()

            return True, f"Simulation started in {self._mode} mode (UUID: {run_uuid})"

    def pause_simulation(self) -> Tuple[bool, str]:
        """Safely pauses the running simulation."""
        with self._lock:
            if not self._running:
                return False, "Simulation is not currently running."
            if self._paused:
                return False, "Simulation is already paused."

            self._paused = True
            self._record_decision(
                sim_time=self._current_sim_time,
                junction_id="SYSTEM",
                current_phase=0,
                target_phase=None,
                action="PAUSE",
                reason="Operator paused simulation stepping.",
            )
            self._update_db_status("PAUSED")
            return True, "Simulation paused successfully."

    def resume_simulation(self) -> Tuple[bool, str]:
        """Resumes a paused simulation."""
        with self._lock:
            if not self._running:
                return False, "Simulation is not currently running."
            if not self._paused:
                return False, "Simulation is not paused."

            self._paused = False
            self._record_decision(
                sim_time=self._current_sim_time,
                junction_id="SYSTEM",
                current_phase=0,
                target_phase=None,
                action="RESUME",
                reason="Operator resumed simulation execution.",
            )
            self._update_db_status("RUNNING")
            return True, "Simulation resumed successfully."

    def stop_simulation(self) -> Tuple[bool, str]:
        """Stops the simulation and safely releases SUMO/TraCI resources."""
        with self._lock:
            if not self._running and not self._sim:
                return False, "Simulation is not currently running."

            self._stop_requested = True
            self._paused = False

        # Wait for thread to finish outside lock
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

        with self._lock:
            self._cleanup_sim(final_status="STOPPED")
            return True, "Simulation stopped successfully and resources released."

    def reset_simulation(self) -> Tuple[bool, str]:
        """Resets the simulation state and cleans up resources."""
        self.stop_simulation()
        with self._lock:
            self._current_sim_time = 0.0
            self._latest_states = {}
            self._cached_metrics = {}
            self._error_message = None
            self._record_decision(
                sim_time=0.0,
                junction_id="SYSTEM",
                current_phase=0,
                target_phase=None,
                action="RESET",
                reason="Simulation state reset by operator.",
            )
            return True, "Simulation reset to clean state."

    # ------------------------------------------------------------------
    # Worker Thread
    # ------------------------------------------------------------------

    def _run_simulation_worker(self) -> None:
        """Internal background worker running the SUMO simulation loop."""
        config_path = SUMO_CONFIG_PATH
        if not config_path.is_file():
            err_msg = f"SUMO config file not found: {config_path}"
            logger.error(err_msg)
            with self._lock:
                self._error_message = err_msg
                self._cleanup_sim(final_status="ERROR")
            return

        try:
            sim = MultiIntersectionSimulation(
                sumocfg_path=config_path,
                mode=self._mode,
                gui=self._gui,
                step_length=self._step_length,
                decision_interval=self._decision_interval,
                enable_emergency=self._enable_emergency,
            )
            with self._lock:
                self._sim = sim

            sim.start(seed=self._seed)
            logger.info("SUMO TraCI connection initialized.")

            step_counter = 0
            while not self._stop_requested:
                # Check pause
                if self._paused:
                    time.sleep(0.1)
                    continue

                # Step simulation
                sim_time = sim.sumo_manager.step()
                states = sim.get_states(sim_time)

                # Process emergency preemption if enabled
                if self._enable_emergency:
                    sim.emergency_coordinator.update(sim_time)
                    self._check_emergency_progress(sim, sim_time)

                # Coordinated / Baseline Decision Control
                if sim_time >= sim._next_decision_time:
                    sim._next_decision_time += sim.decision_interval
                    if sim.mode == "coordinated":
                        self._run_coordinated_with_logging(sim, states, sim_time)

                # Collect Metrics
                emergency_duration = (
                    sim.emergency_coordinator.metrics.total_traversal_duration
                    if sim.emergency_coordinator.metrics.completed
                    else 0.0
                )
                sim.metrics_collector.record_step(sim_time, states, emergency_duration=emergency_duration)

                # Update in-memory telemetry
                with self._lock:
                    self._current_sim_time = sim_time
                    self._latest_states = states
                    self._cached_metrics = self._extract_metrics_summary(sim, states, sim_time)

                # Periodic DB write (every 5 seconds)
                step_counter += 1
                if step_counter % int(max(1, 5.0 / self._step_length)) == 0:
                    self._persist_metrics_snapshot(sim_time)

                # Broadcast live telemetry over WebSocket
                self._broadcast_telemetry()

                # Check if target duration reached
                if sim_time >= self._duration:
                    logger.info(f"Target duration {self._duration}s reached.")
                    break

                # Sleep to synchronize with real-time if necessary
                time.sleep(0.02)

            # Simulation completed cleanly
            with self._lock:
                final_st = "COMPLETED" if self._current_sim_time >= self._duration else "STOPPED"
                self._cleanup_sim(final_status=final_st)

        except Exception as exc:
            logger.exception(f"Simulation run failed: {exc}")
            with self._lock:
                self._error_message = str(exc)
                self._cleanup_sim(final_status="ERROR")

    def _cleanup_sim(self, final_status: str = "STOPPED") -> None:
        """Safely closes TraCI, updates database, and resets state flags."""
        if self._sim:
            try:
                self._sim.close()
            except Exception as e:
                logger.warning(f"Error during sim.close(): {e}")
            self._sim = None

        self._running = False
        self._paused = False
        self._stop_requested = False

        # Finalize Database record
        if self._current_run_id:
            db = SessionLocal()
            try:
                run_rec = db.query(SimulationRun).filter(SimulationRun.id == self._current_run_id).first()
                if run_rec:
                    run_rec.status = final_status
                    run_rec.completed_at = datetime.utcnow()
                    run_rec.duration_simulated = self._current_sim_time
                    if self._error_message:
                        run_rec.error_message = self._error_message
                    if self._cached_metrics:
                        run_rec.summary_metrics_json = json.dumps(self._cached_metrics)
                    db.commit()
            except Exception as exc:
                db.rollback()
                logger.error(f"Failed to update final run status in DB: {exc}")
            finally:
                db.close()

        # Final broadcast
        self._broadcast_telemetry()

    # ------------------------------------------------------------------
    # Telemetry Extraction & Persistence
    # ------------------------------------------------------------------

    def _extract_metrics_summary(
        self,
        sim: MultiIntersectionSimulation,
        states: Dict[str, IntersectionState],
        sim_time: float,
    ) -> Dict[str, Any]:
        """Calculates consolidated corridor metrics from states and collector."""
        summary = sim.metrics_collector.compute_summary()
        total_veh = sum(st.vehicle_count for st in states.values())
        mean_speed = sum(st.average_speed_kmh for st in states.values()) / max(1, len(states))
        mean_q = sum(st.total_queue for st in states.values()) / max(1, len(states))
        max_q = max((st.total_queue for st in states.values()), default=0)
        total_wait = sum(st.total_waiting_time for st in states.values())

        return {
            "simulation_time": sim_time,
            "total_vehicles": total_veh,
            "throughput_vehicles": summary.total_corridor_trips_completed,
            "mean_speed_kmh": round(mean_speed, 2),
            "total_corridor_waiting_time_s": round(total_wait, 2),
            "mean_corridor_queue": round(mean_q, 2),
            "max_corridor_queue": max_q,
            "total_co2_kg": round(summary.total_co2_kg, 4),
            "total_nox_g": round(summary.total_nox_g, 4),
            "total_fuel_liters": round(summary.total_fuel_liters, 4),
            "emergency_traversal_duration_s": round(summary.emergency_traversal_duration_s, 2),
            "junction_queues": {j: st.total_queue for j, st in states.items()},
        }

    def _persist_metrics_snapshot(self, sim_time: float) -> None:
        """Stores periodic metric snapshots in SQLite."""
        if not self._current_run_id or not self._cached_metrics:
            return

        db = SessionLocal()
        try:
            m = self._cached_metrics
            rec = TrafficMetricRecord(
                run_id=self._current_run_id,
                simulation_time=sim_time,
                total_vehicles=m.get("total_vehicles", 0),
                throughput_vehicles=m.get("throughput_vehicles", 0),
                mean_speed_kmh=m.get("mean_speed_kmh", 0.0),
                mean_queue=m.get("mean_corridor_queue", 0.0),
                max_queue=m.get("max_corridor_queue", 0),
                total_waiting_time=m.get("total_corridor_waiting_time_s", 0.0),
                co2_kg=m.get("total_co2_kg", 0.0),
                nox_g=m.get("total_nox_g", 0.0),
                fuel_liters=m.get("total_fuel_liters", 0.0),
            )
            db.add(rec)
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning(f"Error persisting traffic metrics snapshot: {exc}")
        finally:
            db.close()

    def _check_emergency_progress(self, sim: MultiIntersectionSimulation, sim_time: float) -> None:
        """Monitors emergency coordinator for preemption events."""
        metrics = sim.emergency_coordinator.metrics
        locked_junctions = [
            j for j, ctrl in sim.controllers.items() if ctrl.emergency_locked
        ]

        if locked_junctions and not self._emergency_events:
            event = EmergencyEventItemSchema(
                simulation_time=sim_time,
                vehicle_id=metrics.vehicle_id or "AMBULANCE_01",
                affected_corridor="Hosur Road (J1 -> J2 -> J3)",
                preemption_active=True,
                arrival_time=metrics.j1_arrival_time,
                clearance_time=metrics.j3_clearance_time,
                traversal_duration=metrics.total_traversal_duration,
                completed=metrics.completed,
            )
            self._emergency_events.append(event)
            self._record_decision(
                sim_time=sim_time,
                junction_id="CORRIDOR",
                current_phase=0,
                target_phase=2,
                action="EMERGENCY_PREEMPTION",
                reason=f"Emergency wave priority granted for ambulance {metrics.vehicle_id}. Preemption locked at {locked_junctions}.",
            )

        if metrics.completed and self._emergency_events:
            self._emergency_events[-1].completed = True
            self._emergency_events[-1].preemption_active = False
            self._emergency_events[-1].traversal_duration = metrics.total_traversal_duration

    def _run_coordinated_with_logging(
        self,
        sim: MultiIntersectionSimulation,
        states: Dict[str, IntersectionState],
        sim_time: float,
    ) -> None:
        """Executes coordinated control logic while capturing rationales."""
        # J2 adaptive controller
        j2_ctrl = sim.controllers["J2"]
        if not j2_ctrl.emergency_locked and j2_ctrl.is_green():
            j2_state = states["J2"]
            curr_phase = j2_ctrl.get_phase()
            hosur_q = j2_state.approach_queues.get("corridor_hosur", 0)
            madiwala_q = j2_state.approach_queues.get("madiwala", 0)
            upstream_inflow_bonus = int(sim.hub.get_expected_inflow("J2") * 5)
            effective_hosur_q = hosur_q + upstream_inflow_bonus
            elapsed = j2_ctrl.get_green_elapsed(sim_time)

            if curr_phase == 0:  # Hosur Green
                if elapsed >= j2_ctrl.min_green and madiwala_q > effective_hosur_q + 2:
                    j2_ctrl.request_switch(target_green_phase=2, sim_time=sim_time)
                    self._record_decision(
                        sim_time, "J2", 0, 2, "SWITCH",
                        f"Cross-traffic demand (Madiwala: {madiwala_q} veh) exceeded Hosur pressure ({effective_hosur_q} veh)."
                    )
                elif effective_hosur_q > 0 and effective_hosur_q >= madiwala_q:
                    j2_ctrl.extend_current_green(sim_time)
                    self._record_decision(
                        sim_time, "J2", 0, 0, "EXTEND",
                        f"Extended Hosur Road green phase. Inflow bonus: +{upstream_inflow_bonus} vehicles from J1."
                    )
            elif curr_phase == 2:  # Madiwala Green
                if elapsed >= j2_ctrl.min_green and effective_hosur_q > madiwala_q + 2:
                    j2_ctrl.request_switch(target_green_phase=0, sim_time=sim_time)
                    self._record_decision(
                        sim_time, "J2", 2, 0, "SWITCH",
                        f"Corridor arterial queue ({effective_hosur_q} veh) reclaimed green from Madiwala ({madiwala_q} veh)."
                    )
                elif madiwala_q > 0 and madiwala_q >= effective_hosur_q:
                    j2_ctrl.extend_current_green(sim_time)

        # J1 & J3 Progression Alignment
        for j_id, target_corridor_phase in [("J1", 2), ("J3", 2)]:
            ctrl = sim.controllers[j_id]
            if not ctrl.emergency_locked and ctrl.is_green():
                q_corridor = states[j_id].approach_queues.get("corridor_hosur", 0)
                q_cross = states[j_id].approach_queues.get("side_cross", 0)
                curr_p = ctrl.get_phase()
                elapsed = ctrl.get_green_elapsed(sim_time)

                if curr_p == target_corridor_phase:
                    if q_corridor > 0 and elapsed < ctrl.max_green:
                        ctrl.extend_current_green(sim_time)
                    elif elapsed >= ctrl.min_green and q_cross > q_corridor + 2:
                        ctrl.request_switch(target_green_phase=0, sim_time=sim_time)
                        self._record_decision(
                            sim_time, j_id, curr_p, 0, "SWITCH",
                            f"Side-cross queue ({q_cross} veh) exceeded corridor queue ({q_corridor} veh)."
                        )
                else:
                    if elapsed >= ctrl.min_green and q_corridor > q_cross:
                        ctrl.request_switch(target_green_phase=target_corridor_phase, sim_time=sim_time)
                        self._record_decision(
                            sim_time, j_id, curr_p, target_corridor_phase, "SWITCH",
                            f"Corridor progression aligned green phase {target_corridor_phase}."
                        )

    def _record_decision(
        self,
        sim_time: float,
        junction_id: str,
        current_phase: int,
        target_phase: Optional[int],
        action: str,
        reason: str,
        is_override: bool = False,
    ) -> None:
        """Appends decision to in-memory history and database."""
        item = DecisionItemSchema(
            id=len(self._decisions_log) + 1,
            simulation_time=sim_time,
            junction_id=junction_id,
            current_phase=current_phase,
            target_phase=target_phase,
            action=action,
            reason=reason,
            is_override=is_override,
            timestamp=datetime.utcnow().isoformat(),
        )
        self._decisions_log.append(item)
        if len(self._decisions_log) > 200:
            self._decisions_log.pop(0)

        # Save to DB if run active
        if self._current_run_id:
            db = SessionLocal()
            try:
                rec = SignalDecisionRecord(
                    run_id=self._current_run_id,
                    simulation_time=sim_time,
                    junction_id=junction_id,
                    current_phase=current_phase,
                    target_phase=target_phase,
                    action=action,
                    reason=reason,
                    is_override=is_override,
                )
                db.add(rec)
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()

    def _update_db_status(self, status: str) -> None:
        """Updates status of the current simulation run in database."""
        if not self._current_run_id:
            return
        db = SessionLocal()
        try:
            run_rec = db.query(SimulationRun).filter(SimulationRun.id == self._current_run_id).first()
            if run_rec:
                run_rec.status = status
                db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    def _broadcast_telemetry(self) -> None:
        """Schedules WebSocket broadcast on the main event loop."""
        if not self.loop or not self.loop.is_running():
            return

        payload = {
            "type": "TRAFFIC_UPDATE",
            "simulation_time": self._current_sim_time,
            "status": "RUNNING" if self._running and not self._paused else ("PAUSED" if self._paused else "STOPPED"),
            "mode": self._mode,
            "metrics": self.get_metrics(),
            "junctions": self.get_live_junctions(),
            "signals": self.get_signals(),
            "emergencies": self.get_emergencies(),
            "decisions": [d.model_dump() for d in self._decisions_log[-5:]],
        }

        try:
            asyncio.run_coroutine_threadsafe(ws_manager.broadcast(payload), self.loop)
        except Exception as exc:
            logger.debug(f"Broadcast threadsafe scheduling error: {exc}")

    # ------------------------------------------------------------------
    # Manual Operator Signal Override
    # ------------------------------------------------------------------

    def request_manual_override(
        self,
        junction_id: str,
        target_phase: int,
        confirmed: bool,
    ) -> Tuple[bool, str]:
        """
        Executes a safe, operator-confirmed manual phase override on a specific traffic light.
        Validates junction ID, phase legality, emergency lock status.
        """
        if not confirmed:
            return False, "Manual override requires explicit operator confirmation."

        with self._lock:
            if not self._running or not self._sim:
                return False, "Cannot override: Simulation is not currently running."

            junction_id = junction_id.upper()
            if junction_id not in self._sim.controllers:
                return False, f"Invalid junction ID '{junction_id}'. Must be J1, J2, or J3."

            ctrl = self._sim.controllers[junction_id]
            if ctrl.emergency_locked:
                return False, f"Override rejected: Junction {junction_id} is locked by active Emergency Green Wave priority."

            valid_phases = {0, 1, 2, 3}
            if target_phase not in valid_phases:
                return False, f"Invalid phase index {target_phase}. Valid phases for {junction_id} are {sorted(list(valid_phases))}."

            current_phase = ctrl.get_phase()
            ctrl.request_switch(target_green_phase=target_phase, sim_time=self._current_sim_time)

            self._record_decision(
                sim_time=self._current_sim_time,
                junction_id=junction_id,
                current_phase=current_phase,
                target_phase=target_phase,
                action="MANUAL_OVERRIDE",
                reason=f"Operator manually forced phase switch to {target_phase}.",
                is_override=True,
            )

            return True, f"Manual override successfully applied to {junction_id}: phase switched to {target_phase}."

    # ------------------------------------------------------------------
    # Public Getters for API
    # ------------------------------------------------------------------

    def get_status(self) -> SimulationStatusResponse:
        """Returns comprehensive status of current simulation."""
        with self._lock:
            return SimulationStatusResponse(
                running=self._running,
                paused=self._paused,
                simulation_time=self._current_sim_time,
                duration=self._duration,
                mode=self._mode,
                seed=self._seed,
                controller="Coordinated Adaptive (Inflow-Aware + Green Wave)" if self._mode == "coordinated" else "Fixed-Time Baseline",
                junctions=["J1", "J2", "J3"],
                error=self._error_message,
            )

    def get_live_junctions(self) -> Dict[str, Any]:
        """Returns latest extracted junction states."""
        with self._lock:
            result = {}
            for j_id in ["J1", "J2", "J3"]:
                st = self._latest_states.get(j_id)
                if st:
                    em = st.emissions
                    emergencies_list = [
                        EmergencyApproachingSchema(
                            vehicle_id=e.vehicle_id,
                            approach=e.approach,
                            distance_to_stopline_m=round(e.distance_to_stopline_m, 1),
                            speed_mps=round(e.speed_mps, 1),
                            estimated_arrival_s=round(e.estimated_arrival_s, 1),
                        )
                        for e in st.approaching_emergency_vehicles
                    ]
                    result[j_id] = JunctionStateSchema(
                        junction_id=j_id,
                        tls_id=st.tls_id,
                        simulation_time=st.simulation_time,
                        current_phase=st.current_phase,
                        phase_duration=st.phase_duration,
                        phase_elapsed=st.phase_elapsed,
                        time_to_switch=st.time_to_switch,
                        approach_queues=st.approach_queues,
                        total_queue=st.total_queue,
                        average_speed_kmh=round(st.average_speed_kmh, 2),
                        total_waiting_time=round(st.total_waiting_time, 2),
                        vehicle_count=st.vehicle_count,
                        vehicle_ids=st.vehicle_ids,
                        emissions=EmissionSchema(
                            co2_mg_s=round(em.co2_mg_s, 2),
                            nox_mg_s=round(em.nox_mg_s, 2),
                            fuel_ml_s=round(em.fuel_ml_s, 2),
                            co_mg_s=round(em.co_mg_s, 2),
                            pmx_mg_s=round(em.pmx_mg_s, 2),
                            accumulated_co2_kg=round(em.accumulated_co2_kg, 4),
                            accumulated_fuel_liters=round(em.accumulated_fuel_liters, 4),
                        ),
                        emergency_present=len(emergencies_list) > 0,
                        approaching_emergency_vehicles=emergencies_list,
                    ).model_dump()
                else:
                    # Default placeholder if not yet stepped
                    result[j_id] = JunctionStateSchema(
                        junction_id=j_id,
                        tls_id="",
                        simulation_time=self._current_sim_time,
                        current_phase=0,
                        phase_duration=0.0,
                        phase_elapsed=0.0,
                        time_to_switch=0.0,
                    ).model_dump()
            return result

    def get_metrics(self) -> Dict[str, Any]:
        """Returns corridor-wide metrics summary."""
        with self._lock:
            if self._cached_metrics:
                return self._cached_metrics
            return {
                "simulation_time": self._current_sim_time,
                "total_vehicles": 0,
                "throughput_vehicles": 0,
                "mean_speed_kmh": 0.0,
                "total_corridor_waiting_time_s": 0.0,
                "mean_corridor_queue": 0.0,
                "max_corridor_queue": 0,
                "total_co2_kg": 0.0,
                "total_nox_g": 0.0,
                "total_fuel_liters": 0.0,
                "emergency_traversal_duration_s": 0.0,
                "junction_queues": {"J1": 0, "J2": 0, "J3": 0},
            }

    def get_signals(self) -> Dict[str, Any]:
        """Returns signal controllers status for J1, J2, J3."""
        with self._lock:
            signals = {}
            for j_id in ["J1", "J2", "J3"]:
                st = self._latest_states.get(j_id)
                ctrl = self._sim.controllers.get(j_id) if self._sim else None
                curr_phase = st.current_phase if st else 0
                is_grn = ctrl.is_green(curr_phase) if ctrl else (curr_phase in {0, 2})
                is_yel = ctrl.is_yellow(curr_phase) if ctrl else (curr_phase in {1, 3})
                locked = ctrl.emergency_locked if ctrl else False

                signals[j_id] = SignalInfoSchema(
                    junction_id=j_id,
                    tls_id=st.tls_id if st else "",
                    current_phase=curr_phase,
                    is_green=is_grn,
                    is_yellow=is_yel,
                    phase_elapsed=st.phase_elapsed if st else 0.0,
                    time_to_switch=st.time_to_switch if st else 0.0,
                    min_green=ctrl.min_green if ctrl else 15.0,
                    max_green=ctrl.max_green if ctrl else 60.0,
                    emergency_locked=locked,
                    approach_queues=st.approach_queues if st else {},
                ).model_dump()
            return signals

    def get_emergencies(self) -> Dict[str, Any]:
        """Returns emergency alerts and traversal performance."""
        with self._lock:
            locked = []
            active_veh = None
            if self._sim and self._enable_emergency:
                coord = self._sim.emergency_coordinator
                locked = [j for j, ctrl in self._sim.controllers.items() if ctrl.emergency_locked]
                if coord.metrics.vehicle_id and not coord.metrics.completed:
                    active_veh = coord.metrics.vehicle_id

            return EmergencyResponse(
                active_emergency=len(locked) > 0 or active_veh is not None,
                emergency_locked_junctions=locked,
                total_completed_events=len([e for e in self._emergency_events if e.completed]),
                active_vehicle_id=active_veh,
                events=list(self._emergency_events),
            ).model_dump()

    def get_decisions(self) -> List[DecisionItemSchema]:
        """Returns controller decisions history."""
        with self._lock:
            return list(self._decisions_log)


# Global singleton instance
sim_service = SimulationService()
