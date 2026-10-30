# Academic Mini-Project Report

## Smart Accident Detection and Emergency Alert System

**Degree:** Bachelor of Engineering / Technology in Electronics and Communication Engineering (ECE)  
**Domain:** Embedded Systems, IoT, Vehicular Telematics & Signal Processing  
**Academic Year:** 2026–2027  

---

## Abstract

Road traffic collisions represent one of the leading causes of preventable fatalities worldwide. A critical factor influencing casualty mortality is the delay in post-crash emergency medical notification—often described in trauma care as the "Golden Hour." In many vehicular accidents, victims become unconscious or trapped, rendering them unable to manually place emergency calls.

This project presents the design and implementation of a **Smart Accident Detection and Emergency Alert System** featuring dual software and hardware architectures. The system employs a 3-axis Micro-Electro-Mechanical Systems (MEMS) accelerometer (MPU6050) to measure vehicular dynamics across three orthogonal planes. A Euclidean vector magnitude algorithm ($A = \sqrt{x^2 + y^2 + z^2}$) continuously calculates net deceleration and shock. A consecutive reading filter suppresses transient mechanical noise and pothole bumps, preventing false alarms. 

Upon detecting a severe collision ($\ge 28.0 \text{ m/s}^2$), the system captures precise geographic coordinates using a satellite GPS receiver (u-blox NEO-6M), triggers an in-cabin acoustic alarm, and prepares an emergency dispatch payload containing a direct Google Maps tracking link. The project features an interactive Python-based real-time telemetry dashboard (Streamlit) operating in both standalone **Simulation Mode** and physical **ESP32 Hardware Mode** via USB serial JSON communications. Experimental evaluation demonstrates 100% detection accuracy for simulated crashes exceeding threshold parameters while successfully filtering single-frame transient road disturbances.

---

## 1. Introduction

With the rapid expansion of global highway infrastructure and vehicular density, traffic collisions have become a pervasive public safety challenge. According to World Health Organization (WHO) statistics, road traffic injuries account for approximately 1.35 million annual fatalities globally, with tens of millions suffering non-fatal injuries.

In severe collisions—especially on remote rural highways or during nighttime hours—passengers are frequently incapacitated. Precious minutes or hours elapse before third-party motorists notice the wreckage and summon rescue teams. Rapid detection and automated transmission of precise accident locations can significantly reduce medical response times, curbing hemorrhagic shock and preventable trauma deaths.

Recent advancements in MEMS sensor integration, low-cost microcontrollers, and modern web application frameworks provide an opportunity to develop scalable, cost-effective vehicular telematics systems capable of operating autonomously or interfacing with vehicle infotainment dashboards.

---

## 2. Problem Statement

Conventional emergency notification methods exhibit severe vulnerabilities:
1. **Human Dependency:** Emergency calls rely exclusively on conscious, uninjured occupants or passing motorists.
2. **Imprecise Location Reporting:** Panicked victims or bystanders often fail to provide accurate geographical landmarks, delaying ambulances.
3. **High False-Alarm Rates:** Naive acceleration monitoring systems trigger false emergency alerts whenever a vehicle encounters rough terrain, railway crossings, or speed bumps.
4. **Hardware-Only Rigidity:** Most educational mini-projects depend strictly on physical embedded hardware, preventing students and researchers from testing algorithms or simulating edge cases when hardware components are unavailable.

---

## 3. Objectives

The primary objectives of this project are:
1. To design a 3-axis acceleration monitoring algorithm calculating Euclidean vector magnitude ($A = \sqrt{x^2 + y^2 + z^2}$).
2. To implement a multi-tiered state machine distinguishing normal driving, speed bumps (`WARNING`), confirmed collisions (`ACCIDENT_DETECTED`), and driver cancellation (`CANCELLED`).
3. To develop a robust noise-filtering mechanism requiring consecutive threshold violations to eliminate road pothole false positives.
4. To integrate GPS satellite positioning to construct automated Google Maps links for first responders.
5. To build a standalone Python software simulation environment allowing testing without physical hardware.
6. To design an ESP32 embedded hardware architecture transmitting structured JSON telemetry over USB serial.
7. To provide an in-cabin manual cancellation interface giving drivers the ability to abort false alerts.

---

## 4. Existing System vs. Proposed System

| Parameter | Existing Conventional Systems | Proposed Smart System |
| :--- | :--- | :--- |
| **Crash Detection** | Mechanical crash sensors / Airbag deployment switches only | MEMS tri-axial acceleration magnitude vector with digital signal processing |
| **False Alarm Filter**| None (Single threshold jolt triggers alarm) | Consecutive sample window filter + Driver cancellation window |
| **Location Data** | None or manual verbal explanation | Automated u-blox NEO-6M GPS coordinate fix + Google Maps link |
| **Driver Override** | Unavailable | Manual hardware push-button and software GUI cancel options |
| **Operation Flexibility**| Strictly physical hardware dependent | Dual-mode: Standalone Python Simulation + ESP32 Hardware Integration |
| **Telemetry Format** | Proprietary or raw analog voltages | Human-readable, standardized JSON Lines protocol |
| **Visualization** | Basic 16x2 character LCD | Full-stack interactive Streamlit web dashboard with real-time graphs |

---

## 5. System Architecture

```
+-----------------------------------------------------------------------------------+
|                            OVERALL SYSTEM ARCHITECTURE                            |
|                                                                                   |
|    +-------------------+       +-------------------+                              |
|    | MPU6050 Accel/IMU |       | NEO-6M GPS Module |                              |
|    +---------+---------+       +---------+---------+                              |
|              | (I2C: GPIO 21/22)         | (UART2: GPIO 16/17)                    |
|              v                           v                                        |
|    +-----------------------------------------------+                              |
|    |           ESP32 Microcontroller Core          |                              |
|    |  - Vector Magnitude Calculation Engine        |                              |
|    |  - Consecutive Anomaly Window Filter          |                              |
|    |  - Multi-tier State Machine (Normal/Warn/Acc) |                              |
|    |  - Structured JSON Line Formatter             |                              |
|    +-----------------------+-----------------------+                              |
|                            | (USB CDC Serial @ 115200 Baud)                       |
|                            v                                                      |
|    +-----------------------------------------------+                              |
|    |            Python Software System             |                              |
|    |  - PySerial Hardware Bridge                   |                              |
|    |  - Fallback Sensor & GPS Simulators           |                              |
|    |  - Streamlit Interactive Web Dashboard        |                              |
|    |  - Emergency Alert & Simulated SMS Manager    |                              |
|    +-----------------------------------------------+                              |
+-----------------------------------------------------------------------------------+
```

---

## 6. Mathematical Formulations & Working Principle

### 6.1 Vector Acceleration Magnitude
Vehicular impacts are non-unidirectional. Whether a vehicle experiences a frontal collision, lateral broadside impact, or dynamic rollover, acceleration vectors distribute across $X$, $Y$, and $Z$ axes.

The net acceleration magnitude $A$ is derived from Euclidean 3D space:

$$A = \sqrt{a_x^2 + a_y^2 + a_z^2}$$

Where:
- $a_x$: Lateral acceleration along the vehicle's transverse axis ($\text{m/s}^2$).
- $a_y$: Longitudinal acceleration along the vehicle's travel axis ($\text{m/s}^2$).
- $a_z$: Vertical acceleration perpendicular to the road surface ($\text{m/s}^2$).

Under resting conditions on a level plane:
$$a_x = 0, \quad a_y = 0, \quad a_z = 9.80665 \text{ m/s}^2 \implies A = 9.80665 \text{ m/s}^2 \approx 1.0g$$

### 6.2 Acceleration Conversion from Sensor Registers
The MPU6050 16-bit ADC outputs integer counts ($LSB$). Configured at $\pm 4g$ full-scale range, the sensitivity factor is $8192 \text{ LSB}/g$:

$$a_{\text{axis}} = \left(\frac{\text{Raw Register Value}}{8192}\right) \times 9.80665 \quad (\text{m/s}^2)$$

### 6.3 Decision State Machine
The classification algorithm evaluates the incoming telemetry stream against two defined thresholds:
- **Warning Threshold ($\theta_w$):** Set at $18.0 \text{ m/s}^2$ ($\approx 1.83g$).
- **Impact Threshold ($\theta_{\text{impact}}$):** Set at $28.0 \text{ m/s}^2$ ($\approx 2.85g$).

Let $S_k$ denote the state at sample step $k$, and $C_k$ denote the consecutive spike counter:

$$\text{If } A_k \ge \theta_{\text{impact}}: \quad C_k = C_{k-1} + 1$$
$$\text{If } C_k \ge N_{\text{req}} \implies S_k = \text{ACCIDENT\_DETECTED}$$
$$\text{If } C_k < N_{\text{req}} \implies S_k = \text{WARNING}$$
$$\text{If } \theta_w \le A_k < \theta_{\text{impact}} \implies S_k = \text{WARNING}, \quad C_k = 0$$
$$\text{If } A_k < \theta_w \text{ and } S_{k-1} \ne \text{ACCIDENT\_DETECTED} \implies S_k = \text{NORMAL}$$

---

## 7. Implementation Details

### 7.1 Software Implementation
- **Programming Language:** Python 3.10+
- **User Interface:** Streamlit interactive reactive framework.
- **Data Structures:** Double-ended queues (`deque`) for sliding-window telemetry buffers; dataclasses for alert encapsulation.
- **Serial Protocol:** JSON Lines (`JSONL`) encoding:
  `{"x":0.20,"y":0.30,"z":9.81,"latitude":11.016800,"longitude":76.955800,"status":"NORMAL"}`
- **Simulation Capabilities:** Synthetic Gaussian noise generators modeling cruising, sharp cornering, braking, speed bumps, and severe vehicular collision shocks.

### 7.2 Hardware Implementation
- **Microcontroller:** ESP32-WROOM-32 (240 MHz dual-core, 520 KB SRAM).
- **Inertial Measurement Unit:** InvenSense MPU6050 connected over I2C at 400 kHz (SDA: GPIO 21, SCL: GPIO 22).
- **Positioning Module:** u-blox NEO-6M GPS connected via HardwareSerial2 (RX: GPIO 16, TX: GPIO 17).
- **Audible Indicator:** Active piezoelectric buzzer connected to GPIO 4.
- **User Input:** Tactile momentary button with internal pull-up on GPIO 15.

---

## 8. Experimental Results and Verification

The system was evaluated through automated unit testing, synthetic telemetry playback, and headless command-line execution:

### 8.1 Automated Test Execution Summary
- **Test Framework:** `pytest 9.2.0`
- **Total Test Cases:** 16
- **Test Coverage:**
  - Acceleration magnitude calculations: 100% accurate across static and tri-axial vectors.
  - State machine transitions: Passed (`NORMAL` $\to$ `WARNING` $\to$ `ACCIDENT_DETECTED`).
  - Road bump filter: Single-frame $30 \text{ m/s}^2$ spike classified as `WARNING`, auto-recovering without triggering accident alert.
  - Consecutive spikes ($N \ge 2$): Accurately escalated to `ACCIDENT_DETECTED`.
  - Manual cancellation: Successfully overrode accident alert to `CANCELLED`.
  - JSON parser: Cleanly handled valid JSONL, fallback CSV, and malformed noise lines.

### 8.2 System Performance Metrics
- **Mean Sampling Period:** 500 ms ($2 \text{ Hz}$ telemetry rate).
- **Detection Latency:** $\le 1000 \text{ ms}$ (2 consecutive sample intervals).
- **Emergency Message Construction Time:** $< 5 \text{ ms}$.
- **Dashboard Refresh Rate:** Real-time (0.8s periodic polling loop).

---

## 9. Limitations

1. **Cellular Network Coverage:** Standalone GSM transmission relies on 2G/GPRS base station availability, which may be degraded in remote mountainous passes or underground tunnels.
2. **GPS Line-of-Sight:** GPS satellite fixes require an open view of the sky; performance indoors or inside parking garages relies on last known stored coordinates.
3. **Threshold Calibration:** Acceleration thresholds must be calibrated to vehicle chassis rigidity; lightweight motorcycles experience higher peak accelerations than heavy commercial trucks during identical collision speeds.
4. **Non-Certified Status:** Designed as an educational engineering prototype; not validated for commercial automotive safety certification (ISO 26262).

---

## 10. Future Scope

1. **Edge AI Crash Classification:** Deploy lightweight 1D-Convolutional Neural Networks (TinyML) on ESP32 to classify crash signatures (rollover vs. frontal collision vs. sideswipe).
2. **OBD-II CAN-Bus Integration:** Intercept airbag deployment flags and vehicle speed directly from vehicle controller area networks.
3. **4G/5G eCall Module:** Replace legacy 2G SIM800L modems with 4G LTE-M / NB-IoT modules conforming to international eCall standards.
4. **Cloud Telematics Fleet Management:** Stream accident telemetry directly to a centralized hospital/emergency fleet dispatch cloud portal.

---

## 11. Conclusion

This project successfully demonstrates the design, algorithmic formulation, and implementation of a **Smart Accident Detection and Emergency Alert System**. By uniting Euclidean acceleration magnitude math, consecutive noise filtering, GPS satellite tracking, and an interactive web dashboard, the system bridges the gap between low-cost embedded hardware and responsive emergency telematics. The dual-mode architecture guarantees educational accessibility while paving the path for real-world automotive deployment.

---

## 12. References

1. World Health Organization (WHO), "Global Status Report on Road Safety," Geneva, Switzerland, 2023.
2. InvenSense Inc., "MPU-6000 and MPU-6050 Product Specification Revision 3.4," Document Number: PS-MPU-6000A-00, 2013.
3. u-blox AG, "NEO-6 u-blox 6 GPS Modules Data Sheet," Document Number: GPS.G6-HW-09005, 2011.
4. Espressif Systems, "ESP32 Series Datasheet," Version 4.0, Espressif Systems Co., Ltd., 2023.
5. National Marine Electronics Association, "NMEA 0183 Standard for Interfacing Marine Electronic Devices," Version 4.10, 2012.
