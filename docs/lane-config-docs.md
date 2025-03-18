# Lane Configuration Guide

The Drag Race Controller supports up to 5 independent racing lanes. This guide explains how to configure the system for different lane counts and hardware setups.

## Basic Configuration

The primary setting that controls the number of active lanes is in `config.py`:

```python
NUM_LANES = 5  # Set this to the desired number of lanes (1-5)
```

This single setting affects:
- How many Lane objects are created
- LED strip configuration and animations
- Display assignment
- Race position tracking
- Status reporting

## Pin Assignments

Each lane requires the following GPIO pins:

```python
# Lane 1 pins
LANE1_START_PIN = 0        # Start line sensor
LANE1_FINISH_PIN = 1       # Finish line sensor
LANE1_SERVO_PIN = 8        # Launch gate servo
LANE1_PLAYER_BTN_PIN = 4   # Player button

# Lane 2 pins
LANE2_START_PIN = 2
LANE2_FINISH_PIN = 3
LANE2_SERVO_PIN = 9
LANE2_PLAYER_BTN_PIN = 5

# Lane 3 pins
LANE3_START_PIN = 10
LANE3_FINISH_PIN = 11
LANE3_SERVO_PIN = 12
LANE3_PLAYER_BTN_PIN = 13

# Lane 4 pins
LANE4_START_PIN = 14
LANE4_FINISH_PIN = 15
LANE4_SERVO_PIN = 16
LANE4_PLAYER_BTN_PIN = 17

# Lane 5 pins
LANE5_START_PIN = 18
LANE5_FINISH_PIN = 19
LANE5_SERVO_PIN = 22
LANE5_PLAYER_BTN_PIN = 26
```

## Servo Configuration

Each lane can have customized servo positions:

```python
# Lane-specific servo positions (overrides defaults)
LANE_SERVO_POSITIONS = [
    {"open": 8200, "closed": 2000},  # Lane 1
    {"open": 8000, "closed": 2200},  # Lane 2
    {"open": 8200, "closed": 2000},  # Lane 3
    {"open": 8200, "closed": 2000},  # Lane 4
    {"open": 8200, "closed": 2000}   # Lane 5
]
```

## LED Configuration

The system automatically calculates the required number of LEDs based on your lane configuration:

```python
LEDS_PER_LANE = 5          # Number of LEDs per lane (amber1, amber2, amber3, green, red)
SEPARATION_LEDS = 3        # Number of LEDs to use as separation between lanes
# Total number of LEDs needed with separation
NUM_LEDS = (LEDS_PER_LANE * NUM_LANES) + (SEPARATION_LEDS * (NUM_LANES - 1))
```

The LED mapping defines which LEDs correspond to which light in each lane:

```python
LED_MAPPING = {
    1: {  # Lane 1
        "amber1": 0,
        "amber2": 1,
        "amber3": 2,
        "green": 3,
        "red": 4
    },
    # Additional lane mappings...
}
```

## Hardware Requirements by Lane Count

| Component | Per Lane | 2 Lanes | 3 Lanes | 4 Lanes | 5 Lanes |
|-----------|----------|---------|---------|---------|---------|
| GPIO Pins | 4        | 8       | 12      | 16      | 20      |
| Servos    | 1        | 2       | 3       | 4       | 5       |
| Sensors   | 2        | 4       | 6       | 8       | 10      |
| Buttons   | 1        | 2       | 3       | 4       | 5       |
| LEDs      | 5        | 13      | 21      | 29      | 37      |

## Additional Considerations

### Raspberry Pi Pico W Pin Limitations
The Pico W has 26 usable GPIO pins, which sets the practical upper limit for lanes without additional hardware. With 4 pins per lane plus shared control pins, 5 lanes is the maximum supported.

### Power Requirements
- Each servo typically requires 5V and can draw 500-900mA during operation
- WS2812B LEDs use approximately 60mA per LED at full brightness
- Ensure your power supply can handle the current requirements of your configuration

### Display Requirements
For the best experience:
- Single display mode: 1 display per lane
- Dual display mode: 2 displays per lane

## Example Configurations

### Basic 2-Lane Setup
```python
NUM_LANES = 2
DISPLAYS_PER_LANE = 2
```

### Compact 4-Lane Setup
```python
NUM_LANES = 4
DISPLAYS_PER_LANE = 1  # Use 1 display per lane to save on hardware
```

### Full 5-Lane Championship Setup
```python
NUM_LANES = 5
DISPLAYS_PER_LANE = 2
```

## Troubleshooting

If you encounter issues with lane configuration:

1. Verify that `NUM_LANES` matches your physical setup
2. Check that all required GPIO pins are properly connected
3. Ensure your LED strip has enough LEDs for your configuration
4. Make sure your power supply can handle the current requirements
