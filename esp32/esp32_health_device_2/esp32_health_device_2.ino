/*
  ESP32 Health Monitor - Device 2
  Educational prototype; not a medical device.

  Before compiling:
  1. Copy config.example.h to config.h in this folder.
  2. Fill in Wi-Fi credentials and your laptop's LAN IP in config.h.
  3. Install compatible OneWire, DallasTemperature, and MAX30100 libraries.
  4. Verify the MAX30100 library API used below matches your installed library.
*/
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <MAX30100_PulseOximeter.h>
#include "config.h"

#define ONE_WIRE_BUS 4
#define BUZZER_PIN 15

const int DEVICE_ID = 2;
const unsigned long SEND_INTERVAL_MS = 2000;
const unsigned long BUZZER_INTERVAL_MS = 500;

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensor(&oneWire);
PulseOximeter pox;

bool pulseSensorReady = false;
unsigned long lastSend = 0;
unsigned long lastBuzzer = 0;
bool buzzerOn = false;
float latestHeartRate = 0.0f;
float latestSpO2 = 0.0f;

void onBeatDetected() {
  // Optional: add a short visual or sound indication of a detected beat.
}

float readTemperatureF() {
  tempSensor.requestTemperatures();
  float tempC = tempSensor.getTempCByIndex(0);
  if (tempC == DEVICE_DISCONNECTED_C || tempC < -100.0f) {
    return 0.0f; // zero indicates unavailable/invalid reading in this demo
  }
  return DallasTemperature::toFahrenheit(tempC);
}

void updatePulseReadings() {
  if (!pulseSensorReady) {
    latestHeartRate = 0.0f;
    latestSpO2 = 0.0f;
    return;
  }

  pox.update(); // Call frequently, not only when sending HTTP data.
  float hr = pox.getHeartRate();
  float oxygen = pox.getSpO2();

  // Zero is used as an unavailable/invalid marker; never invent readings.
  latestHeartRate = (hr > 0.0f && hr < 250.0f) ? hr : 0.0f;
  latestSpO2 = (oxygen > 0.0f && oxygen <= 100.0f) ? oxygen : 0.0f;
}

void sendReading(float tempF, float spo2, float heartRate) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi not connected; skipping upload.");
    return;
  }

  HTTPClient http;
  http.setTimeout(4000);
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");

  String payload = "{\"id\":" + String(DEVICE_ID) +
                   ",\"temp\":" + String(tempF, 1) +
                   ",\"spo2\":" + String(spo2, 1) +
                   ",\"heart_rate\":" + String(heartRate, 1) + "}";

  int code = http.POST(payload);
  Serial.print("POST result: ");
  Serial.println(code);
  if (code > 0) {
    Serial.println(http.getString());
  }
  http.end();
}

void updateBuzzer(float tempF, float spo2, float heartRate) {
  // Example demo thresholds only; they are not medical advice or diagnosis.
  bool alert = (tempF > 100.4f) ||
               (spo2 > 0.0f && spo2 < 90.0f) ||
               (heartRate > 0.0f && (heartRate > 120.0f || heartRate < 50.0f));

  if (alert && millis() - lastBuzzer >= BUZZER_INTERVAL_MS) {
    lastBuzzer = millis();
    buzzerOn = !buzzerOn;
    digitalWrite(BUZZER_PIN, buzzerOn ? HIGH : LOW);
  } else if (!alert) {
    buzzerOn = false;
    digitalWrite(BUZZER_PIN, LOW);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  tempSensor.begin();
  Wire.begin();

  Serial.println("Starting ESP32 Health Monitor...");
  if (pox.begin()) {
    pulseSensorReady = true;
    pox.setOnBeatDetectedCallback(onBeatDetected);
    Serial.println("MAX30100 initialized.");
  } else {
    pulseSensorReady = false;
    Serial.println("MAX30100 initialization failed; pulse readings will be zero.");
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("Wi-Fi connected. ESP32 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Wi-Fi connection timed out; check config.h and network.");
  }
}

void loop() {
  updatePulseReadings();

  float tempF = readTemperatureF();
  updateBuzzer(tempF, latestSpO2, latestHeartRate);

  if (millis() - lastSend >= SEND_INTERVAL_MS) {
    lastSend = millis();
    Serial.printf("Device %d | Temp: %.1f F | SpO2: %.1f | HR: %.1f\n",
                  DEVICE_ID, tempF, latestSpO2, latestHeartRate);
    sendReading(tempF, latestSpO2, latestHeartRate);
  }
  delay(10);
}
