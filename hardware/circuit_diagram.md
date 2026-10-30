# Circuit Diagram & Interconnection Guide

This document describes the complete wiring topology, pin connections, logic-level matching, and schematic layout for connecting physical sensors to the ESP32 microcontroller.

---

## 1. Complete Pin Connection Mapping Table

| Periph / Module | Module Pin | ESP32 Pin | Interface Type | Electrical Notes |
| :--- | :--- | :--- | :--- | :--- |
| **MPU6050** | VCC | 3.3V | Power | Powers IMU regulator (Clean 3.3V) |
| | GND | GND | Ground | Common system ground |
| | SCL | GPIO 22 | I2C Clock | Pull-up internal or on module |
| | SDA | GPIO 21 | I2C Data | Bi-directional I2C bus |
| | AD0 | GND | Address Select | Selects default I2C address `0x68` |
| | INT | Not Connected | Interrupt | Polled via software timer |
| **NEO-6M GPS** | VCC | 3.3V or 5V (VIN)| Power | Module onboard LDO regulates to 3.3V |
| | GND | GND | Ground | Common system ground |
| | TX | GPIO 16 (RX2) | UART RX | ESP32 HardwareSerial 2 RX |
| | RX | GPIO 17 (TX2) | UART TX | Optional for sending NMEA commands |
| **Active Buzzer** | (+) Anode | GPIO 4 | Digital Output | Driven HIGH during accident alert |
| | (-) Cathode | GND | Ground | Common system ground |
| **Push Button** | Terminal 1 | GPIO 15 | Digital Input | Configured with `INPUT_PULLUP` |
| | Terminal 2 | GND | Ground | Pulls GPIO 15 LOW when pressed |
| **Status LED** | Anode (+) | GPIO 2 | Digital Output | In series with 220Ω resistor |
| | Cathode (-) | GND | Ground | Common system ground |
| **SIM800L (Opt)**| VCC | **External 4.0V** | High Current | **DO NOT CONNECT TO ESP32 3.3V!** |
| | GND | **External GND** | Ground | **Must share common ground with ESP32**|
| | SIM_TXD | GPIO 26 (RX1) | UART RX | 3.3V compatible output from GSM |
| | SIM_RXD | GPIO 27 (TX1) | UART TX | 3.3V logic to SIM800L RX |

---

## 2. Mermaid Circuit Topology Diagram

```mermaid
graph TD
    subgraph ESP32_Controller ["ESP32 Development Board"]
        ESP_3V3["3.3V Out"]
        ESP_GND["GND"]
        GPIO_21["GPIO 21 (SDA)"]
        GPIO_22["GPIO 22 (SCL)"]
        GPIO_16["GPIO 16 (RX2)"]
        GPIO_17["GPIO 17 (TX2)"]
        GPIO_4["GPIO 4 (Buzzer)"]
        GPIO_15["GPIO 15 (Cancel Button)"]
        GPIO_2["GPIO 2 (Status LED)"]
    end

    subgraph MPU6050_Sensor ["MPU6050 6-DOF IMU"]
        MPU_VCC["VCC"]
        MPU_GND["GND"]
        MPU_SDA["SDA"]
        MPU_SCL["SCL"]
        MPU_AD0["AD0"]
    end

    subgraph GPS_Module ["NEO-6M GPS Receiver"]
        GPS_VCC["VCC"]
        GPS_GND["GND"]
        GPS_TX["TXD"]
        GPS_RX["RXD"]
    end

    subgraph Alert_IO ["Audible & User I/O"]
        BUZ_POS["Buzzer (+)"]
        BUZ_NEG["Buzzer (-)"]
        BTN_1["Cancel Button Pin 1"]
        BTN_2["Cancel Button Pin 2"]
    end

    subgraph Optional_GSM ["SIM800L Module (External Power)"]
        GSM_VCC["VCC (4.0V, 2A)"]
        GSM_GND["GND"]
        GSM_TXD["TXD"]
        GSM_RXD["RXD"]
        EXT_PWR["LM2596 / 18650 Battery (4.0V Regulated)"]
        CAP["1000uF 16V Buffer Cap"]
    end

    %% Wiring Connections
    ESP_3V3 --> MPU_VCC
    ESP_3V3 --> GPS_VCC
    ESP_GND --> MPU_GND
    ESP_GND --> MPU_AD0
    ESP_GND --> GPS_GND
    ESP_GND --> BUZ_NEG
    ESP_GND --> BTN_2

    GPIO_21 <--> MPU_SDA
    GPIO_22 --> MPU_SCL

    GPS_TX --> GPIO_16
    GPIO_17 --> GPS_RX

    GPIO_4 --> BUZ_POS
    GPIO_15 --> BTN_1

    %% Optional GSM Wiring
    EXT_PWR --> GSM_VCC
    EXT_PWR --> CAP
    CAP --> GSM_GND
    EXT_PWR --> GSM_GND
    GSM_GND --- ESP_GND
    GSM_TXD -->|GPIO 26 RX| ESP32_Controller
    ESP32_Controller -->|GPIO 27 TX| GSM_RXD
```

---

## 3. ASCII Circuit Diagram

```
                 +---------------------------------------+
                 |            ESP32 Microcontroller      |
                 |                                       |
                 |  [3.3V]  [GND]   [21]   [22]   [16]   |
                 +----+-------+-------+------+------+----+
                      |       |       |      |      |
         +------------+       |       |      |      |
         |                    |       |      |      |
   +-----+-----+              |       |      |      |
   |  MPU6050  |              |       |      |      |
   |  VCC  GND |<-------------+       |      |      |
   |  SDA  SCL |<---------------------+------+      |
   |  AD0 (GND)|                      |             |
   +-----------+                      |             |
                                      |             |
   +-----------+                      |             |
   |  NEO-6M   |                      |             |
   |  VCC  GND |<---------------------+             |
   |  TXD      |------------------------------------+
   +-----------+
                                      |
   +-----------+                      |
   |  BUZZER   |                      |
   |  (+)  (-) |<---------------------+
   |   ^       |
   +---|-------+
       |
     GPIO 4

   +-----------+
   |  BUTTON   |
   |  (Cancel) |
   |   1     2 |<---------------------+
   +---|-------+
       |
     GPIO 15 (Pullup)
```

---

## 4. Hardware Wiring Best Practices
1. **Twisted Pairs for I2C:** Keep wires between MPU6050 and ESP32 under 20 cm in length to prevent inductive noise or data corruption.
2. **GPS Antenna Placement:** The ceramic patch on the NEO-6M GPS antenna must face unobstructed toward the sky or open window. Indoors, satellite lock may take 2–5 minutes.
3. **Common Ground Reference:** When using external power supplies for GSM or high-power buzzers, always tie all ground (`GND`) pins together.
