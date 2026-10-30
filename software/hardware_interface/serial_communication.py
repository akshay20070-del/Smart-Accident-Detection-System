"""
Serial Communication Manager Module.

Manages connection lifecycle with ESP32 over USB Serial:
- Automatic available COM / tty port enumeration.
- Connect, disconnect, and baud-rate configuration (default 115200).
- Thread-safe or non-blocking line reading with timeout protection.
- State indicators for HARDWARE vs SIMULATION modes.
- Clear error reporting when hardware is disconnected or unavailable.
"""

from typing import List, Optional, Dict, Any
import time

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    serial = None
    SERIAL_AVAILABLE = False

from .sensor_data_parser import SensorDataParser


class SerialCommunicationManager:
    """
    Handles physical USB serial communication with the ESP32 microcontroller.
    """

    def __init__(self, baud_rate: int = 115200, timeout: float = 1.0):
        """
        Initialize serial communication manager.

        Args:
            baud_rate: Baud rate matching ESP32 firmware (standard: 115200).
            timeout: Read timeout in seconds.
        """
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial_connection: Optional[Any] = None
        self.active_port: Optional[str] = None
        self.is_connected: bool = False
        self.last_error: Optional[str] = None
        self.parser = SensorDataParser()

    @staticmethod
    def list_available_ports() -> List[str]:
        """
        Scan and return list of all physically available serial ports.

        Returns:
            List of port identifiers, e.g. ['COM3', 'COM4'] on Windows or ['/dev/ttyUSB0'] on Linux.
        """
        if not SERIAL_AVAILABLE:
            return []
        try:
            ports = serial.tools.list_ports.comports()
            return [port.device for port in ports]
        except Exception:
            return []

    def connect(self, port_name: str) -> bool:
        """
        Establish connection to specified serial port.

        Args:
            port_name: Target serial port (e.g., 'COM3').

        Returns:
            True if connection succeeded, False otherwise.
        """
        if not SERIAL_AVAILABLE:
            self.last_error = "PySerial is not installed. Run 'pip install pyserial'."
            self.is_connected = False
            return False

        try:
            self.disconnect()  # Ensure prior connection closed
            self.serial_connection = serial.Serial(
                port=port_name,
                baudrate=self.baud_rate,
                timeout=self.timeout,
            )
            # Short sleep to allow ESP32 DTR/RTS reset line to settle
            time.sleep(1.5)
            self.active_port = port_name
            self.is_connected = True
            self.last_error = None
            return True
        except serial.SerialException as exc:
            self.last_error = f"Serial connection error on {port_name}: {exc}"
            self.is_connected = False
            self.serial_connection = None
            return False
        except Exception as exc:
            self.last_error = f"Unexpected error opening {port_name}: {exc}"
            self.is_connected = False
            self.serial_connection = None
            return False

    def disconnect(self) -> None:
        """Close the active serial connection safely."""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
            except Exception:
                pass
        self.serial_connection = None
        self.is_connected = False
        self.active_port = None

    def read_telemetry(self) -> Optional[Dict[str, Any]]:
        """
        Read the next line from the ESP32 and parse it into telemetry.

        Returns:
            Validated telemetry dict, or None if no valid line read or hardware disconnected.
        """
        if not self.is_connected or not self.serial_connection:
            self.last_error = "Hardware disconnected: Serial port is not open."
            return None

        try:
            if self.serial_connection.in_waiting > 0:
                raw_bytes = self.serial_connection.readline()
                raw_line = raw_bytes.decode("utf-8", errors="replace").strip()
                if raw_line:
                    parsed = self.parser.parse_line(raw_line)
                    return parsed
            return None
        except serial.SerialException as exc:
            self.last_error = f"Device disconnected unexpectedly: {exc}"
            self.disconnect()
            return None
        except Exception as exc:
            self.last_error = f"Read error: {exc}"
            return None

    def get_status_info(self) -> Dict[str, Any]:
        """Return diagnostic status summary."""
        return {
            "pyserial_available": SERIAL_AVAILABLE,
            "is_connected": self.is_connected,
            "active_port": self.active_port,
            "baud_rate": self.baud_rate,
            "last_error": self.last_error,
        }
