"""
Unit Tests for Smart Accident Detection and Emergency Alert System.

Tests cover:
1. Magnitude mathematical calculation
2. State transitions (NORMAL, WARNING, ACCIDENT_DETECTED, CANCELLED)
3. Consecutive reading filter (rejection of single transient spikes)
4. Manual alert cancellation
5. System reset functionality
6. Telemetry JSON & CSV parsing
7. GPS simulation & Google Maps link generation
8. Emergency Alert Manager history & messaging
"""

import pytest
import math
from software.core.accident_detection import AccidentDetector, DetectionState
from software.core.sensor_simulator import SensorSimulator
from software.core.gps_simulator import GPSSimulator
from software.core.alert_manager import AlertManager
from software.hardware_interface.sensor_data_parser import SensorDataParser


class TestAccidentDetector:
    """Tests for AccidentDetector core algorithm."""

    def test_magnitude_calculation(self):
        detector = AccidentDetector()

        # Static upright vehicle (Earth gravity on Z)
        mag_static = detector.calculate_magnitude(0.0, 0.0, 9.8)
        assert pytest.approx(mag_static, 0.01) == 9.8

        # Pythagorean 3-4-0 test: sqrt(3^2 + 4^2 + 0^2) = 5
        mag_340 = detector.calculate_magnitude(3.0, 4.0, 0.0)
        assert pytest.approx(mag_340, 0.001) == 5.0

        # Tri-axial symmetric test: sqrt(10^2 + 10^2 + 10^2) = sqrt(300) ~ 17.3205
        mag_sym = detector.calculate_magnitude(10.0, 10.0, 10.0)
        assert pytest.approx(mag_sym, 0.01) == math.sqrt(300)

    def test_normal_driving_reading(self):
        detector = AccidentDetector(impact_threshold=28.0, warning_threshold=18.0)
        result = detector.process_reading(0.2, -0.3, 9.81)

        assert result["state"] == DetectionState.NORMAL
        assert result["is_accident"] is False
        assert result["is_warning"] is False
        assert result["magnitude"] < 18.0

    def test_single_transient_spike_triggers_warning_not_accident(self):
        """A single high-G spike (e.g. sharp pothole) should enter WARNING when consecutive_required=2."""
        detector = AccidentDetector(impact_threshold=28.0, warning_threshold=18.0, consecutive_required=2)

        # First spike
        res1 = detector.process_reading(30.0, 5.0, 9.8)
        assert res1["state"] == DetectionState.WARNING
        assert res1["is_accident"] is False
        assert res1["consecutive_spikes"] == 1

        # Returns to normal -> should recover
        res2 = detector.process_reading(0.1, 0.0, 9.8)
        assert res2["state"] == DetectionState.NORMAL
        assert res2["is_accident"] is False

    def test_consecutive_spikes_trigger_accident(self):
        """Two consecutive readings above impact threshold must trigger ACCIDENT_DETECTED."""
        detector = AccidentDetector(impact_threshold=28.0, warning_threshold=18.0, consecutive_required=2)

        # 1st spike
        res1 = detector.process_reading(32.0, 6.0, 10.0)
        assert res1["state"] == DetectionState.WARNING

        # 2nd consecutive spike
        res2 = detector.process_reading(35.0, 4.0, 12.0)
        assert res2["state"] == DetectionState.ACCIDENT_DETECTED
        assert res2["is_accident"] is True

    def test_manual_cancellation(self):
        """User can cancel an active accident alert."""
        detector = AccidentDetector(impact_threshold=28.0, consecutive_required=1)
        detector.process_reading(40.0, 0.0, 10.0)
        assert detector.state == DetectionState.ACCIDENT_DETECTED

        detector.cancel_alert()
        assert detector.state == DetectionState.CANCELLED

        # Subsequent readings while cancelled remain CANCELLED until reset
        res = detector.process_reading(0.0, 0.0, 9.8)
        assert res["state"] == DetectionState.CANCELLED

    def test_system_reset(self):
        """Reset clears alert state and history buffer."""
        detector = AccidentDetector(impact_threshold=28.0, consecutive_required=1)
        detector.process_reading(40.0, 0.0, 10.0)
        assert detector.state == DetectionState.ACCIDENT_DETECTED

        detector.reset()
        assert detector.state == DetectionState.NORMAL
        assert detector.consecutive_spikes == 0
        assert len(detector.history_buffer) == 0


class TestSensorSimulator:
    """Tests for SensorSimulator."""

    def test_normal_sensor_readings(self):
        sim = SensorSimulator()
        data = sim.get_reading()
        assert "x" in data and "y" in data and "z" in data
        assert "motion_type" in data
        # Normal reading should have Z roughly around gravity
        assert 5.0 <= abs(data["z"]) <= 18.0

    def test_manual_impact_trigger(self):
        sim = SensorSimulator()
        sim.trigger_impact(duration_steps=2)

        reading1 = sim.get_reading()
        assert reading1["motion_type"] == "COLLISION_IMPACT"
        mag1 = math.sqrt(reading1["x"]**2 + reading1["y"]**2 + reading1["z"]**2)
        assert mag1 >= 25.0  # High-G collision magnitude


class TestGPSSimulator:
    """Tests for GPSSimulator."""

    def test_gps_default_and_custom_coords(self):
        gps = GPSSimulator(initial_lat=11.0168, initial_lon=76.9558)
        coords = gps.get_coordinates()
        assert coords["latitude"] == 11.0168
        assert coords["longitude"] == 76.9558

        gps.set_custom_coordinates(13.0827, 80.2707)
        coords2 = gps.get_coordinates()
        assert coords2["latitude"] == 13.0827
        assert coords2["longitude"] == 80.2707

    def test_maps_url_generation(self):
        url = GPSSimulator.get_maps_url(11.0168, 76.9558)
        assert url == "https://www.google.com/maps?q=11.016800,76.955800"

    def test_invalid_coords_validation(self):
        gps = GPSSimulator()
        with pytest.raises(ValueError):
            gps.set_custom_coordinates(95.0, 80.0)  # Latitude > 90 invalid


class TestSensorDataParser:
    """Tests for ESP32 serial data parser."""

    def test_parse_valid_json_line(self):
        raw = '{"x":0.2,"y":0.3,"z":9.8,"latitude":11.0168,"longitude":76.9558,"status":"NORMAL"}'
        parsed = SensorDataParser.parse_line(raw)
        assert parsed is not None
        assert parsed["x"] == 0.2
        assert parsed["y"] == 0.3
        assert parsed["z"] == 9.8
        assert parsed["latitude"] == 11.0168
        assert parsed["longitude"] == 76.9558
        assert parsed["status"] == "NORMAL"

    def test_parse_fallback_csv(self):
        raw_csv = "0.2, 0.3, 9.8, 11.0168, 76.9558, NORMAL"
        parsed = SensorDataParser.parse_line(raw_csv)
        assert parsed is not None
        assert parsed["x"] == 0.2
        assert parsed["z"] == 9.8

    def test_parse_malformed_string_returns_none(self):
        assert SensorDataParser.parse_line("garbled serial junk @#$!") is None
        assert SensorDataParser.parse_line("") is None
        assert SensorDataParser.parse_line(None) is None

    def test_to_json_line(self):
        line = SensorDataParser.to_json_line(0.1, 0.2, 9.8, 11.0, 76.0, "NORMAL")
        parsed = SensorDataParser.parse_line(line)
        assert parsed["x"] == 0.1
        assert parsed["z"] == 9.8


class TestAlertManager:
    """Tests for AlertManager."""

    def test_trigger_and_cancel_alert(self):
        mgr = AlertManager()
        alert = mgr.trigger_emergency_alert(
            latitude=11.0168,
            longitude=76.9558,
            magnitude=38.5,
            maps_url="https://www.google.com/maps?q=11.016800,76.955800",
        )
        assert alert.alert_id == 1
        assert "EMERGENCY ALERT" in alert.message_content
        assert len(mgr.alert_history) == 1

        # Cancel
        cancelled = mgr.cancel_latest_alert()
        assert cancelled is not None
        assert cancelled.cancellation_status == "CANCELLED_BY_USER"
