# ESP32 Multi-Device Real-Time Health Monitoring System

A learning/demo project that collects temperature, heart-rate, and SpO₂ readings from up to three ESP32 devices and displays the latest readings on a Flask web dashboard.

## Project structure

```text
HealthMonitor/
├── server.py
├── requirements.txt
├── .gitignore
├── README.md
├── esp32/
│   ├── esp32_health_device_1/
│   ├── esp32_health_device_2/
│   └── esp32_health_device_3/
├── docs/
│   └── wiring.md
└── screenshots/
```

## Features

- Flask server with `/data` endpoint for ESP32 JSON readings.
- SQLite history database created locally when the server starts.
- Dashboard showing device status, temperature (°F), SpO₂, and heart rate.
- Three separate ESP32 sketches, one for each device ID.
- Dashboard refreshes approximately every two seconds.

## Requirements

- Python 3.10 or newer
- Arduino IDE and ESP32 board support (only needed to build/upload firmware)
- DS18B20 temperature sensor
- Compatible MAX30100 pulse-oximeter module and Arduino library
- ESP32 boards and Wi-Fi network

## Run the dashboard server

Open Command Prompt in this project folder and run:

```powershell
python -m pip install -r requirements.txt
python server.py
```

On the laptop, open `http://127.0.0.1:5000`.

The ESP32 sketches must use the laptop's current local Wi-Fi IP address in `SERVER_URL`. The laptop and ESP32 boards need to be on the same network, and Windows Firewall may need to allow Python on private networks.

## ESP32 configuration

For each device folder, copy `config.example.h` to `config.h`, then enter the Wi-Fi network name, password, and laptop IP address in `config.h`. `config.h` is ignored by Git so credentials should not be uploaded.

Open the `.ino` file in Arduino IDE. Install compatible OneWire, DallasTemperature, and MAX30100 libraries before compiling. Library APIs vary by package, so verify that the installed MAX30100 library supports the functions used in the sketch.

## Important safety and accuracy note

This project is an educational prototype, not a medical device. Sensor readings can be inaccurate and must not be used to diagnose, treat, or make urgent medical decisions. Never rely on this system instead of appropriate medical equipment or professional advice.

## GitHub privacy

Do not commit Wi-Fi passwords, API keys, private personal data, or local database files. Keep `config.h` private and upload only `config.example.h`.
