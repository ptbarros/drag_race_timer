# Configuration file for Raspberry Pi Pico Drag Race Controller

# ------------------
# Light sequence timing (in milliseconds)
# ------------------
LIGHT_ON_DURATION = 1000    # How long each light stays on
TRANSITION_DELAY = 200      # Delay between one light turning off and the next turning on

# ------------------
# Race setup timing
# ------------------
PRE_START_DELAY = 3000      # Delay before starting the light sequence
POST_RACE_DELAY = 2000      # Delay after race completion before allowing a new race
RACE_TIMEOUT = 15000        # Maximum time for a race before auto-complete (15 seconds)

# ------------------
# Servo settings
# ------------------
# Global defaults
SERVO_OPEN_POSITION = 8200  # Default PWM value for servo in open position
SERVO_CLOSED_POSITION = 2000  # Default PWM value for servo in closed position
SERVO_HOLD_TIME = 500       # How long to hold servo in open position

# Lane-specific servo positions (overrides defaults)
LANE_SERVO_POSITIONS = [
    {"open": 8200, "closed": 2000},  # Lane 1
    {"open": 8000, "closed": 2200},   # Lane 2
    {"open": 8200, "closed": 2000},  # Lane 3
    {"open": 8200, "closed": 2000},  # Lane 4
    {"open": 8200, "closed": 2000}   # Lane 5
]

# ------------------
# Main loop timing
# ------------------
LOOP_DELAY = 5              # Delay in main loop for timing responsiveness
BUTTON_DEBOUNCE = 500       # Debounce time for buttons

# ------------------
# Display settings
# ------------------
DISPLAY_ENABLED = True               # Enable/disable displays
NUM_LANES = 2                        # Define the number of lanes
DISPLAYS_PER_LANE = 2                # Number of displays per lane (set to 2 for dual displays)
I2C_SDA_PIN = 20                     # SDA pin for I2C (GPIO 20)
I2C_SCL_PIN = 21                     # SCL pin for I2C (GPIO 21)
DISPLAY_BRIGHTNESS = 1               # Display brightness (0-15)

# Display I2C addresses - set explicitly for each display
# Format: [lane1_display1, lane1_display2, lane2_display1, lane2_display2, ...]
DISPLAY_ADDRESSES = [0x70, 0x72, 0x71, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79]  # Adjust as needed
# Display cycling settings
DISPLAY_CYCLE_ENABLED = True     # Enable cycling between different info on secondary displays
DISPLAY_CYCLE_INTERVAL = 3000    # Time to display each piece of info (in milliseconds)

# ------------------
# Simulation mode settings
# ------------------
SIMULATION_MODE = True               # Enable/disable simulation mode
SIMULATION_REACTION_TIMES = [200, 300, 250, 225, 275]  # Reaction time in ms for each lane
SIMULATION_RACE_TIMES = [4000, 3500, 3800, 4200, 3600]    # Total race time in ms for each lane
# Lane-specific simulation flags (False = use real hardware, True = simulate)
LANE_SIMULATION_ENABLED = [False, False, True, True, True]  # First two lanes use real hardware
# ------------------
# WS2812B LED Configuration
# ------------------
WS2812B_PIN = 28           # GPIO pin connected to the WS2812B data line
LEDS_PER_LANE = 5          # Number of LEDs per lane (amber1, amber2, amber3, green, red)
SEPARATION_LEDS = 3        # Number of LEDs to use as separation between lanes

# Total number of LEDs needed with separation
NUM_LEDS = (LEDS_PER_LANE * NUM_LANES) + (SEPARATION_LEDS * (NUM_LANES - 1))

# Define colors (in GRB order for WS2812B) - GRB, not RGB!
YELLOW = 0xFFFF00          # Yellow (GRB: G=FF, R=FF, B=00)
GREEN = 0xFF0000           # Green (GRB: G=FF, R=00, B=00)
RED = 0x00FF00             # Red (GRB: G=00, R=FF, B=00)
BLUE = 0x0000FF            # Blue (GRB: G=00, R=00, B=FF)
WHITE = 0xFFFFFF           # White
BLACK = 0x000000           # Off

# WS2812B light tree sequence colors
TREE_COLORS = {
    "amber1": YELLOW,
    "amber2": YELLOW,
    "amber3": YELLOW,
    "green": GREEN,
    "red": RED,
    "off": BLACK
}

# LED mapping for each lane, defining which LEDs correspond to which light in the sequence
# With 5 lanes, we need to map each lane's lights to the correct LED positions
LED_MAPPING = {
    1: {  # Lane 1
        "amber1": 0,
        "amber2": 1,
        "amber3": 2,
        "green": 3,
        "red": 4
    },
    2: {  # Lane 2
        "amber1": 8,    # Offset by LEDS_PER_LANE + SEPARATION_LEDS
        "amber2": 9,
        "amber3": 10,
        "green": 11,
        "red": 12
    },
    3: {  # Lane 3
        "amber1": 16,
        "amber2": 17,
        "amber3": 18,
        "green": 19,
        "red": 20
    },
    4: {  # Lane 4
        "amber1": 24,
        "amber2": 25,
        "amber3": 26,
        "green": 27,
        "red": 28
    },
    5: {  # Lane 5
        "amber1": 32,
        "amber2": 33,
        "amber3": 34,
        "green": 35,
        "red": 36
    }
}


# ------------------
# Pin Assignments
# ------------------
# Lane 1 pins
LANE1_START_PIN = 0
LANE1_FINISH_PIN = 1
LANE1_SERVO_PIN = 8
LANE1_PLAYER_BTN_PIN = 4

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

# Control pins
START_BUTTON_PIN = 6
RESET_BUTTON_PIN = 7
