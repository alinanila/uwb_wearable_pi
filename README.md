# Wearable Device for Non-Sighted Stage Navigation

Wearable Raspberry Pi application for the UWB stage navigation system. The Pi reads a BNO085 IMU, latches button press events from a GPIO input, and publishes IMU messages over ZeroMQ for the main localisation system.

This project was originally converted from ESP32 firmware. The current target is a Raspberry Pi Zero 2 W.

## System Overview

| Component | Quantity | Purpose |
|---|:---:|---|
| Raspberry Pi Zero 2 W | 1 | Runs the wearable publisher |
| BNO085 9-DoF IMU | 1 | Orientation, acceleration, gyro, step and stability data |
| Momentary button | 1 | Performer input, reported in IMU messages |
| DWM3001CDK | 1 | UWB tag, powered alongside the Pi |

## Raspberry Pi Zero 2 W

Enable I2C before running the app:

```bash
sudo raspi-config
```

Use `Interface Options > I2C > Enable`, then reboot if prompted.

The app uses Broadcom GPIO numbering. The default button pin is GPIO17 and can be changed in `config/wearable.yaml`.

## BNO085 Wiring

| BNO085 Pin | Raspberry Pi Pin | Description |
|:---:|:---:|---|
| VIN | 3V3 | 3.3 V power |
| GND | GND | Ground |
| SDA | GPIO2 / SDA1 | I2C data |
| SCL | GPIO3 / SCL1 | I2C clock |

PS0 and PS1 are pulled low by default, which sets the BNO085 operating mode to I2C.

### I2C Stability

The BNO085 can expose Raspberry Pi I2C clock-stretching issues. Symptoms include debug packets with `UNKNOWN Report Type` and `KeyError` values such as `123` or `124` during startup or reads.

First try changing the hardware I2C baudrate in `/boot/firmware/config.txt` and rebooting:

```text
dtparam=i2c_arm_baudrate=400000
```

If hardware I2C is still unreliable, enable a software I2C bus instead:

```text
dtoverlay=i2c-gpio,bus=8
```

After rebooting, confirm the bus exists:

```bash
ls /dev/i2c*
```

Then set `bno085.i2c_bus: 8` in `config/wearable.yaml`.

## Button Wiring

The default configuration expects a momentary button wired between GPIO17 and GND. The software enables the internal pull-up resistor through `gpiozero`, so a press pulls the input low.

## Running

Install the Raspberry Pi GPIO packages from apt, then install Hatch and run from the repository root:

```bash
sudo apt update
sudo apt install python3-rpi.gpio python3-gpiozero python3-lgpio
```

```bash
hatch run wearable
```

The default Hatch environment uses Python 3.13 for Raspberry Pi OS Trixie and enables access to system site packages. This lets Debian's Pi-specific GPIO packages satisfy dependencies from the Adafruit/Blinka stack instead of forcing pip to compile RPi.GPIO from PyPI. The default Hatch script uses config/wearable.yaml. Update imu_sink.endpoint in that file to match the host receiving IMU messages.

## Service Install

The systemd service assumes the project lives at `/home/localuwb/wearable` and Hatch is installed for the `localuwb` user. Adjust `systemd/uwb-wearable.service` if your install path or user differs.

```bash
chmod +x ./systemd/install_services.sh
sudo ./systemd/install_services.sh
```
