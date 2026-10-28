# Wiring notes (verify against your exact modules)

This document is a planning reference, not a substitute for the datasheets and pin labels for your exact boards.

## DS18B20 temperature sensor

- ESP32 GPIO 4 connects to the DS18B20 data line.
- Sensor VCC and GND connect to the correct supply and ground for your sensor module.
- A bare DS18B20 commonly needs a pull-up resistor between DATA and VCC; some modules already include one.
- Confirm the sensor pin order from its datasheet before powering the circuit.

## MAX30100 pulse-oximeter module

- Connect the module's I²C SDA/SCL, power, and ground according to the exact breakout board's specifications.
- ESP32 default I²C pins are commonly GPIO 21 (SDA) and GPIO 22 (SCL), but verify the board and wiring.
- Some MAX30100 breakout boards have different voltage requirements. Do not assume every board accepts 5 V.

## Buzzer (optional)

- The earlier design used GPIO 15 as a buzzer control pin.
- Check whether the buzzer module is active or passive and ensure its current draw is safe for the ESP32 GPIO. Use a suitable driver if needed.

## Network

- ESP32 devices send JSON to `http://<LAPTOP-LAN-IP>:5000/data`.
- The laptop and devices should be connected to the same Wi-Fi/LAN.
- Do not expose the development server directly to the public internet.
