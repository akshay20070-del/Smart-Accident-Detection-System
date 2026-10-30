"""Core detection and simulation package for Smart Accident Detection System."""
from .accident_detection import AccidentDetector, DetectionState
from .sensor_simulator import SensorSimulator
from .gps_simulator import GPSSimulator
from .alert_manager import AlertManager, EmergencyAlert

__all__ = [
    "AccidentDetector",
    "DetectionState",
    "SensorSimulator",
    "GPSSimulator",
    "AlertManager",
    "EmergencyAlert",
]
