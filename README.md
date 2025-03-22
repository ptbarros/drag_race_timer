# Raspberry Pi Pico W Drag Race Controller

A comprehensive multi-lane drag race timing system for Hot Wheels or similar model cars, built on the Raspberry Pi Pico W platform.

## Project Structure

```
race_controller/
├── main.py               # Entry point and main loop
├── config.py             # All configuration parameters
├── lane.py               # Lane class
├── race_manager.py       # RaceManager class
├── display/
│   ├── __init__.py       # Makes directory a package
│   ├── controller.py     # DisplayController class
│   └── basic_display.py  # Basic display driver for HT16K33
├── led/
│   ├── __init__.py       # Makes directory a package
│   ├── ws2812b.py        # LED strip functions
│   └── animations.py     # LED animations
└── utils/
    ├── __init__.py       # Makes directory a package
    └── helpers.py        # Helper functions
```

## Features

- **Professional Drag Race Timing**:
  - Christmas tree light sequence with amber staging lights
  - Precise reaction time measurement
  - Race time measurement from green light to finish
  - False start (red light) detection
  - Button presses during amber lights for realistic anticipation

- **Multi-Lane Support**:
  - Independent timing for up to 5 lanes
  - Position tracking (1st, 2nd, 3rd, etc.)
  - Independent servo control for starting gates

- **Display System**:
  - HT16K33-based 7-segment displays (2 per lane)
  - Race time display with millisecond precision
  - Reaction time display
  - Status information and cycling displays

- **WS2812B LED Support**:
  - Full RGB color control
  - Addressable LEDs for light tree visualization
  - Animations for race start, wins, and false starts

- **Non-Blocking Design**:
  - Responsive system with non-blocking I/O
  - Servo control without sleep delays
  - Event-based button handling

- **Simulation Mode**:
  - Configurable per-lane simulation
  - Mix of physical and simulated lanes
  - Configurable reaction and race times
  - Simulated beam breaks based on timing

## Hardware Requirements

- Raspberry Pi Pico W
- Start/finish line sensors (phototransistors with direct GPIO connection)
- WS2812B LED strip
- HT16K33-based 7-segment displays (optional)
- SG90 servos for starting gates
- Pushbuttons for controls
- 5V power supply for LED strip

## Sensor Setup

The project uses phototransistors in a simplified digital configuration:

- **Digital Sensor Wiring**:
  - Phototransistor collector connected to GPIO pin
  - Phototransistor emitter connected to GND
  - Internal pull-up resistors enabled (no external resistors needed)
  - LED beam across track to phototransistor for start/finish detection

- **Detection Logic**:
  - When beam is clear (phototransistor conducting): Reads LOW (0)
  - When beam is broken (phototransistor not conducting): Reads HIGH (1)

## Pin Assignments

The pins are defined in `config.py` and can be customized:

- **Lane 1**:
  - Start sensor: GPIO 0
  - Finish sensor: GPIO 1
  - Servo: GPIO 8
  - Player button: GPIO 4

- **Lane 2**:
  - Start sensor: GPIO 2
  - Finish sensor: GPIO 3
  - Servo: GPIO 9
  - Player button: GPIO 5

- **Lane 3**:
  - Start sensor: GPIO 10
  - Finish sensor: GPIO 11
  - Servo: GPIO 12
  - Player button: GPIO 13

- **Lane 4**:
  - Start sensor: GPIO 14
  - Finish sensor: GPIO 15
  - Servo: GPIO 16
  - Player button: GPIO 17

- **Lane 5**:
  - Start sensor: GPIO 18
  - Finish sensor: GPIO 19
  - Servo: GPIO 22
  - Player button: GPIO 26

- **Control**:
  - Start race button: GPIO 6
  - Reset button: GPIO 7
  - WS2812B LED data: GPIO 28
  - I2C for displays: SDA (GPIO 20), SCL (GPIO 21)

## Installation

1. Clone this repository to your local machine
2. Connect your Raspberry Pi Pico W to your computer
3. Copy all files to the Pico W
4. Reset the Pico W to start the program

## Configuration

All settings can be adjusted in `config.py`:

- Timing parameters
- Servo positions
- Display settings
- LED configuration
- Per-lane simulation settings

### Simulation Configuration

Configure simulation on a per-lane basis:

```python
# Lane-specific simulation flags (False = use hardware, True = simulate)
LANE_SIMULATION_ENABLED = [False, True, True, True, True]  # Lane 1 uses hardware, others simulated
```

This allows mixing real hardware with simulated lanes for testing or when building the system gradually.

## Usage

1. Power on the system
2. Press the reset button to initialize
3. Place cars at the starting gates
4. Press start to begin the light sequence
5. Players press their buttons when they want to release cars
   - Pressing before green light causes a false start (red light)
   - Reaction time is measured from green light to button press
   - Race time is measured from green light to finish line
6. Results are displayed on the 7-segment displays and via LED animations

## Extending the Project

- Add more lanes by extending the lane configuration
- Implement different race modes (bracket racing, etc.)
- Add Bluetooth or WiFi connectivity using the Pico W's wireless capabilities
- Create a web interface for race control and result tracking

## License

This project is open source and available under the MIT License.
