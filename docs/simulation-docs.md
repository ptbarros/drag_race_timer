# Simulation Mode Documentation

The Drag Race Controller includes a comprehensive simulation system that allows you to test and demonstrate the system without having all the physical hardware connected.

## Configuration Options

These simulation settings can be adjusted in `config.py`:

```python
# Global simulation mode
SIMULATION_MODE = True               # Enable/disable simulation mode

# Reaction time in ms for each lane (time from player button press to start beam break)
SIMULATION_REACTION_TIMES = [200, 300, 250, 225, 275]  

# Total race time in ms for each lane (from green light to finish line)
SIMULATION_RACE_TIMES = [4000, 3500, 3800, 4200, 3600]

# Lane-specific simulation flags (False = use real hardware, True = simulate)
LANE_SIMULATION_ENABLED = [True, True, True, True, True]  # All lanes simulated
```

## Simulation Features

### Global vs. Lane-Specific Simulation

The system provides two levels of simulation control:

1. **Global Simulation Mode** (`SIMULATION_MODE`):
   - When enabled, this allows the simulation system to function
   - Affects all aspects of the race system

2. **Lane-Specific Simulation** (`LANE_SIMULATION_ENABLED`):
   - Individual control for each lane
   - Only takes effect when global simulation is disabled
   - Allows mixing of hardware and simulated lanes

### What Gets Simulated

When a lane is in simulation mode:

1. **Start Line Detection**:
   - The system simulates the car breaking the start beam
   - Uses the configured reaction time for that lane
   - Triggers after player button press

2. **Finish Line Detection**:
   - The system simulates the car crossing the finish line
   - Uses the configured race time for that lane
   - Calculated from when the start beam was broken

3. **Race Results**:
   - Position tracking works the same as with physical hardware
   - Reaction times and race times are calculated based on simulation settings

## Mixing Hardware and Simulation

To use some physical hardware while simulating the rest:

1. Set `SIMULATION_MODE = False` in `config.py`
2. Configure the `LANE_SIMULATION_ENABLED` array:
   ```python
   # Example: Lanes 1-2 use real hardware, Lanes 3-5 are simulated
   LANE_SIMULATION_ENABLED = [False, False, True, True, True]
   ```

This allows for gradual implementation of physical hardware, testing new lanes, or demonstrating multi-lane racing with limited hardware.

## Use Cases

Simulation mode is useful for:

1. **Development and Testing**:
   - Test race logic without physical sensors
   - Verify display functionality
   - Test multi-lane racing with limited hardware

2. **Demonstrations**:
   - Show how the race system works before building the hardware
   - Demonstrate features to others

3. **Troubleshooting**:
   - Isolate hardware vs. software issues
   - Verify expected behavior against simulated "known good" values

## Status Reporting

When simulation is active, the system provides clear indicators:

- Console messages showing which lanes are simulated vs. hardware
- Status logs for simulated beam breaks
- All other race functionality works normally

## Technical Implementation

The simulation system operates by:
1. Responding to player button presses
2. Waiting the configured reaction time for that lane
3. Triggering a simulated start beam break
4. Waiting the configured race time
5. Triggering a simulated finish beam break

This process closely mimics the behavior of real hardware while allowing precise control over timing for testing purposes.
