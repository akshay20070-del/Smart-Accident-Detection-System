"""
Smart Accident Detection & Emergency Alert System - Streamlit Dashboard.

Modern web-based monitoring dashboard:
- Real-time 3-axis accelerometer display (X, Y, Z, Magnitude).
- Live accident classification and warning banners.
- Simulation Mode (default) with manual accident trigger and custom GPS.
- Hardware Mode with USB Serial port detection for ESP32.
- Alert history table and simulated SMS notification logs.
- Interactive Google Maps tracking link.
"""

import sys
import os
import time
from datetime import datetime
import pandas as pd
import streamlit as st

# Add repository root to python sys.path to allow consistent imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from software.core.accident_detection import AccidentDetector, DetectionState
from software.core.sensor_simulator import SensorSimulator
from software.core.gps_simulator import GPSSimulator
from software.core.alert_manager import AlertManager
from software.hardware_interface.serial_communication import SerialCommunicationManager
from software.hardware_interface.sensor_data_parser import SensorDataParser

# Page configuration
st.set_page_config(
    page_title="Smart Accident Detection System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .status-normal {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 700;
        display: inline-block;
    }
    .status-warning {
        background-color: #FEF08A;
        color: #713F12;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 700;
        display: inline-block;
    }
    .status-accident {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 800;
        animation: pulse 1s infinite alternate;
        display: inline-block;
    }
    .status-cancelled {
        background-color: #E1EFFE;
        color: #1E429F;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 700;
        display: inline-block;
    }
    @keyframes pulse {
        0% { opacity: 0.7; transform: scale(0.98); }
        100% { opacity: 1; transform: scale(1.02); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "detector" not in st.session_state:
    st.session_state.detector = AccidentDetector(impact_threshold=28.0, warning_threshold=18.0)
if "sensor_sim" not in st.session_state:
    st.session_state.sensor_sim = SensorSimulator()
if "gps_sim" not in st.session_state:
    st.session_state.gps_sim = GPSSimulator(initial_lat=11.0168, initial_lon=76.9558)
if "alert_mgr" not in st.session_state:
    st.session_state.alert_mgr = AlertManager()
if "serial_mgr" not in st.session_state:
    st.session_state.serial_mgr = SerialCommunicationManager()
if "is_monitoring" not in st.session_state:
    st.session_state.is_monitoring = True
if "telemetry_history" not in st.session_state:
    st.session_state.telemetry_history = []
if "accident_alert_triggered" not in st.session_state:
    st.session_state.accident_alert_triggered = False

# Sidebar Controls
st.sidebar.image(
    "https://img.icons8.com/fluency/96/car-collision.png",
    width=80,
)
st.sidebar.title("System Control")

# Operation Mode Toggle
operation_mode = st.sidebar.radio(
    "Select Operating Mode:",
    options=["Simulation Mode", "Hardware Mode (ESP32)"],
    index=0,
    help="Default is Simulation Mode. Switch to Hardware Mode when ESP32 is attached via USB.",
)

# Detector Threshold Configurations
st.sidebar.markdown("---")
st.sidebar.subheader("Detection Parameters")
impact_thresh = st.sidebar.slider(
    "Impact Threshold (m/s²)",
    min_value=15.0,
    max_value=50.0,
    value=28.0,
    step=1.0,
    help="Calculated acceleration magnitude threshold that triggers accident state (~2.85g).",
)
warning_thresh = st.sidebar.slider(
    "Warning Threshold (m/s²)",
    min_value=10.0,
    max_value=25.0,
    value=18.0,
    step=1.0,
    help="Intermediate threshold indicating rough terrain, road bump, or sharp braking.",
)
consecutive_spikes = st.sidebar.slider(
    "Consecutive Reading Filter",
    min_value=1,
    max_value=5,
    value=2,
    help="Number of consecutive anomalous samples required to reject sensor glitches and false alarms.",
)

# Apply settings to detector
st.session_state.detector.impact_threshold = impact_thresh
st.session_state.detector.warning_threshold = warning_thresh
st.session_state.detector.consecutive_required = consecutive_spikes

# Hardware Configuration (if selected)
if operation_mode == "Hardware Mode (ESP32)":
    st.sidebar.markdown("---")
    st.sidebar.subheader("ESP32 Serial Configuration")
    available_ports = SerialCommunicationManager.list_available_ports()
    if available_ports:
        selected_port = st.sidebar.selectbox("Select COM Port", options=available_ports)
        if st.sidebar.button("Connect ESP32"):
            ok = st.session_state.serial_mgr.connect(selected_port)
            if ok:
                st.sidebar.success(f"Connected to {selected_port}!")
            else:
                st.sidebar.error(st.session_state.serial_mgr.last_error)
        if st.sidebar.button("Disconnect"):
            st.session_state.serial_mgr.disconnect()
            st.sidebar.info("Disconnected.")
    else:
        st.sidebar.warning("No physical COM ports detected. Please plug in ESP32 via USB.")
        st.sidebar.caption("Hardware mode is optional. You can use Simulation Mode without hardware.")

# Custom GPS Override
st.sidebar.markdown("---")
st.sidebar.subheader("GPS Coordinates")
custom_lat = st.sidebar.number_input(
    "Latitude (°N)",
    min_value=-90.0,
    max_value=90.0,
    value=st.session_state.gps_sim.latitude,
    format="%.6f",
)
custom_lon = st.sidebar.number_input(
    "Longitude (°E)",
    min_value=-180.0,
    max_value=180.0,
    value=st.session_state.gps_sim.longitude,
    format="%.6f",
)
if st.sidebar.button("Update GPS Position"):
    st.session_state.gps_sim.set_custom_coordinates(custom_lat, custom_lon)
    st.sidebar.success("Coordinates updated!")

# Emergency Contact Setting
st.sidebar.markdown("---")
emergency_phone = st.sidebar.text_input("Emergency Contact Number", value="+91 98765 43210")
st.session_state.alert_mgr.default_recipient = emergency_phone

# Main Title Header
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown('<div class="main-header">Smart Accident Detection & Emergency Alert System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">ECE Mini Project | Real-time Telemetry, Sensor Fusion & Emergency Dispatch</div>', unsafe_allow_html=True)

with col_status:
    # Operating Mode Badge
    if operation_mode == "Simulation Mode":
        st.info("Mode: **SIMULATION** (No Hardware Needed)")
    else:
        if st.session_state.serial_mgr.is_connected:
            st.success(f"Mode: **HARDWARE** ({st.session_state.serial_mgr.active_port})")
        else:
            st.warning("Mode: **HARDWARE** (Disconnected)")

# Control Buttons Bar
btn_col1, btn_col2, btn_col3, btn_col4, btn_col5 = st.columns(5)
with btn_col1:
    if st.session_state.is_monitoring:
        if st.button("⏹ Stop Monitoring", use_container_width=True):
            st.session_state.is_monitoring = False
            st.rerun()
    else:
        if st.button("▶ Start Monitoring", use_container_width=True, type="primary"):
            st.session_state.is_monitoring = True
            st.rerun()

with btn_col2:
    if st.button("💥 Simulate Accident", use_container_width=True, type="secondary"):
        st.session_state.sensor_sim.trigger_impact(duration_steps=3)
        st.session_state.accident_alert_triggered = False
        st.toast("⚠️ Severe collision impact simulated!", icon="💥")
        st.rerun()

with btn_col3:
    if st.button("🛑 Cancel Alert", use_container_width=True):
        st.session_state.detector.cancel_alert()
        st.session_state.alert_mgr.cancel_latest_alert()
        st.session_state.accident_alert_triggered = False
        st.toast("Alert cancelled by driver/operator.", icon="🛡️")
        st.rerun()

with btn_col4:
    if st.button("🔄 Reset System", use_container_width=True):
        st.session_state.detector.reset()
        st.session_state.sensor_sim.impact_active = False
        st.session_state.accident_alert_triggered = False
        st.toast("System reset to normal standby.", icon="🔄")
        st.rerun()

with btn_col5:
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.alert_mgr.clear_history()
        st.session_state.telemetry_history.clear()
        st.rerun()

st.markdown("---")

# Telemetry Retrieval: Fetch next sample
current_telemetry = None
if st.session_state.is_monitoring:
    if operation_mode == "Simulation Mode":
        # Pull from sensor simulator
        sim_data = st.session_state.sensor_sim.get_reading()
        lat, lon = st.session_state.gps_sim.update_position(drift=True)
        current_telemetry = {
            "x": sim_data["x"],
            "y": sim_data["y"],
            "z": sim_data["z"],
            "latitude": lat,
            "longitude": lon,
            "motion_type": sim_data["motion_type"],
        }
    else:
        # Hardware Mode
        if st.session_state.serial_mgr.is_connected:
            hw_data = st.session_state.serial_mgr.read_telemetry()
            if hw_data:
                current_telemetry = {
                    "x": hw_data["x"],
                    "y": hw_data["y"],
                    "z": hw_data["z"],
                    "latitude": hw_data.get("latitude", st.session_state.gps_sim.latitude),
                    "longitude": hw_data.get("longitude", st.session_state.gps_sim.longitude),
                    "motion_type": "HARDWARE_ESP32",
                }
            else:
                # Retain last known or placeholder
                current_telemetry = {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 9.8,
                    "latitude": st.session_state.gps_sim.latitude,
                    "longitude": st.session_state.gps_sim.longitude,
                    "motion_type": "WAITING_SERIAL_DATA",
                }
        else:
            current_telemetry = {
                "x": 0.0,
                "y": 0.0,
                "z": 9.8,
                "latitude": st.session_state.gps_sim.latitude,
                "longitude": st.session_state.gps_sim.longitude,
                "motion_type": "HARDWARE_DISCONNECTED",
            }
else:
    # Monitoring is paused
    current_telemetry = {
        "x": 0.0,
        "y": 0.0,
        "z": 9.8,
        "latitude": st.session_state.gps_sim.latitude,
        "longitude": st.session_state.gps_sim.longitude,
        "motion_type": "MONITORING_PAUSED",
    }

# Process telemetry through accident detection filter
eval_result = st.session_state.detector.process_reading(
    current_telemetry["x"], current_telemetry["y"], current_telemetry["z"]
)
detection_state = eval_result["state"]
mag = eval_result["magnitude"]
mag_g = eval_result["magnitude_g"]
maps_url = GPSSimulator.get_maps_url(current_telemetry["latitude"], current_telemetry["longitude"])

# Trigger emergency alert if accident detected
if detection_state == DetectionState.ACCIDENT_DETECTED and not st.session_state.accident_alert_triggered:
    st.session_state.alert_mgr.trigger_emergency_alert(
        latitude=current_telemetry["latitude"],
        longitude=current_telemetry["longitude"],
        magnitude=mag,
        maps_url=maps_url,
        recipient=st.session_state.alert_mgr.default_recipient,
    )
    st.session_state.accident_alert_triggered = True

# Record telemetry history for chart
timestamp_str = datetime.now().strftime("%H:%M:%S")
st.session_state.telemetry_history.append({
    "time": timestamp_str,
    "magnitude": mag,
    "threshold": impact_thresh,
    "x": current_telemetry["x"],
    "y": current_telemetry["y"],
    "z": current_telemetry["z"],
    "status": detection_state.value,
})
# Keep last 40 telemetry readings for smooth rendering
if len(st.session_state.telemetry_history) > 40:
    st.session_state.telemetry_history.pop(0)

# Display Prominent State Banner
if detection_state == DetectionState.ACCIDENT_DETECTED:
    st.error(
        f"🚨 **ACCIDENT DETECTED!** High-G impact recorded: **{mag:.2f} m/s² ({mag_g:.2f} g)**! "
        f"Simulated emergency SMS dispatched to {st.session_state.alert_mgr.default_recipient}. "
        f"[Open Google Maps Pin]({maps_url}) | Click **'Stop Monitoring'** or **'Cancel Alert'** if false alarm."
    )
elif detection_state == DetectionState.WARNING:
    st.warning(
        f"⚠️ **WARNING:** Abnormal vehicle motion detected (**{mag:.2f} m/s²**). Analyzing consecutive readings to filter road bumps..."
    )
elif detection_state == DetectionState.CANCELLED:
    st.info("🛡️ **ALERT CANCELLED:** Emergency sequence overridden by driver/operator.")
else:
    st.success("✅ **SYSTEM NORMAL:** Vehicle acceleration and orientation within safe parameters.")

# Top Metrics Row
m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
with m_col1:
    st.metric("Total Magnitude", f"{mag:.2f} m/s²", delta=f"{mag_g:.2f} g")
with m_col2:
    st.metric("X-Axis (Lateral)", f"{current_telemetry['x']:.2f} m/s²")
with m_col3:
    st.metric("Y-Axis (Longitudinal)", f"{current_telemetry['y']:.2f} m/s²")
with m_col4:
    st.metric("Z-Axis (Vertical)", f"{current_telemetry['z']:.2f} m/s²")
with m_col5:
    badge_html = f'<div class="status-{detection_state.value.lower()}">{detection_state.value}</div>'
    st.markdown("**Vehicle Status**")
    st.markdown(badge_html, unsafe_allow_html=True)

# Main Section: Charts and GPS Location
st.markdown("### Real-time Dynamics & Location")
graph_col, map_col = st.columns([3, 2])

with graph_col:
    st.subheader("Acceleration Magnitude vs Threshold")
    if st.session_state.telemetry_history:
        chart_df = pd.DataFrame(st.session_state.telemetry_history)
        st.line_chart(
            chart_df.set_index("time")[["magnitude", "threshold"]],
            color=["#EF4444", "#3B82F6"],
            use_container_width=True,
        )
    st.caption("🔴 Red: Acceleration Magnitude (m/s²) | 🔵 Blue: Impact Detection Threshold (m/s²)")

with map_col:
    st.subheader("Vehicle GPS Position")
    st.markdown(f"**Latitude:** `{current_telemetry['latitude']:.6f}`")
    st.markdown(f"**Longitude:** `{current_telemetry['longitude']:.6f}`")
    st.markdown(f"**Google Maps Link:** [📍 View on Google Maps]({maps_url})")

    # Render Streamlit built-in map
    map_data = pd.DataFrame({
        "lat": [current_telemetry["latitude"]],
        "lon": [current_telemetry["longitude"]],
    })
    st.map(map_data, zoom=14, use_container_width=True)

# Emergency Dispatch & Alert History Section
st.markdown("---")
st.subheader("📋 Emergency Alert History & Dispatched SMS Log")

history_records = st.session_state.alert_mgr.get_history_as_dicts()
if history_records:
    history_df = pd.DataFrame(history_records)
    st.dataframe(history_df, use_container_width=True)

    # Show raw SMS preview for the latest alert
    latest_alert = st.session_state.alert_mgr.alert_history[0]
    with st.expander("💬 View Simulated SMS Payload (Sent to Emergency Services / Family)"):
        st.code(
            f"RECIPIENT: {latest_alert.recipient_phone}\n"
            f"TIMESTAMP: {latest_alert.timestamp}\n"
            f"STATUS: {latest_alert.cancellation_status}\n\n"
            f"MESSAGE:\n{latest_alert.message_content}",
            language="markdown",
        )
else:
    st.info("No accident alerts triggered yet. Click '💥 Simulate Accident' to test the emergency alert sequence.")

# System Diagnostics / Live JSON Stream inspection
with st.expander("🔍 Telemetry Data Inspection (ESP32 Serial JSON Line Format)"):
    json_preview = SensorDataParser.to_json_line(
        current_telemetry["x"],
        current_telemetry["y"],
        current_telemetry["z"],
        current_telemetry["latitude"],
        current_telemetry["longitude"],
        detection_state.value,
    )
    st.code(json_preview, language="json")
    st.caption("This exact JSON format is transmitted by ESP32 firmware over USB Serial @ 115200 baud.")

# Auto-refresh loop when monitoring is active
if st.session_state.is_monitoring:
    time.sleep(0.8)
    st.rerun()
