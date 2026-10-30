"""
Accident Detection Algorithm Module.

Calculates acceleration magnitude from 3-axis accelerometer readings (X, Y, Z),
filters transient noise using consecutive reading windows, classifies vehicle states
(NORMAL, WARNING, ACCIDENT_DETECTED, CANCELLED), and supports manual cancellation.
"""

import math
from collections import deque
from enum import Enum
from typing import Dict, Any, Optional, Tuple


class DetectionState(str, Enum):
    """Enumeration of possible vehicle safety states."""
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    ACCIDENT_DETECTED = "ACCIDENT_DETECTED"
    CANCELLED = "CANCELLED"


class AccidentDetector:
    """
    Evaluates tri-axial acceleration to detect vehicular collisions.

    Mathematical Basis:
        Magnitude: A = sqrt(X^2 + Y^2 + Z^2)
        Normal static gravity: ~9.8 m/s^2 (1.0 g)
        Sudden collision threshold: typically > 25-35 m/s^2 (~2.5g - 3.5g)
    """

    def __init__(
        self,
        impact_threshold: float = 28.0,
        warning_threshold: float = 18.0,
        consecutive_required: int = 2,
        buffer_size: int = 10,
    ):
        """
        Initialize detector with configurable thresholds.

        Args:
            impact_threshold: Acceleration magnitude (m/s^2) for accident trigger.
            warning_threshold: Acceleration magnitude (m/s^2) for warning alert.
            consecutive_required: Consecutive anomalous readings to confirm accident (noise filter).
            buffer_size: Size of sliding history buffer for rolling average.
        """
        self.impact_threshold = impact_threshold
        self.warning_threshold = warning_threshold
        self.consecutive_required = consecutive_required

        # Sliding window buffer to compute rolling statistics and filter transient spikes
        self.history_buffer = deque(maxlen=buffer_size)

        # Counter for consecutive anomalous readings exceeding threshold
        self.consecutive_spikes = 0

        # Current state
        self.state: DetectionState = DetectionState.NORMAL
        self.last_magnitude: float = 9.8
        self.last_acceleration: Tuple[float, float, float] = (0.0, 0.0, 9.8)

        # Cancellation state
        self.cancellation_active: bool = False

    @staticmethod
    def calculate_magnitude(x: float, y: float, z: float) -> float:
        """
        Calculate scalar acceleration magnitude from 3-axis components.

        Formula:
            A = sqrt(x^2 + y^2 + z^2)

        Args:
            x: Acceleration along X-axis (m/s^2)
            y: Acceleration along Y-axis (m/s^2)
            z: Acceleration along Z-axis (m/s^2)

        Returns:
            Magnitude A in m/s^2
        """
        return math.sqrt(x**2 + y**2 + z**2)

    def process_reading(self, x: float, y: float, z: float) -> Dict[str, Any]:
        """
        Process a new (x, y, z) accelerometer reading and update detection state.

        Args:
            x: X-axis acceleration in m/s^2
            y: Y-axis acceleration in m/s^2
            z: Z-axis acceleration in m/s^2

        Returns:
            Dictionary containing processed metrics and detection status:
            {
                'x': float,
                'y': float,
                'z': float,
                'magnitude': float,
                'magnitude_g': float,
                'state': DetectionState,
                'is_accident': bool,
                'is_warning': bool,
                'consecutive_spikes': int
            }
        """
        self.last_acceleration = (x, y, z)
        magnitude = self.calculate_magnitude(x, y, z)
        self.last_magnitude = magnitude
        self.history_buffer.append(magnitude)

        # If user explicitly cancelled an alert, maintain CANCELLED state until reset
        if self.cancellation_active:
            return {
                "x": round(x, 2),
                "y": round(y, 2),
                "z": round(z, 2),
                "magnitude": round(magnitude, 2),
                "magnitude_g": round(magnitude / 9.80665, 2),
                "state": DetectionState.CANCELLED,
                "is_accident": False,
                "is_warning": False,
                "consecutive_spikes": self.consecutive_spikes,
            }

        # Analyze magnitude against thresholds
        if magnitude >= self.impact_threshold:
            self.consecutive_spikes += 1
            if self.consecutive_spikes >= self.consecutive_required:
                self.state = DetectionState.ACCIDENT_DETECTED
            else:
                self.state = DetectionState.WARNING
        elif magnitude >= self.warning_threshold:
            self.consecutive_spikes = max(0, self.consecutive_spikes - 1)
            # Only downgrade if not already locked in accident state
            if self.state != DetectionState.ACCIDENT_DETECTED:
                self.state = DetectionState.WARNING
        else:
            self.consecutive_spikes = 0
            # If accident was already locked, retain it until user cancels or resets
            if self.state != DetectionState.ACCIDENT_DETECTED:
                self.state = DetectionState.NORMAL

        return {
            "x": round(x, 2),
            "y": round(y, 2),
            "z": round(z, 2),
            "magnitude": round(magnitude, 2),
            "magnitude_g": round(magnitude / 9.80665, 2),
            "state": self.state,
            "is_accident": (self.state == DetectionState.ACCIDENT_DETECTED),
            "is_warning": (self.state == DetectionState.WARNING),
            "consecutive_spikes": self.consecutive_spikes,
        }

    def cancel_alert(self) -> None:
        """User manual cancellation: overrides accident state to CANCELLED."""
        self.cancellation_active = True
        self.state = DetectionState.CANCELLED
        self.consecutive_spikes = 0

    def reset(self) -> None:
        """Reset the detector back to clean NORMAL state."""
        self.cancellation_active = False
        self.state = DetectionState.NORMAL
        self.consecutive_spikes = 0
        self.history_buffer.clear()
        self.last_magnitude = 9.8
        self.last_acceleration = (0.0, 0.0, 9.8)

    def force_accident(self) -> None:
        """Manually trigger accident state for testing/demonstration."""
        self.cancellation_active = False
        self.state = DetectionState.ACCIDENT_DETECTED
        self.consecutive_spikes = self.consecutive_required
