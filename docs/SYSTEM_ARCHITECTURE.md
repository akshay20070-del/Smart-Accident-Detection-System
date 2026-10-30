# System Architecture & Technical Specification

This document provides an in-depth architectural breakdown of the **Smart Accident Detection and Emergency Alert System**.

---

## 1. High-Level Architectural Decomposition

The system is architected into three decoupled layers:
1. **Sensor & Acquisition Layer (Hardware / Synthetic Simulation):** Generates 3-axis acceleration and geographic positioning.
2. **Signal Processing & Decision Layer (Embedded Firmware / Python Core):** Computes Euclidean vector magnitudes, filters transient mechanical anomalies, and executes the finite state machine.
3. **Presentation & Telemetry Layer (Streamlit Dashboard & Alert Manager):** Visualizes live telemetry, handles serial handshakes, manages emergency dispatches, and provides driver controls.

```mermaid
graph TD
    subgraph Data_Acquisition ["1. Data Acquisition Layer"]
        A1[MPU6050 Accelerometer]
        A2[NEO-6M GPS Receiver]
        A3[Synthetic Sensor Simulator]
        A4[Synthetic GPS Simulator]
    end

    subgraph Processing_Layer ["2. Signal Processing & State Engine"]
        B1["Euclidean Magnitude Engine: A = sqrt(x² + y² + z²)"]
        B2["Consecutive Reading Filter (N >= 2)"]
        B3["Finite State Machine (Normal, Warning, Accident, Cancelled)"]
    end

    subgraph Presentation_Layer ["3. Presentation & Emergency Dispatch"]
        C1[Streamlit Web Dashboard]
        C2[Real-time Charts & Map View]
        C3[Emergency Alert & Simulated SMS Log]
        C4[GSM AT Commands Engine]
    end

    A1 -->|I2C 400kHz| B1
    A2 -->|UART 9600 Baud| B3
    A3 -->|Python Class| B1
    A4 -->|Python Class| B3

    B1 --> B2
    B2 --> B3

    B3 -->|JSON Telemetry / Internal Object| C1
    C1 --> C2
    C1 --> C3
    C3 -.->|Future Expansion| C4
```

---

## 2. Finite State Machine (FSM)

The system moves across four well-defined states:

```mermaid
stateDiagram-v2
    [*] --> NORMAL: System Power On / Reset

    NORMAL --> WARNING: Acceleration Magnitude >= Warning Threshold (18 m/s²)
    WARNING --> NORMAL: Acceleration drops below Warning Threshold

    WARNING --> ACCIDENT_DETECTED: Consecutive Spikes >= 2 exceeding Impact Threshold (28 m/s²)
    
    ACCIDENT_DETECTED --> CANCELLED: Driver presses Cancel Button / GUI Cancel
    WARNING --> CANCELLED: Driver aborts warning sequence

    CANCELLED --> NORMAL: Operator Clicks Reset System
    ACCIDENT_DETECTED --> NORMAL: Operator Clicks Reset System
```

### State Definitions:
- **`NORMAL`:** Accelerations remain within standard vehicular cruising parameters ($A \approx 9.81 \pm 2.0 \text{ m/s}^2$).
- **`WARNING`:** An abnormal jolt or severe deceleration is detected ($A \ge 18.0 \text{ m/s}^2$). Buzzer remains silent while consecutive readings determine whether it is a harmless speed bump or an active crash.
- **`ACCIDENT_DETECTED`:** High-G collision confirmed across multiple consecutive sample frames ($A \ge 28.0 \text{ m/s}^2$). Buzzer sounds continuously, rapid LED flashing engages, and emergency SMS dispatch payload is broadcast with Google Maps tracking coordinates.
- **`CANCELLED`:** The driver or occupant manually overrides the alert sequence within the cancellation window. Emergency dispatches are aborted.

---

## 3. Telemetry Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Driver
    participant Sensor as MPU6050 / Simulator
    participant GPS as NEO-6M / GPS Sim
    participant MCU as ESP32 / Python Core
    participant UI as Streamlit Dashboard
    participant Alert as Emergency Dispatch

    loop Every 500ms
        Sensor->>MCU: Transmit 3-Axis Accel (X, Y, Z)
        GPS->>MCU: Transmit Coordinates (Lat, Lon)
        MCU->>MCU: Calculate Magnitude A = sqrt(x² + y² + z²)
        MCU->>MCU: Evaluate Consecutive Spike Filter
        MCU->>UI: Stream JSON Telemetry Frame
        UI->>UI: Update Metric Cards & Live Charts
    end

    opt Collision Event
        Sensor->>MCU: Sudden Impact (e.g. 38.5 m/s²)
        Sensor->>MCU: Sustained Impact Deceleration (e.g. 33.2 m/s²)
        MCU->>MCU: Consecutive Spikes >= 2 -> Lock ACCIDENT_DETECTED
        MCU->>UI: Broadcast ACCIDENT Status
        MCU->>Alert: Construct Emergency Alert Payload
        Alert->>Driver: Audible Buzzer / Alert Banner
        Alert->>Alert: Log Dispatched SMS with Google Maps Link
    end

    opt Driver Cancellation
        Driver->>MCU: Press Cancel Button / Dashboard Button
        MCU->>MCU: Transition State -> CANCELLED
        MCU->>Alert: Abort Emergency Dispatch
        MCU->>UI: Display Alert Cancelled Confirmation
    end
```

---

## 4. Failure Modes and Mitigation Strategies

| Potential Failure Mode | Root Cause | Built-in Architectural Mitigation |
| :--- | :--- | :--- |
| **Speed bump / Pothole False Alarm** | Momentary vertical mechanical shock | Consecutive reading filter requires $N \ge 2$ consecutive spikes above $28 \text{ m/s}^2$ before triggering accident state. |
| **I2C Bus Lockup** | Electrical noise on SDA/SCL lines | Defensive read routines catch bus errors and provide safe default values ($a_z = 9.81$) without firmware freeze. |
| **GPS Fix Loss (Tunnels / Indoors)** | Satellite signal attenuation | Software retains and transmits last known valid coordinates with a fix warning flag. |
| **Serial Communication Disconnect** | USB cable unseated during drive | Python manager traps `SerialException`, automatically unmounts port, and warns the user without crashing. |
| **Simulated vs Hardware Ambiguity** | Unclear origin of displayed telemetry | Prominent UI badges clearly identify whether data originates from physical ESP32 or simulation engine. |
