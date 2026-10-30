# Hardware Components List & Specifications

This document outlines all physical components required to construct the **Smart Accident Detection and Emergency Alert System**.

> [!IMPORTANT]
> The software simulation is fully standalone and **does not require physical hardware to run**. The hardware implementation described below is designed for physical fabrication, laboratory demonstration, and future embedded integration.

---

## 1. Components Summary Table

| Category | Component Name | Model / Specification | Quantity | Role / Function | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Microcontroller** | ESP32 Development Board | ESP32-WROOM-32 / NodeMCU-32S (30 or 38 pin) | 1 | Central Processing Unit, sensor reading, telemetry output | **Required** |
| **Motion Sensor** | MPU6050 Accelerometer & Gyro | 6-DOF IMU, I2C Interface, ±2g/±4g/±8g/±16g | 1 | Measures 3-axis vehicular acceleration and tilt | **Required** |
| **Location Tracking** | GPS Module | u-blox NEO-6M with ceramic patch antenna | 1 | Acquires Latitude and Longitude coordinates | **Required** |
| **Acoustic Indicator** | Active Buzzer | 5V / 3.3V Active Piezo Buzzer | 1 | Immediate in-cabin audible accident alert | **Required** |
| **User Control** | Tactile Push Button | 6x6mm momentary tactile button | 1 | Manual alert cancellation by driver | **Required** |
| **Visual Indicator** | LED (Red / Green) | 5mm Diffused LED with 220Ω resistor | 1 | Visual indicator for system status & warnings | **Required** |
| **Cellular SMS** | GSM / GPRS Module | SIM800L Quad-band Micro-SIM module | 1 | Standalone cellular SMS dispatch (SMS alert to phone) | **Optional** |
| **Power Converter** | DC-DC Step-Down Buck | LM2596 Buck Converter (Adjustable 1.25V–35V) | 1 | Dedicated high-current regulated power for SIM800L | **Optional (Required if GSM used)** |
| **Power Source** | External Power Supply | 18650 Li-ion battery (3.7V 2500mAh) or 12V 2A DC Adapter | 1 | Powers ESP32 and cellular module | **Required for standalone vehicle use** |
| **Interconnects** | Breadboard & Jumper Wires | MB-102 Breadboard, Male-to-Male & Male-to-Female | 1 set | Circuit prototype interconnection | **Required** |
| **PC Interface** | Micro-USB Cable | High-speed data sync cable (not power-only) | 1 | Programming ESP32 & sending JSON telemetry to Python | **Required** |

---

## 2. Detailed Technical Specifications

### 2.1 ESP32 Microcontroller
- **Core:** Dual-core Tensilica Xtensa 32-bit LX6 microprocessor @ 240 MHz.
- **Operating Voltage:** 3.3 V (On-board AMS1117-3.3 regulator accepts 5V via Micro-USB or VIN).
- **GPIO Pins:** 34 usable GPIOs with capacitive touch, ADC, DAC, I2C, SPI, UART.
- **Hardware UARTs:** 3 hardware serial ports (UART0 for USB debug, UART1, UART2 for peripherals).
- **Why Chosen:** Exceptional processing speed, dual-core architecture, dual hardware UARTs, and native USB serial debugging.

### 2.2 MPU6050 6-Axis Motion Sensor
- **Sensors:** 3-axis accelerometer and 3-axis gyroscope on a single silicon die.
- **Digital Interface:** I2C (Up to 400 kHz fast mode), default I2C address `0x68` (AD0 grounded).
- **Supply Voltage:** 3.3V to 5V (module features an onboard 3.3V LDO).
- **Acceleration Range:** Configurable: ±2g, ±4g, ±8g, ±16g.
- **Sensitivity:** 8192 LSB/g at ±4g range.
- **Measurement Formula:** Total magnitude $A = \sqrt{a_x^2 + a_y^2 + a_z^2}$.

### 2.3 NEO-6M GPS Module
- **Receiver Type:** 50-channel u-blox 6 positioning engine.
- **Update Rate:** 1 Hz (default) up to 5 Hz.
- **Protocol:** NMEA 0183 (GPGGA, GPRMC sentences).
- **Supply Voltage:** 3.3V to 5V (VCC has built-in low-dropout regulator).
- **Communication:** UART serial @ 9600 baud.
- **Antenna:** High-gain ceramic patch antenna (requires line of sight to open sky / window).

### 2.4 SIM800L GSM Module (Optional Expansion)
- **Cellular Band:** Quad-band 850/900/1800/1900 MHz.
- **Operating Voltage:** **3.7V to 4.2V ONLY** (Typical 4.0V).
- **Peak Current:** **Up to 2.0 Amperes** during network burst transmissions.
- **SIM Card Slot:** Micro-SIM with 2G/GPRS cellular network support.
- **Logic Level:** 2.8V to 3.3V UART (compatible with ESP32 with voltage protection).

---

## 3. Power Supply Precautions & Critical Guidelines

> [!CAUTION]
> **NEVER POWER THE SIM800L FROM THE ESP32 3.3V PIN!**
> The ESP32 on-board voltage regulator (AMS1117) provides a maximum of 500mA–800mA. The SIM800L draws peak surge currents of **2.0A** when searching for cellular towers or transmitting an SMS. Connecting SIM800L to the ESP32 3.3V pin will cause immediate brownout resets, permanent reboot loops, or destruction of the ESP32 regulator.

### Correct Power Setup:
1. When using **Simulation or Sensor-Only Testing**:
   - Power ESP32, MPU6050, GPS, and Buzzer directly through the PC USB port.
2. When using **Physical SIM800L GSM Module**:
   - Use an external **LM2596 DC-DC Buck Converter** tuned to output **4.0V DC**, or a high-drain **18650 3.7V Li-ion battery**.
   - Add a **1000 µF 16V electrolytic capacitor** across the SIM800L `VCC` and `GND` pins to absorb burst current surges.
   - **Crucial:** Connect the **External Power Supply Ground (GND)** directly to the **ESP32 Ground (GND)** to establish a common electrical reference.
