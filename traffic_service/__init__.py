"""
traffic_service package

Modular simulation, state extraction, multi-intersection coordination,
emergency green wave, and corridor traffic/emission metrics for the
Hybrid AI-Based Smart Traffic Control System.
"""

from .sumo_manager import SumoManager
from .state_extractor import IntersectionStateExtractor, IntersectionState, EmissionSnapshot
from .signal_controller import SignalController
from .communication import CorridorCommunicationHub, IntersectionMessage
from .emergency_wave import EmergencyWaveCoordinator
from .corridor_metrics import CorridorMetricsCollector, CorridorMetricsSummary
from .multi_intersection_simulation import MultiIntersectionSimulation
from .webster_controller import (
    WebsterTimingPlan,
    WebsterJunctionConfig,
    WebsterJunctionController,
    WebsterCorridorController,
    calculate_webster_timing,
    create_default_webster_configs,
)
from .nema_controller import (
    NEMARecallMode,
    NEMAPhaseConfig,
    NEMAJunctionConfig,
    NEMAJunctionController,
    NEMACorridorController,
    create_default_nema_configs,
)
from .max_pressure_controller import (
    MaxPressureMovement,
    MaxPressurePhaseConfig,
    MaxPressureJunctionConfig,
    MaxPressureJunctionController,
    MaxPressureCorridorController,
    create_default_max_pressure_configs,
)

__all__ = [
    "SumoManager",
    "IntersectionStateExtractor",
    "IntersectionState",
    "EmissionSnapshot",
    "SignalController",
    "CorridorCommunicationHub",
    "IntersectionMessage",
    "EmergencyWaveCoordinator",
    "CorridorMetricsCollector",
    "CorridorMetricsSummary",
    "MultiIntersectionSimulation",
    "WebsterTimingPlan",
    "WebsterJunctionConfig",
    "WebsterJunctionController",
    "WebsterCorridorController",
    "calculate_webster_timing",
    "create_default_webster_configs",
    "NEMARecallMode",
    "NEMAPhaseConfig",
    "NEMAJunctionConfig",
    "NEMAJunctionController",
    "NEMACorridorController",
    "create_default_nema_configs",
    "MaxPressureMovement",
    "MaxPressurePhaseConfig",
    "MaxPressureJunctionConfig",
    "MaxPressureJunctionController",
    "MaxPressureCorridorController",
    "create_default_max_pressure_configs",
]
