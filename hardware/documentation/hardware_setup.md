# Complete Hardware Setup & Flashing Guide

This guide walks you through assembling the hardware prototype, configuring the Arduino IDE, uploading firmware to the ESP32, and interfacing with the Python dashboard.

---

## 1. Arduino IDE Setup for ESP32

### Step 1: Install Arduino IDE
Download and install **Arduino IDE 2.x** from the official Arduino website.

### Step 2: Add ESP32 Board URL
1. Open Arduino IDE and navigate to **File > Preferences**.
2. Locate the field **Additional Boards Manager URLs** and enter:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Click **OK**.

### Step 3: Install ESP32 Board Package
1. Open **Tools > Board > Boards Manager...**
2. Search for `ESP32` by **Espressif Systems** and click **Install**.

### Step 4: Install Required Arduino Libraries
Open **Tools > Manage Libraries...** and install:
- `Adafruit MPU6050`
- `Adafruit Unified Sensor`
- `Adafruit BusIO`
- `TinyGPSPlus` (by Mikal Hart)

---

## 2. Hardware Wiring Step-by-Step

Assemble the components on a standard solderless breadboard according to this wiring map:

### 1. MPU6050 Accelerometer
- `VCC` -> ESP32 `3.3V`
- `GND` -> ESP32 `GND`
- `SCL` -> ESP32 `GPIO 22`
- `SDA` -> ESP32 `GPIO 21`
- `AD0` -> ESP32 `GND`

### 2. NEO-6M GPS Module
- `VCC` -> ESP32 `3.3V` (or `VIN` if using a 5V-only NEO-6M board)
- `GND` -> ESP32 `GND`
- `TX`  -> ESP32 `GPIO 16` (RX2)
- `RX`  -> ESP32 `GPIO 17` (TX2)

### 3. Active Buzzer & Cancel Button
- **Buzzer (+)** -> ESP32 `GPIO 4`
- **Buzzer (-)** -> ESP32 `GND`
- **Button Terminal 1** -> ESP32 `GPIO 15`
- **Button Terminal 2** -> ESP32 `GND`

### 4. Optional SIM800L GSM Module (If Used)
- `VCC` -> External 4.0V (from LM2596 buck converter or 18650 Li-ion battery)
- `GND` -> External GND **AND** connected to ESP32 `GND`
- `TXD` -> ESP32 `GPIO 26`
- `RXD` -> ESP32 `GPIO 27`

---

## 3. Code Upload Instructions

1. Connect the ESP32 to your PC using a micro-USB data cable.
2. Open the file `hardware/esp32/accident_detection_esp32.ino` in Arduino IDE.
3. In **Tools > Board**, select:
   `ESP32 Dev Module` (or `NodeMCU-32S`).
4. In **Tools > Port**, select the recognized COM port (e.g. `COM3` on Windows or `/dev/ttyUSB0` on Linux).
5. In **Tools > Upload Speed**, select `921600` (or `115200` if upload fails).
6. Click the **Upload** button (Right Arrow).
7. If the IDE displays `Connecting........_____.....`, press and hold the **BOOT** button on the ESP32 until the flashing progress bar begins.

---

## 4. Verification in Serial Monitor

1. Open **Tools > Serial Monitor**.
2. Set the baud rate in the bottom-right corner to **115200 baud**.
3. You should see boot messages followed by continuous JSON telemetry:
   ```json
   {"x":0.15,"y":-0.08,"z":9.81,"latitude":11.016800,"longitude":76.955800,"status":"NORMAL"}
   ```
4. Gently tilt or shake the breadboard; verify that the acceleration values respond.
5. Close the Serial Monitor before launching the Python software (only one application can access the COM port at a time).

---

## 5. Troubleshooting Common Hardware Issues

| Issue | Probable Cause | Corrective Action |
| :--- | :--- | :--- |
| **MPU6050 Not Detected (Error 2 or 4)** | Loose I2C wires or incorrect address | Check SDA/SCL connections on GPIO 21 & 22; tie AD0 to GND. |
| **GPS Fix Not Acquired (Coordinates Stay Default)** | Testing indoors without satellite sight | Move antenna near a window or outdoors. Wait 2–5 minutes for satellite lock. |
| **Brownout Detector Triggered / ESP32 Keeps Resetting** | SIM800L or peripherals drawing excessive current from 3.3V | Disconnect SIM800L from ESP32 pins. Use external LM2596 power supply with common ground. |
| **Access Denied on COM Port in Python** | Arduino Serial Monitor is still open | Close Arduino Serial Monitor before clicking "Connect ESP32" in Python dashboard. |
| **No COM Port Detected on PC** | Missing CP2102 or CH340 USB-UART driver | Download and install the CP210x or CH340 driver for your ESP32 board. |
