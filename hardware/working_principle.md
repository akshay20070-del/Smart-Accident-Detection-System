# Hardware Working Principle

This document explains the physical and computational working principles of the **Smart Accident Detection and Emergency Alert System**.

---

## 1. MEMS Accelerometer Sensing Principle (MPU6050)

The MPU6050 utilizes **Micro-Electro-Mechanical Systems (MEMS)** technology:

```
          [ Fixed Electrode ]   (Capacitance C1)
       ===|==================|===
       ---[ Proof Mass / Springs ]---   <--- Moves when vehicle accelerates
       ===|==================|===
          [ Fixed Electrode ]   (Capacitance C2)
```

1. **Proof Mass Displacement:** Inside the sensor die, microscopic silicon proof masses are suspended on silicon springs along three orthogonal axes ($X$, $Y$, $Z$).
2. **Newton's Second Law ($F = ma$):** When the vehicle accelerates, brakes, or collides, inertia causes displacement of the proof mass relative to stationary capacitive plates.
3. **Differential Capacitance:** The mechanical displacement causes a differential capacitance change ($\Delta C = C_1 - C_2$), which is converted into an analog voltage.
4. **On-Chip ADC & Scaling:** An internal 16-bit Analog-to-Digital Converter (ADC) digitizes the voltage into signed integer LSBs:
   $$a_x = \frac{\text{raw}_x}{\text{Sensitivity Scale Factor}} \times 9.80665 \quad (\text{m/s}^2)$$
   At the $\pm 4g$ range configuration, the sensitivity is $8192 \text{ LSB}/g$.

---

## 2. 3-Axis Acceleration Magnitude Math

Vehicular collisions occur at unpredictable angles (head-on collision, broadside T-bone, rear-end impact, or vehicle rollover). Monitoring only one single axis can fail to detect diagonal or lateral impacts.

To achieve orientation-independent impact detection, the system continuously calculates the **Euclidean vector magnitude**:

$$A_{\text{total}} = \sqrt{a_x^2 + a_y^2 + a_z^2}$$

### Benchmark Physical Values:
- **Stationary Vehicle (Earth Gravity):**
  $$a_x \approx 0, \quad a_y \approx 0, \quad a_z \approx 9.81 \text{ m/s}^2 \implies A_{\text{total}} \approx 9.81 \text{ m/s}^2 \quad (\approx 1.0g)$$
- **Gentle Cruising & Smooth Highway Driving:**
  $$A_{\text{total}} \in [9.2 \text{ m/s}^2, 11.5 \text{ m/s}^2]$$
- **Speed Bumps / Road Potholes:**
  $$A_{\text{total}} \in [13.0 \text{ m/s}^2, 19.0 \text{ m/s}^2] \implies \text{Triggers WARNING state}$$
- **Severe Vehicular Crash (Deformation & Rapid Deceleration):**
  $$A_{\text{total}} \ge 28.0 \text{ m/s}^2 \quad (\ge 2.85g) \implies \text{Triggers ACCIDENT state}$$

---

## 3. False Alarm Filtering Algorithm

Single transient anomalies (such as dropping a phone on the dashboard or driving over an abrupt speed bump) can cause brief momentary spikes. To avoid nuisance emergency alerts:

1. **Consecutive Spike Filter:**
   - An impact reading must exceed $28.0 \text{ m/s}^2$ across **two consecutive sample frames** ($N \ge 2$) before transitioning into `ACCIDENT_DETECTED`.
   - A single isolated spike temporarily moves the system to `WARNING` and auto-resets if subsequent readings return to normal.
2. **Driver Cancellation Window:**
   - Upon entering the accident sequence, an in-cabin active buzzer sounds loudly.
   - The driver or passenger has a physical **Cancel Button** (GPIO 15) to abort the alert if they are unharmed or if the detection was a false alarm.

---

## 4. GPS Trilateration & Coordinate Acquisition

The **NEO-6M GPS Module** receives radio frequency signals from orbiting GPS satellites at 1575.42 MHz (L1 band):

1. **Time of Flight (ToF):** The GPS receiver measures the exact time taken by atomic clock signals to travel from at least 4 satellites to the vehicle antenna.
2. **Trilateration:** The intersection of spheres calculated from each satellite range pinpoints the vehicle's exact 3D position:
   $$\text{Distance}_i = c \times (t_{\text{received}} - t_{\text{transmitted}})$$
3. **NMEA 0183 Framing:** The module formats the position into standardized NMEA sentences sent over UART serial @ 9600 baud:
   `$GPGGA,100000.00,1101.0080,N,07657.3480,E,1,08,1.0,410.2,M...*42`
4. **Coordinate Extraction:** The firmware parses latitude ($11.016800^\circ\text{N}$) and longitude ($76.955800^\circ\text{E}$) and constructs the Google Maps tracking URL.

---

## 5. Serial Telemetry Stream & Python Handshake

The ESP32 processes sensor data every 500 ms and packages the output into a structured **JSON line**:

```json
{"x": 0.20, "y": 0.30, "z": 9.81, "latitude": 11.016800, "longitude": 76.955800, "status": "NORMAL"}
```

- **Transport:** Standard USB-to-UART bridge (CP2102 or CH340 on ESP32 development board) @ 115200 baud.
- **Defensive Parsing:** The Python software validates every line. If a line is corrupted, the parser discards the frame without crashing the dashboard.
