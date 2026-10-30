# Future Enhancements & Development Roadmap

This document outlines architectural and engineering enhancements planned for subsequent revisions of the **Smart Accident Detection and Emergency Alert System**.

---

## 1. Roadmap Overview

```
Phase 1 (Current Release)   -> Dual Simulation & ESP32 Hardware Integration, JSONL Telemetry
Phase 2 (Edge Intelligence) -> TinyML 1D-CNN Crash Classification on ESP32 Microcontroller
Phase 3 (Automotive Bus)    -> OBD-II CAN-Bus Transceiver for Airbag & Speed Telematics
Phase 4 (Cloud & Vision)    -> 4G/LTE eCall Module, Cloud Telematics Fleet Hub & Dashcam AI
```

---

## 2. Phase 2: Edge AI & TinyML Crash Classification

### Concept:
While threshold-based magnitude math ($A = \sqrt{x^2 + y^2 + z^2}$) is fast and computationally lightweight, complex crash scenarios (such as dynamic rollovers or multiple-vehicle pileups) exhibit unique time-series acceleration signatures.

### Proposed Implementation:
- Train a lightweight **1D Convolutional Neural Network (1D-CNN)** or **Random Forest Classifier** on real-world crash crash-test datasets (e.g., NHTSA vehicle crash databases).
- Quantize the model using **TensorFlow Lite for Microcontrollers (TFLM)** to execute directly on the ESP32 Tensilica dual-core processor.
- Classify impact types into:
  - *Frontal Collision*
  - *Rear-end Impact*
  - *Side-impact T-bone*
  - *Dynamic Rollover*
  - *Harmless Road Irregularity (Speed hump, gravel)*

---

## 3. Phase 3: Automotive CAN-Bus / OBD-II Integration

### Concept:
Modern passenger vehicles contain tens of Electronic Control Units (ECUs) exchanging diagnostic and safety messages across the Controller Area Network (CAN-Bus).

### Proposed Hardware:
- **MCP2515 CAN Controller** + **TJA1050 High-Speed CAN Transceiver** connected to the vehicle's standard **OBD-II 16-pin diagnostic port**.

### Telematics Integration:
- Query real-time vehicle speed (PID `0x0D`) to verify whether sudden acceleration spikes correspond with sudden zero-velocity drop.
- Intercept **Airbag Deployment Control Module (ACM)** state flags.
- Query **Seatbelt Buckle Status** to assess passenger risk severity before emergency medical dispatch.

---

## 4. Phase 4: Next-Generation Cellular Connectivity (4G LTE eCall)

### Concept:
2G GSM networks (utilized by basic SIM800L modules) are facing carrier sunsetting in numerous countries. Upgrading to modern cellular technologies ensures long-term field viability.

### Upgrades:
- Integrate **SIM7600E-H** or **A7670C 4G LTE Cat-1 / NB-IoT** modems with integrated GNSS.
- Implement international **eCall (Regulation EU 2015/758)** compliance: automatically generating Minimum Set of Data (MSD) packets transmitting vehicle VIN, fuel type, timestamps, and passenger headcount to Public Safety Answering Points (PSAPs).

---

## 5. Phase 5: Dashcam Video Snapshot Capture

### Proposed Feature:
- Pair an **ESP32-CAM** or USB camera to capture a 5-second video buffer and high-resolution still image upon collision trigger.
- Automatically upload imagery to cloud storage (AWS S3 / Google Cloud Storage) and include a secure image link in the emergency dispatch SMS to assist trauma teams in triaging damage severity prior to arriving on site.
