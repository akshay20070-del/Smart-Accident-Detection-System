"""
Emergency Alert Manager Module.

Coordinates emergency alert events:
- Formats emergency SMS payloads with timestamps and Google Maps links.
- Logs alert history for forensic analysis.
- Maintains simulated SMS dispatch (clearly distinguished from real network transmission).
- Provides an extensible hardware GSM interface hook (e.g., SIM800L AT commands) for future physical integration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class EmergencyAlert:
    """Represents a recorded emergency accident alert event."""
    alert_id: int
    timestamp: str
    latitude: float
    longitude: float
    maps_url: str
    acceleration_magnitude: float
    status: str
    sms_status: str
    cancellation_status: str = "ACTIVE"
    recipient_phone: str = "+91 9876543210"
    message_content: str = field(init=False)

    def __post_init__(self):
        self.message_content = (
            f"EMERGENCY ALERT: Possible vehicle accident detected! "
            f"Impact: {self.acceleration_magnitude:.2f} m/s^2. "
            f"Location: {self.latitude:.6f}, {self.longitude:.6f}. "
            f"Time: {self.timestamp}. Track location: {self.maps_url}"
        )


class GSMHardwareInterface:
    """
    Interface specification and AT command generator for future physical GSM (SIM800L) integration.
    Allows easy plug-in when connected to an ESP32 or external GSM modem.
    """

    def __init__(self, serial_port: Optional[str] = None):
        self.serial_port = serial_port
        self.is_connected = False

    def generate_at_commands(self, phone_number: str, message: str) -> List[str]:
        """
        Generate standard 3GPP AT commands required to send an SMS via SIM800L.

        Args:
            phone_number: Recipient phone number (e.g., "+919876543210").
            message: Text payload.

        Returns:
            List of sequential AT command strings.
        """
        return [
            "AT",                   # Handshake check
            "AT+CMGF=1",            # Set SMS text mode
            f'AT+CMGS="{phone_number}"',  # Set destination number
            f"{message}\x1A",       # Payload terminated by Ctrl+Z (ASCII 26)
        ]

    def transmit_sms(self, phone_number: str, message: str) -> bool:
        """
        Transmit SMS over hardware GSM module.
        Currently stubbed for future hardware expansion.
        """
        # When hardware is active, this writes AT commands to serial interface
        return False


class AlertManager:
    """
    Central controller for logging, dispatching, and managing accident alerts.
    """

    def __init__(self, default_recipient: str = "+91 98765 43210"):
        self.default_recipient = default_recipient
        self.alert_history: List[EmergencyAlert] = []
        self._next_id: int = 1
        self.gsm_interface = GSMHardwareInterface()

    def trigger_emergency_alert(
        self,
        latitude: float,
        longitude: float,
        magnitude: float,
        maps_url: str,
        recipient: Optional[str] = None,
    ) -> EmergencyAlert:
        """
        Create and record a new emergency alert event.

        Args:
            latitude: GPS latitude.
            longitude: GPS longitude.
            magnitude: Impact acceleration in m/s^2.
            maps_url: Google Maps tracking URL.
            recipient: Optional emergency phone number override.

        Returns:
            Recorded EmergencyAlert instance.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        phone = recipient if recipient else self.default_recipient

        alert = EmergencyAlert(
            alert_id=self._next_id,
            timestamp=now_str,
            latitude=latitude,
            longitude=longitude,
            maps_url=maps_url,
            acceleration_magnitude=magnitude,
            status="ACCIDENT_DETECTED",
            sms_status="SIMULATED_DISPATCHED",
            cancellation_status="ACTIVE",
            recipient_phone=phone,
        )
        self._next_id += 1
        self.alert_history.insert(0, alert)  # newest first
        return alert

    def cancel_latest_alert(self) -> Optional[EmergencyAlert]:
        """
        Mark the most recent active alert as cancelled by the user.

        Returns:
            The cancelled EmergencyAlert or None.
        """
        for alert in self.alert_history:
            if alert.cancellation_status == "ACTIVE":
                alert.cancellation_status = "CANCELLED_BY_USER"
                alert.sms_status = "SIMULATED_CANCELLATION_SENT"
                return alert
        return None

    def get_history_as_dicts(self) -> List[Dict[str, Any]]:
        """Return history as tabular list of dictionaries."""
        return [
            {
                "ID": a.alert_id,
                "Timestamp": a.timestamp,
                "Coordinates": f"{a.latitude:.5f}, {a.longitude:.5f}",
                "Impact (m/s²)": f"{a.acceleration_magnitude:.2f}",
                "Status": a.status,
                "Dispatch": a.sms_status,
                "User State": a.cancellation_status,
                "Recipient": a.recipient_phone,
                "Maps URL": a.maps_url,
            }
            for a in self.alert_history
        ]

    def clear_history(self) -> None:
        """Clear the alert logs."""
        self.alert_history.clear()
        self._next_id = 1
