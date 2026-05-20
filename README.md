# Wearable Device for Non-Sighted Stage Navigation
Wearable aspect of the UWB app. This is the code for the wearable electronics, to be integrated with the [UWB localisation system](https://github.com/alinanila/uwb_app).

Move to FreeRTOS so that can add button interrupts and tasks for haptics.
Need to find a way to do bluetooth audio on esp.

## System overview

| Component | Quantity |
|---|:---:|
| Raspberry Pi Zero 2 W | 1 |
| BNO085 9-DoF | 1 |
| DWM3001CDK | 1 |

Add wiring diagram and explain what all the things are doing

### Raspberry Pi Zer 2 W

Controller for sensors on the performer.

Include pinout.

### BNO085 (I2C) - 9-DoF Inertial Measurement Unit
| BNO085 Pin |ESP Pin | Description |
|:---:|:---:|:---:|
| VIN | 3V | 3.3V power |
| GND | GND | Ground |
| SDA | SDA | I2C data |
| SCL | SCL| I2C clock|

PS0 and PS1 are pulled low by default, this sets the operating mode to I2C

### DWM3001CDK - UWB Tag

More information on the tag in the other repo, only here for power.

### Sam's board

Need to actually look at her repo and work out how I could connect to this with the esp.
