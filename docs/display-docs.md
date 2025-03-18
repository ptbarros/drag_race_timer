# Display Configuration Guide

The Drag Race Controller supports HT16K33-based 7-segment displays for showing race information. The system is flexible and can operate with various display configurations.

## Configuration Options

These settings can be adjusted in `config.py`:

```python
DISPLAY_ENABLED = True               # Enable/disable displays
NUM_LANES = 5                        # Define the number of lanes
DISPLAYS_PER_LANE = 2                # Number of displays per lane (1 or 2)
I2C_SDA_PIN = 20                     # SDA pin for I2C (GPIO 20)
I2C_SCL_PIN = 21                     # SCL pin for I2C (GPIO 21)
DISPLAY_BRIGHTNESS = 1               # Display brightness (0-15)

# Display cycling settings
DISPLAY_CYCLE_ENABLED = True         # Enable cycling between different info
DISPLAY_CYCLE_INTERVAL = 3000        # Time to display each piece of info (ms)
```

## Display Modes

### Single Display Per Lane
When `DISPLAYS_PER_LANE = 1`, each lane uses a single display that cycles between:
- Race time (with appropriate decimal places)
- Lane position (centered number)
- Status information (READY, FOUL, etc.)

This mode is ideal when you have limited displays or want a more compact setup.

### Dual Display Per Lane
When `DISPLAYS_PER_LANE = 2`, each lane uses two displays:
- Primary display: Shows race time or position
- Secondary display: Cycles between reaction time and status information

This provides more comprehensive race information at a glance.

## Auto-Detection

The DisplayController automatically detects available displays on the I2C bus and assigns them to lanes based on:
1. The number of lanes configured (`NUM_LANES`)
2. The number of displays per lane (`DISPLAYS_PER_LANE`)

If you have fewer displays than required for your configuration, the system will gracefully handle this by assigning displays to lanes in order and providing placeholder information for missing displays.

## I2C Addressing

You can control display addressing in two ways:

### Default Auto-Assignment
The system scans the I2C bus and automatically assigns displays in the order they're discovered.

### Prioritized Assignment
You can provide a priority list of addresses in `config.py`:

```python
DISPLAY_ADDRESSES = [0x70, 0x72, 0x71, 0x73, 0x74, 0x75, 0x76, 0x77]
```

The system will use this list to assign displays in the specified order, but only if the addresses are actually found on the I2C bus.

## Display Content

The displays show various types of information during a race:

- **Ready State**: "RDY-" or "STBY"
- **Race Time**: Time in seconds with appropriate decimal places
- **Position**: Centered lane position number (1-5)
- **Reaction Time**: Time between green light and car launch
- **False Start**: "FOUL" or "RED-" indicators

## Hardware Setup

Connect your HT16K33 displays to the I2C bus:
- SDA: GPIO 20 (default)
- SCL: GPIO 21 (default)

Each display should have a unique I2C address, which can be set using the address jumpers on the display board.

## Troubleshooting

If displays aren't showing up:
1. Check the I2C wiring
2. Verify that each display has a unique address
3. Run the I2C scanner (`utils.helpers.scan_i2c()`) to see what addresses are detected
4. Check the DisplayController initialization logs for errors
