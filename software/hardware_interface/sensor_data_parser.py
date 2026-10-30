"""
Sensor Data Parser Module.

Safely parses and validates structured telemetry lines emitted by the ESP32 firmware over USB Serial.
Primary Protocol: JSON Lines (JSONL).
Example:
    {"x":0.2,"y":0.3,"z":9.8,"latitude":11.0168,"longitude":76.9558,"status":"NORMAL"}

Includes defensive fallbacks for corrupted/partial frames and CSV formatting.
"""

import json
from typing import Dict, Any, Optional, Tuple


class SensorDataParser:
    """
    Parses and sanitizes incoming serial data frames from ESP32 or simulated streams.
    """

    @staticmethod
    def parse_line(raw_line: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single raw string line into a validated telemetry dictionary.

        Args:
            raw_line: Raw string line read from serial port.

        Returns:
            Dictionary with validated fields:
            {
                'x': float,
                'y': float,
                'z': float,
                'latitude': float,
                'longitude': float,
                'status': str
            }
            or None if the line could not be parsed into valid telemetry.
        """
        if not raw_line or not isinstance(raw_line, str):
            return None

        cleaned = raw_line.strip()
        if not cleaned:
            return None

        # Attempt 1: Standard JSON parsing
        if cleaned.startswith("{") and cleaned.endswith("}"):
            try:
                data = json.loads(cleaned)
                return SensorDataParser._validate_and_normalize(data)
            except (json.JSONDecodeError, ValueError):
                pass

        # Attempt 2: Fallback CSV parsing "x,y,z,lat,lon,status"
        if "," in cleaned:
            parts = [p.strip() for p in cleaned.split(",")]
            if len(parts) >= 3:
                try:
                    data = {
                        "x": float(parts[0]),
                        "y": float(parts[1]),
                        "z": float(parts[2]),
                        "latitude": float(parts[3]) if len(parts) > 3 else 11.0168,
                        "longitude": float(parts[4]) if len(parts) > 4 else 76.9558,
                        "status": parts[5] if len(parts) > 5 else "NORMAL",
                    }
                    return SensorDataParser._validate_and_normalize(data)
                except (ValueError, IndexError):
                    pass

        return None

    @staticmethod
    def _validate_and_normalize(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate data types and bounds, applying safe defaults for missing optional fields.
        """
        try:
            x = float(data.get("x", 0.0))
            y = float(data.get("y", 0.0))
            z = float(data.get("z", 9.8))

            latitude = float(data.get("latitude", 11.0168))
            longitude = float(data.get("longitude", 76.9558))

            status = str(data.get("status", "NORMAL")).strip().upper()

            # Sanity bounds check
            if not (-90.0 <= latitude <= 90.0):
                latitude = 11.0168
            if not (-180.0 <= longitude <= 180.0):
                longitude = 76.9558

            return {
                "x": round(x, 2),
                "y": round(y, 2),
                "z": round(z, 2),
                "latitude": round(latitude, 6),
                "longitude": round(longitude, 6),
                "status": status,
            }
        except (ValueError, TypeError):
            return None

    @staticmethod
    def to_json_line(x: float, y: float, z: float, lat: float, lon: float, status: str = "NORMAL") -> str:
        """
        Format telemetry into the standard ESP32 JSON line string.

        Args:
            x, y, z: Accelerations in m/s^2.
            lat, lon: Coordinates.
            status: Vehicle status string.

        Returns:
            One JSON-formatted line.
        """
        payload = {
            "x": round(x, 2),
            "y": round(y, 2),
            "z": round(z, 2),
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "status": status,
        }
        return json.dumps(payload)
