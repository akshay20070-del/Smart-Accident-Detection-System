"""
Main Entry Point for Smart Accident Detection System.

Usage:
    python main.py             -> Launches interactive Streamlit web dashboard.
    python main.py --cli       -> Runs headless command-line sensor simulation loop.
    python main.py --help      -> Displays command options.
"""

import sys
import os
import time
import argparse

# Add project root directory to path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from software.core.accident_detection import AccidentDetector, DetectionState
from software.core.sensor_simulator import SensorSimulator
from software.core.gps_simulator import GPSSimulator
from software.core.alert_manager import AlertManager


def run_cli_mode(duration_seconds: int = 20, simulate_crash_at: int = 8):
    """
    Run headless terminal monitoring loop with simulated sensor readings.

    Args:
        duration_seconds: How long the simulation loop should run.
        simulate_crash_at: Second at which to trigger a simulated crash.
    """
    print("=" * 70)
    print("  SMART ACCIDENT DETECTION & EMERGENCY ALERT SYSTEM (CLI MODE)")
    print("=" * 70)
    print("Initializing components...")
    detector = AccidentDetector(impact_threshold=28.0, warning_threshold=18.0, consecutive_required=2)
    sensor_sim = SensorSimulator()
    gps_sim = GPSSimulator(initial_lat=11.0168, initial_lon=76.9558)
    alert_mgr = AlertManager()

    print(f"Impact Threshold : {detector.impact_threshold} m/s^2 (~2.85 g)")
    print(f"Warning Threshold: {detector.warning_threshold} m/s^2 (~1.83 g)")
    print(f"Simulation will trigger a crash test at t = {simulate_crash_at}s\n")
    print(f"{'Time':<10} | {'X':<6} {'Y':<6} {'Z':<6} | {'Magnitude':<10} | {'Status':<18} | {'GPS (Lat, Lon)'}")
    print("-" * 75)

    start_time = time.time()
    crash_triggered = False

    # Ensure utf-8 output encoding on Windows consoles
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    try:
        step = 0
        while (time.time() - start_time) < duration_seconds:
            elapsed = int(time.time() - start_time)

            if elapsed >= simulate_crash_at and not crash_triggered:
                print("\n>>> [SIMULATION EVENT]: TRIGGERING SUDDEN VEHICLE COLLISION! <<<\n")
                sensor_sim.trigger_impact(duration_steps=3)
                crash_triggered = True

            reading = sensor_sim.get_reading()
            lat, lon = gps_sim.update_position(drift=True)

            result = detector.process_reading(reading["x"], reading["y"], reading["z"])
            state = result["state"]
            mag = result["magnitude"]

            status_display = state.value
            if state == DetectionState.ACCIDENT_DETECTED:
                status_display = "[!!] ACCIDENT!"
            elif state == DetectionState.WARNING:
                status_display = "[!]  WARNING"
            elif state == DetectionState.NORMAL:
                status_display = "[OK] NORMAL"

            print(
                f"t={elapsed:02d}s     | "
                f"{reading['x']:>5.2f} {reading['y']:>5.2f} {reading['z']:>5.2f} | "
                f"{mag:>6.2f} m/s² | "
                f"{status_display:<18} | "
                f"{lat:.5f}, {lon:.5f}"
            )

            if state == DetectionState.ACCIDENT_DETECTED and len(alert_mgr.alert_history) == 0:
                maps_url = GPSSimulator.get_maps_url(lat, lon)
                alert = alert_mgr.trigger_emergency_alert(lat, lon, mag, maps_url)
                print("\n" + "#" * 70)
                print(">>> EMERGENCY ALERT DISPATCHED (SIMULATED SMS) <<<")
                print(f"Recipient: {alert.recipient_phone}")
                print(f"Message  : {alert.message_content}")
                print("#" * 70 + "\n")

            time.sleep(1.0)
            step += 1

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

    print("\nSimulation completed.")
    print("=" * 70)


def launch_dashboard():
    """Launch the Streamlit web dashboard via subprocess."""
    import subprocess
    dashboard_path = os.path.join(CURRENT_DIR, "dashboard", "app.py")
    print(f"Launching Streamlit Dashboard from: {dashboard_path}")
    subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Accident Detection System Launcher")
    parser.add_argument("--cli", action="store_true", help="Run headless in terminal mode instead of web UI")
    parser.add_argument("--duration", type=int, default=20, help="Duration in seconds for CLI mode")
    args = parser.parse_args()

    if args.cli:
        run_cli_mode(duration_seconds=args.duration)
    else:
        launch_dashboard()
