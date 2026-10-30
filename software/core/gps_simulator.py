"""
GPS Simulator Module.

Generates realistic geographic coordinates (Latitude, Longitude), allows user customization,
and constructs direct Google Maps tracking links for emergency alerts.
"""

import random
from typing import Dict, Tuple


class GPSSimulator:
    """
    Simulates a NEO-6M GPS receiver providing NMEA-style positioning fixes.
    Default reference coordinates: Coimbatore / Bangalore tech hub corridor.
    """

    def __init__(self, initial_lat: float = 11.0168, initial_lon: float = 76.9558):
        """
        Initialize GPS simulator with base coordinates.

        Args:
            initial_lat: Starting latitude in decimal degrees (e.g. 11.0168).
            initial_lon: Starting longitude in decimal degrees (e.g. 76.9558).
        """
        self.latitude = initial_lat
        self.longitude = initial_lon
        self.speed_kmh = 45.0  # Simulated vehicle speed

    def set_custom_coordinates(self, lat: float, lon: float) -> None:
        """
        Override simulator with user-defined coordinates.

        Args:
            lat: Custom latitude (-90.0 to +90.0).
            lon: Custom longitude (-180.0 to +180.0).
        """
        if not (-90.0 <= lat <= 90.0):
            raise ValueError(f"Latitude {lat} is out of valid bounds [-90, +90].")
        if not (-180.0 <= lon <= 180.0):
            raise ValueError(f"Longitude {lon} is out of valid bounds [-180, +180].")

        self.latitude = lat
        self.longitude = lon

    def update_position(self, drift: bool = True) -> Tuple[float, float]:
        """
        Update vehicle position with realistic minor road drift.

        Args:
            drift: If True, adds small realistic displacement representing motion.

        Returns:
            Tuple of (latitude, longitude).
        """
        if drift:
            # ~0.00005 deg is roughly 5-6 meters displacement
            delta_lat = random.uniform(-0.00004, 0.00008)
            delta_lon = random.uniform(-0.00004, 0.00008)
            self.latitude += delta_lat
            self.longitude += delta_lon

        return round(self.latitude, 6), round(self.longitude, 6)

    def get_coordinates(self) -> Dict[str, float]:
        """Return the current coordinates as a dictionary."""
        return {
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
        }

    @staticmethod
    def get_maps_url(lat: float, lon: float) -> str:
        """
        Generate a direct Google Maps URL for pinpointing coordinates.

        Args:
            lat: Latitude.
            lon: Longitude.

        Returns:
            Standard Google Maps link string.
        """
        return f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}"
