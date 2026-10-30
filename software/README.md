# Software Implementation - Smart Accident Detection System

This directory houses the complete Python software suite for the **Smart Accident Detection and Emergency Alert System**.

> [!TIP]
> The software is **100% standalone**. You can run the full real-time dashboard, simulate vehicular driving, trigger collisions, test false-alarm filtering, and inspect emergency SMS dispatches without connecting physical hardware.

---

## 1. Software Architecture & Directory Layout

```
software/
├── README.md               # Detailed software documentation
├── requirements.txt        # Python dependency manifest
├── main.py                 # Multi-mode launcher (Dashboard & Headless CLI)
├── core/                   # Core algorithmic engine
│   ├── accident_detection.py # Magnitude calculations, thresholding & filtering
│   ├── sensor_simulator.py   # Synthesizes 3-axis motion & collision shocks
│   ├── gps_simulator.py      # Generates coordinate drift & Google Maps links
│   └── alert_manager.py      # Logs alerts, simulated SMS & GSM AT commands
├── hardware_interface/     # Physical hardware bridge
│   ├── serial_communication.py # USB COM port management & PySerial driver
│   └── sensor_data_parser.py   # Validates & normalizes ESP32 JSON lines
├── dashboard/              # Streamlit interactive web interface
│   └── app.py              # Real-time charts, metrics & control UI
├── data/                   # Sample sensor telemetry
│   └── sample_sensor_data.csv
└── tests/                  # Automated pytest verification suite
    └── test_accident_detection.py
```

---

## 2. Key Features

- **Vector Acceleration Math:** Continuously evaluates Euclidean acceleration magnitude:
  $$A = \sqrt{x^2 + y^2 + z^2}$$
- **Multi-Tier State Machine:** Classifies motion into `NORMAL`, `WARNING` (speed bumps, sudden braking), `ACCIDENT_DETECTED` (violent collisions $\ge 28 \text{ m/s}^2$), and `CANCELLED`.
- **False Alarm Rejection:** Enforces consecutive anomaly filtering to eliminate transient sensor noise and single pothole jolts.
- **Manual Alert Cancellation:** Provides drivers with a cancellation mechanism to abort false alerts.
- **Dual Operating Modes:**
  - **Simulation Mode (Default):** Runs realistic dynamic vehicle simulations with zero hardware.
  - **Hardware Mode (ESP32):** Reads live JSON telemetry from an ESP32 connected via USB.
- **GPS Mapping:** Real-time latitude/longitude tracking with direct Google Maps coordinate generation.
- **Simulated Emergency Dispatch:** Logs timestamped emergency alerts formatted for family/emergency services.

---

## 3. Installation & Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.10, 3.11, 3.12, 3.13, and 3.14).

### Step 1: Open Terminal in Project Root
Navigate to the project root directory:
```bash
cd "d:/akshaya/1st project"
```

### Step 2: Install Dependencies
Install all required libraries using `pip`:
```bash
pip install -r software/requirements.txt
```

---

## 4. How to Run the Software

### Option A: Launch Interactive Streamlit Dashboard (Recommended)
You can start the web interface either via `main.py` or directly with `streamlit`:

```bash
# Method 1: Using main.py launcher
python software/main.py

# Method 2: Direct Streamlit execution
streamlit run software/dashboard/app.py
```
The dashboard will open automatically in your web browser at:
`http://localhost:8501`

### Option B: Run Headless CLI Simulation
For terminal-only or low-resource testing:
```bash
python software/main.py --cli --duration 25
```
This runs a 25-second continuous terminal loop with a simulated collision triggered at $t = 8\text{s}$.

---

## 5. Using the Dashboard

1. **Start / Stop Monitoring:** Toggle real-time telemetry processing using the controls in the top bar.
2. **Simulate Collision:** Click **"💥 Simulate Accident"** to inject a violent shock into the simulator. Observe the status transition from `NORMAL` $\to$ `WARNING` $\to$ `ACCIDENT DETECTED`.
3. **Cancel False Alarm:** Click **"🛑 Cancel Alert"** to override the emergency sequence.
4. **Adjust Sensitivity:** Use the sidebar sliders to customize the **Impact Threshold** (default: $28 \text{ m/s}^2$) and **Consecutive Reading Filter** count.
5. **Custom GPS:** Enter custom coordinates in the sidebar to simulate location tracking anywhere in the world.

---

## 6. Switching to Hardware Mode (ESP32)

1. Connect your flashed ESP32 to your PC using a micro-USB cable.
2. In the dashboard sidebar, select **"Hardware Mode (ESP32)"**.
3. Select the detected COM port (e.g. `COM3` on Windows or `/dev/ttyUSB0` on Linux) and click **"Connect ESP32"**.
4. Telemetry from the physical MPU6050 and NEO-6M sensors will now stream live into the dashboard!

---

## 7. Running the Test Suite

Execute the unit test suite with `pytest`:
```bash
python -m pytest software/tests/test_accident_detection.py -v
```

All 16 unit tests verify magnitude calculations, state transitions, false alarm rejection, JSON parser resilience, and alert dispatch.

---

## 8. Serial Telemetry Protocol Specification

The software parser expects standard JSON lines formatted as follows:

```json
{"x":0.20,"y":0.30,"z":9.81,"latitude":11.016800,"longitude":76.955800,"status":"NORMAL"}
```

- If an incomplete or garbled string is received, the parser discards the corrupted frame safely without interrupting dashboard execution.
