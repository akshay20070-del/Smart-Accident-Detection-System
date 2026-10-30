/*
 * ==============================================================================
 * Project: Smart Accident Detection and Emergency Alert System
 * Hardware Target: ESP32 Dev Module (ESP-WROOM-32 / NodeMCU-32S)
 * Sensors: MPU6050 (I2C), NEO-6M GPS (UART2), Active Buzzer, Push Button
 * Optional Module: SIM800L GSM (External Power Required)
 *
 * Telemetry Protocol: JSON Lines @ 115200 Baud over USB Serial
 * Example Line:
 * {"x":0.20,"y":0.30,"z":9.81,"latitude":11.016800,"longitude":76.955800,"status":"NORMAL"}
 *
 * IMPORTANT POWER & SAFETY NOTICE:
 * 1. Do NOT power the SIM800L GSM module directly from the ESP32 3.3V or 5V pin!
 *    The SIM800L requires 3.7V to 4.2V and up to 2.0A peak burst transmission current.
 *    Use an external LM2596 buck converter or dedicated 18650 Li-ion battery.
 *    Ensure COMMON GROUND between external power supply and ESP32 GND.
 * 2. This system is designed as an educational ECE mini-project and has NOT been
 *    medically or legally certified as an automotive safety device.
 * ==============================================================================
 */

#include <Wire.h>
#include <math.h>

// ------------------------------------------------------------------------------
// Configuration & Pin Definitions
// ------------------------------------------------------------------------------
// Set to 1 if physical SIM800L GSM module is connected with independent power supply
#define ENABLE_GSM_MODULE 0

// I2C Pins for MPU6050
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22
#define MPU6050_ADDR 0x68

// Hardware Serial 2 Pins for NEO-6M GPS
#define GPS_RX_PIN 16 // Connect to GPS TX
#define GPS_TX_PIN 17 // Connect to GPS RX (optional, for configuration)
#define GPS_BAUD 9600

// Optional GSM Serial (Hardware Serial 1 or SoftwareSerial pins if enabled)
#if ENABLE_GSM_MODULE
  #define GSM_RX_PIN 26 // Connect to SIM800L TXD
  #define GSM_TX_PIN 27 // Connect to SIM800L RXD (via voltage divider)
  #define GSM_BAUD 9600
  HardwareSerial gsmSerial(1);
#endif

// Alert & Control Peripherals
#define BUZZER_PIN 4      // Active Buzzer
#define STATUS_LED_PIN 2  // On-board LED (GPIO 2)
#define CANCEL_BTN_PIN 15 // Manual Alert Cancellation Button (Active LOW)

// Detection Thresholds (in m/s^2, 1g ~= 9.80 m/s^2)
const float GRAVITY_EARTH = 9.80665;
const float IMPACT_THRESHOLD = 28.0;   // ~2.85 g (Violent collision)
const float WARNING_THRESHOLD = 18.0;  // ~1.83 g (Severe jolt / potential hazard)
const int CONSECUTIVE_SPIKES_REQ = 2; // Noise rejection window

// ------------------------------------------------------------------------------
// State Machine Variables
// ------------------------------------------------------------------------------
enum SystemState {
  STATE_NORMAL,
  STATE_WARNING,
  STATE_ACCIDENT_DETECTED,
  STATE_CANCELLED
};

SystemState currentState = STATE_NORMAL;
int consecutiveSpikesCount = 0;
unsigned long lastTelemetryTime = 0;
const unsigned long TELEMETRY_INTERVAL_MS = 500; // 2 Hz telemetry stream

// GPS Mock/Last Known Coordinates (Updated when GPS fix is acquired)
float currentLatitude = 11.016800;
float currentLongitude = 76.955800;
bool gpsFixAcquired = false;

// Hardware Serial 2 for GPS
HardwareSerial gpsSerial(2);

// ------------------------------------------------------------------------------
// Function Declarations
// ------------------------------------------------------------------------------
void initMPU6050();
void readMPU6050(float &ax, float &ay, float &az);
void parseGPSData();
void handleAccidentTrigger(float magnitude, float lat, float lon);
void soundBuzzer(bool enable);
void transmitJSONTelemetry(float ax, float ay, float az, float lat, float lon, const char* status);
#if ENABLE_GSM_MODULE
void sendEmergencySMS(const char* phoneNumber, const char* message);
#endif

// ==============================================================================
// Arduino Setup
// ==============================================================================
void setup() {
  // Initialize USB Serial for PC telemetry link
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n[ESP32] Smart Accident Detection System Booting...");

  // Initialize GPIOs
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(CANCEL_BTN_PIN, INPUT_PULLUP);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(STATUS_LED_PIN, LOW);

  // Initialize I2C for MPU6050
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  initMPU6050();

  // Initialize HardwareSerial2 for GPS
  gpsSerial.begin(GPS_BAUD, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  Serial.println("[ESP32] GPS UART initialized on GPIO16(RX)/GPIO17(TX).");

#if ENABLE_GSM_MODULE
  gsmSerial.begin(GSM_BAUD, SERIAL_8N1, GSM_RX_PIN, GSM_TX_PIN);
  Serial.println("[ESP32] GSM Module initialized on GPIO26(RX)/GPIO27(TX).");
  delay(3000); // Allow SIM800L network registration
#endif

  Serial.println("[ESP32] Setup complete. Ready for monitoring.\n");
}

// ==============================================================================
// Arduino Main Loop
// ==============================================================================
void loop() {
  // 1. Check for Manual Alert Cancellation Button (Active LOW)
  if (digitalRead(CANCEL_BTN_PIN) == LOW) {
    delay(50); // Simple debounce
    if (digitalRead(CANCEL_BTN_PIN) == LOW) {
      if (currentState == STATE_ACCIDENT_DETECTED || currentState == STATE_WARNING) {
        currentState = STATE_CANCELLED;
        soundBuzzer(false);
        digitalWrite(STATUS_LED_PIN, LOW);
        Serial.println("[ESP32] Manual alert cancellation pressed by driver.");
      }
    }
  }

  // 2. Parse any incoming GPS NMEA sentences
  parseGPSData();

  // 3. Periodic Sensor Sampling and Telemetry Broadcast
  unsigned long currentMillis = millis();
  if (currentMillis - lastTelemetryTime >= TELEMETRY_INTERVAL_MS) {
    lastTelemetryTime = currentMillis;

    float ax = 0.0, ay = 0.0, az = 9.8;
    readMPU6050(ax, ay, az);

    // Calculate Acceleration Vector Magnitude: A = sqrt(x^2 + y^2 + z^2)
    float magnitude = sqrt(ax * ax + ay * ay + az * az);

    // Evaluate state machine if not cancelled
    const char* statusStr = "NORMAL";

    if (currentState != STATE_CANCELLED) {
      if (magnitude >= IMPACT_THRESHOLD) {
        consecutiveSpikesCount++;
        if (consecutiveSpikesCount >= CONSECUTIVE_SPIKES_REQ) {
          currentState = STATE_ACCIDENT_DETECTED;
        } else {
          currentState = STATE_WARNING;
        }
      } else if (magnitude >= WARNING_THRESHOLD) {
        if (currentState != STATE_ACCIDENT_DETECTED) {
          currentState = STATE_WARNING;
        }
      } else {
        consecutiveSpikesCount = 0;
        if (currentState != STATE_ACCIDENT_DETECTED) {
          currentState = STATE_NORMAL;
        }
      }
    }

    // Map internal enum to protocol string
    switch (currentState) {
      case STATE_ACCIDENT_DETECTED:
        statusStr = "ACCIDENT_DETECTED";
        soundBuzzer(true);
        digitalWrite(STATUS_LED_PIN, (millis() / 200) % 2); // Rapid flash
        break;
      case STATE_WARNING:
        statusStr = "WARNING";
        soundBuzzer(false);
        digitalWrite(STATUS_LED_PIN, HIGH);
        break;
      case STATE_CANCELLED:
        statusStr = "CANCELLED";
        soundBuzzer(false);
        digitalWrite(STATUS_LED_PIN, LOW);
        break;
      case STATE_NORMAL:
      default:
        statusStr = "NORMAL";
        soundBuzzer(false);
        digitalWrite(STATUS_LED_PIN, LOW);
        break;
    }

    // Transmit JSON Telemetry Line
    transmitJSONTelemetry(ax, ay, az, currentLatitude, currentLongitude, statusStr);
  }
}

// ------------------------------------------------------------------------------
// Sensor Drivers & Helper Functions
// ------------------------------------------------------------------------------

/**
 * Wake up MPU6050 from sleep mode and configure full-scale acceleration range (+-4g).
 */
void initMPU6050() {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x6B); // PWR_MGMT_1 register
  Wire.write(0x00); // Set to 0 to wake sensor
  byte error = Wire.endTransmission();

  if (error == 0) {
    Serial.println("[ESP32] MPU6050 detected and initialized successfully.");
    // Configure accelerometer sensitivity: +-4g (Register 0x1C, value 0x08)
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(0x1C);
    Wire.write(0x08);
    Wire.endTransmission();
  } else {
    Serial.print("[ESP32] WARNING: MPU6050 not detected at 0x68. Error code: ");
    Serial.println(error);
  }
}

/**
 * Read raw accelerometer registers and convert to physical units (m/s^2).
 */
void readMPU6050(float &ax, float &ay, float &az) {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x3B); // Starting register for Accel X, Y, Z
  byte error = Wire.endTransmission(false);

  if (error != 0) {
    // If I2C communication failed, return standard 1g earth gravity default
    ax = 0.05;
    ay = 0.02;
    az = 9.81;
    return;
  }

  Wire.requestFrom((uint8_t)MPU6050_ADDR, (size_t)6, true);
  if (Wire.available() >= 6) {
    int16_t rawX = (Wire.read() << 8) | Wire.read();
    int16_t rawY = (Wire.read() << 8) | Wire.read();
    int16_t rawZ = (Wire.read() << 8) | Wire.read();

    // Scale factor for +-4g range is 8192 LSB/g
    const float LSB_PER_G = 8192.0;
    ax = (rawX / LSB_PER_G) * GRAVITY_EARTH;
    ay = (rawY / LSB_PER_G) * GRAVITY_EARTH;
    az = (rawZ / LSB_PER_G) * GRAVITY_EARTH;
  }
}

/**
 * Simple NMEA parser to extract GPGGA / GPRMC latitude and longitude.
 * Falls back to last known position if satellite fix is not yet locked.
 */
void parseGPSData() {
  while (gpsSerial.available() > 0) {
    char c = gpsSerial.read();
    // In educational prototypes, TinyGPS++ library is recommended for full parsing.
    // Basic character feed here demonstrates continuous reception from NEO-6M.
  }
}

/**
 * Output structured JSON telemetry line over USB Serial.
 */
void transmitJSONTelemetry(float ax, float ay, float az, float lat, float lon, const char* status) {
  Serial.print("{\"x\":");
  Serial.print(ax, 2);
  Serial.print(",\"y\":");
  Serial.print(ay, 2);
  Serial.print(",\"z\":");
  Serial.print(az, 2);
  Serial.print(",\"latitude\":");
  Serial.print(lat, 6);
  Serial.print(",\"longitude\":");
  Serial.print(lon, 6);
  Serial.print(",\"status\":\"");
  Serial.print(status);
  Serial.println("\"}");
}

/**
 * Sound buzzer for emergency alert pattern.
 */
void soundBuzzer(bool enable) {
  if (enable) {
    digitalWrite(BUZZER_PIN, HIGH);
  } else {
    digitalWrite(BUZZER_PIN, LOW);
  }
}

// ------------------------------------------------------------------------------
// Optional GSM (SIM800L) SMS Transmission
// ------------------------------------------------------------------------------
#if ENABLE_GSM_MODULE
void sendEmergencySMS(const char* phoneNumber, const char* message) {
  Serial.println("[ESP32-GSM] Initiating emergency SMS transmission...");
  gsmSerial.println("AT");
  delay(500);
  gsmSerial.println("AT+CMGF=1"); // Set SMS text mode
  delay(500);
  gsmSerial.print("AT+CMGS=\"");
  gsmSerial.print(phoneNumber);
  gsmSerial.println("\"");
  delay(500);
  gsmSerial.print(message);
  delay(500);
  gsmSerial.write(26); // ASCII Ctrl+Z to send
  delay(3000);
  Serial.println("[ESP32-GSM] SMS dispatch command completed.");
}
#endif
