# Raspberry Pi Pico W Drag Race Controller

A comprehensive timing system for Hot Wheels or similar model car drag racing, built on the Raspberry Pi Pico W platform. Features a web-based control interface, LED light tree, and multi-lane support.

## Project Structure

```
race_controller/
├── main.py               # Entry point and main loop
├── config.py             # All configuration parameters
├── boot.py               # Initial system setup on boot
├── lane.py               # Lane class
├── race_manager.py       # RaceManager class
├── display/              # Display components
│   ├── __init__.py       # Makes directory a package
│   ├── controller.py     # DisplayController class
│   └── basic_display.py  # Basic display driver for HT16K33
├── led/                  # LED components
│   ├── __init__.py       # Makes directory a package
│   ├── ws2812b.py        # LED strip functions
│   ├── animations.py     # LED animations
│   └── aux_lighting.py   # Additional lighting functions
├── web/                  # Web server components
│   ├── __init__.py       # Makes directory a package
│   ├── server.py         # Web server implementation
│   ├── index.html        # Main web page
│   ├── control.html      # Race control interface
│   └── test.html         # Test page for API functionality
└── utils/                # Utility functions
    ├── __init__.py       # Makes directory a package
    ├── helpers.py        # Helper functions
    ├── sensor_test.py    # Sensor testing utility
    └── phototransistor_test.py  # Phototransistor testing utility
```

## Features

- **Professional Drag Race Timing**:
  - Christmas tree light sequence with amber staging lights
  - Precise reaction time measurement
  - Race time measurement from green light to finish
  - False start (red light) detection

- **Multi-Lane Support**:
  - Independent timing for up to 5 lanes
  - Position tracking (1st, 2nd, etc.)
  - Independent servo control for starting gates

- **Web Interface**:
  - Control races from any device with a web browser
  - Real-time race status and results
  - Mobile-friendly responsive design
  - No app installation required

- **Display System**:
  - HT16K33-based 7-segment displays (1-2 per lane)
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
  - Test functionality without physical hardware
  - Configurable reaction and race times
  - Simulated beam breaks based on timing

## Hardware Requirements

- Raspberry Pi Pico W
- Start/finish line sensors (normally-closed beam break sensors)
- WS2812B LED strip
- HT16K33-based 7-segment displays (optional)
- SG90 servos for starting gates
- Pushbuttons for controls
- 5V power supply for LED strip

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

- **Control**:
  - Start race button: GPIO 6
  - Reset button: GPIO 7
  - WS2812B LED data: GPIO 28
  - I2C for displays: SDA (GPIO 20), SCL (GPIO 21)

## Installation

1. Clone this repository to your local machine
2. Connect your Raspberry Pi Pico W to your computer
3. Copy all files to the Pico W, maintaining the directory structure
4. Reset the Pico W to start the program

## Configuration

All settings can be adjusted in `config.py`:

- Timing parameters
- Servo positions
- Display settings
- LED configuration
- Simulation mode
- WiFi settings
- Web server options

### WiFi Configuration

To use the web interface, configure the WiFi settings in `config.py`:

```python
# Home network settings (primary connection)
HOME_WIFI_SSID = 'YourHomeWiFi'        # Your home WiFi name
HOME_WIFI_PASSWORD = 'YourPassword'    # Your home WiFi password

# Fallback AP settings (if home network connection fails)
AP_WIFI_SSID = 'DragRaceTimer'         # Name for the fallback AP
AP_WIFI_PASSWORD = 'race123456'        # Password for the fallback AP
```

## Usage

### Physical Controls

1. Power on the system
2. Press the reset button to initialize
3. Place cars at the starting gates
4. Press start to begin the light sequence
5. Players press their buttons to release cars when the green light comes on
6. Results are displayed on the 7-segment displays and via LED animations

### Web Interface

1. Connect to the WiFi network "DragRaceTimer" with password "race123456"
   - If configured, the system will connect to your home WiFi instead
2. Open a web browser and navigate to the IP address shown on the display or console
   - Default for access point mode: http://192.168.4.1
3. Use the web interface to:
   - Start races
   - Reset the system
   - View real-time race status and results

The web interface automatically updates every 2 seconds to show current race status. You can also use the "Manual Refresh" button to update immediately.

## Simulation Mode

To test without full hardware setup, enable simulation mode in `config.py`:

```python
# Global simulation mode
SIMULATION_MODE = True

# Lane-specific simulation (False = use real hardware, True = simulate)
LANE_SIMULATION_ENABLED = [False, True, True, True]  # Lane 1 hardware, others simulated
```

This allows you to test the system with any combination of real and simulated lanes.

## Extending the Project

- Add more lanes by extending the lane configuration
- Implement different race modes (bracket racing, etc.)
- Enhance the web interface with additional features
- Create a mobile app using the existing API endpoints
- Add data logging and race history tracking

## Troubleshooting

- **No web interface**: Check WiFi settings and confirm the Pico W's IP address
- **Sensor issues**: Run the sensor test utilities in the `utils` directory
- **Display problems**: Verify I2C connections and addresses
- **LED strip not working**: Check power supply and data pin connection

## License

This project is open source and available under the MIT License.
