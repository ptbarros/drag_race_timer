# Lane class for Raspberry Pi Pico Drag Race Controller
# Updated to use digital pins with internal pull-up resistors only
from machine import Pin, PWM
import time
import config
from led.ws2812b import set_lane_light

class Lane:
    def __init__(self, lane_id, start_pin, finish_pin, servo_pin=None, player_btn_pin=None, display_controller=None):
        """
        Initialize a Lane with digital pins using pull-up resistors
        
        Parameters:
        lane_id (int): Lane identifier (1-based)
        start_pin (int): GPIO pin number for start sensor
        finish_pin (int): GPIO pin number for finish sensor
        servo_pin (int, optional): GPIO pin number for servo
        player_btn_pin (int, optional): GPIO pin number for player button
        display_controller (DisplayController, optional): Reference to display controller
        """
        self.lane_id = lane_id
        
        # Determine if this lane should use simulation
        self.use_simulation = False  # Default to hardware mode
        if hasattr(config, 'LANE_SIMULATION_ENABLED') and self.lane_id <= len(config.LANE_SIMULATION_ENABLED):
            self.use_simulation = config.LANE_SIMULATION_ENABLED[self.lane_id-1]
        
        # Print simulation status for this lane
        if self.use_simulation:
            print(f"Lane {lane_id}: SIMULATION MODE ACTIVE")
        else:
            print(f"Lane {lane_id}: HARDWARE MODE ACTIVE")
        
        # Initialize digital pins for start and finish sensors WITH pull-up resistors
        self.start_pin = Pin(start_pin, Pin.IN, Pin.PULL_UP)
        self.finish_pin = Pin(finish_pin, Pin.IN, Pin.PULL_UP)
        print(f"Lane {lane_id}: Initialized digital sensors on GPIO{start_pin} and GPIO{finish_pin} with PULL_UP")
        
        # Initialize player button and servo
        if player_btn_pin is not None:
            self.player_btn = Pin(player_btn_pin, Pin.IN, Pin.PULL_UP)
        else:
            self.player_btn = None
            
        if servo_pin is not None:
            self.servo = PWM(Pin(servo_pin))
            self.servo.freq(50)
        else:
            self.servo = None
            
        self.display_controller = display_controller
        
        # Digital pin state that indicates beam is blocked
        # With PULL_UP resistors:
        # - When beam is clear (phototransistor conducting): reads LOW (0)
        # - When beam is broken (phototransistor not conducting): reads HIGH (1)
        self.digital_blocked_state = 1  # HIGH (1) means blocked with pull-up configuration
        
        # Last known sensor states
        self.last_start_blocked = False
        self.last_finish_blocked = False
        
        self.prestaged = False
        self.staged = False
        
        # Track light states in memory
        self.tree_state = {
            "prestage": 0,
            "stage": 0,
            "amber1": 0,
            "amber2": 0,
            "amber3": 0,
            "green": 0,
            "red": 0
        }
        
        # Race state variables
        self.reaction_time = None
        self.finish_time = None
        self.start_time = None
        self.false_start = False
        self.gate_released = False
        self.start_line_broken = False  # Track if start line has been broken
        self.start_beam_time = None  # When the start beam was broken
        self.finish_line_broken = False  # Track if finish line has been broken
        self.place = None  # Position in race (1st, 2nd, etc.)
        
        # Get lane-specific servo positions or use defaults
        if lane_id <= len(config.LANE_SERVO_POSITIONS):
            self.servo_open_position = config.LANE_SERVO_POSITIONS[lane_id-1]["open"]
            self.servo_closed_position = config.LANE_SERVO_POSITIONS[lane_id-1]["closed"]
        else:
            self.servo_open_position = config.SERVO_OPEN_POSITION
            self.servo_closed_position = config.SERVO_CLOSED_POSITION
        
        # Simulation variables
        self.player_pressed_time = None  # When the player button was pressed
        self.start_sim_scheduled = False # Whether a start beam break is scheduled
        self.finish_sim_scheduled = False # Whether a finish beam break is scheduled
        
        # Non-blocking servo control variables
        self.servo_close_time = 0       # When to close the servo
        self.servo_closing_pending = False  # Whether the servo needs to be closed
        
        # Debug variables
        self.debug_mode = False  # Set to True to enable debug printing

    def set_light(self, light_name, state):
        """Set a light in the tree to on (1) or off (0) and update the LED strip"""
        if light_name in self.tree_state:
            self.tree_state[light_name] = state
            # Update the physical LED
            set_lane_light(self.lane_id, light_name, state)

    def get_light_state(self, light_name):
        """Get the current state of a light in the tree"""
        return self.tree_state.get(light_name, 0)

    def fire_servo(self):
        """Trigger the servo to release the car"""
        if not self.gate_released and self.servo is not None:
            print(f"Lane {self.lane_id}: Launching car")
            print(f"  servo.duty_u16({self.servo_open_position})")
            self.servo.duty_u16(self.servo_open_position)  # Open position
            
            # Schedule servo closing instead of blocking with sleep
            self.servo_close_time = time.ticks_ms() + config.SERVO_HOLD_TIME
            self.servo_closing_pending = True
            self.gate_released = True
            
            # In simulation mode, record when the player pressed the button
            if self.use_simulation:
                self.player_pressed_time = time.ticks_ms()
                self.start_sim_scheduled = True
    
    def update_servo(self):
        """Check if the servo needs to be closed (non-blocking)"""
        if self.servo_closing_pending and self.servo is not None and time.ticks_diff(time.ticks_ms(), self.servo_close_time) >= 0:
            print(f"  servo.duty_u16({self.servo_closed_position})")
            self.servo.duty_u16(self.servo_closed_position)  # Closed position
            self.servo_closing_pending = False

    def reset(self):
        """Reset the lane to its initial state"""
        self.reaction_time = None
        self.finish_time = None
        self.start_time = None
        self.false_start = False
        self.gate_released = False
        self.start_line_broken = False
        self.start_beam_time = None
        self.finish_line_broken = False
        self.place = None
        self.last_start_blocked = False
        self.last_finish_blocked = False
        
        # Turn off all lights
        for light in self.tree_state:
            self.set_light(light, 0)
        
        # Reset staging variables
        self.prestaged = False
        self.staged = False
        
        # Reset simulation variables
        self.player_pressed_time = None
        self.start_sim_scheduled = False
        self.finish_sim_scheduled = False
        
        # Reset servo control variables
        self.servo_closing_pending = False

    def is_start_beam_blocked(self):
        """Check if start beam is blocked using digital input with pull-up resistor"""
        # With pull-up resistors, HIGH (1) means beam is blocked
        return self.start_pin.value() == self.digital_blocked_state

    def is_finish_beam_blocked(self):
        """Check if finish beam is blocked using digital input with pull-up resistor"""
        # With pull-up resistors, HIGH (1) means beam is blocked
        return self.finish_pin.value() == self.digital_blocked_state

    def check_start_line(self):
        """Check if the start line has been crossed"""
        # In simulation mode, check if it's time to simulate a start beam break
        if self.use_simulation and self.start_sim_scheduled and not self.start_line_broken:
            current_time = time.ticks_ms()
            # Get the reaction time for this lane (default to first lane if index is out of bounds)
            sim_reaction_time = config.SIMULATION_REACTION_TIMES[self.lane_id-1] if self.lane_id <= len(config.SIMULATION_REACTION_TIMES) else config.SIMULATION_REACTION_TIMES[0]
            
            # Check if enough time has passed since the player button was pressed
            if self.player_pressed_time and time.ticks_diff(current_time, self.player_pressed_time) >= sim_reaction_time:
                self._handle_start_beam_break(current_time)
                self.start_sim_scheduled = False
                self.finish_sim_scheduled = True  # Schedule finish beam break
                return  # Early return after simulating start beam
                
            # Return early - in simulation mode, we don't check physical sensors
            return
        
        # Only check physical sensors if NOT in simulation mode 
        if not self.use_simulation:
            # Regular start beam check with digital pin using pull-up
            is_blocked = self.is_start_beam_blocked()
            
            # Detect transition from unblocked to blocked (beam break)
            if not self.start_line_broken and is_blocked and not self.last_start_blocked:
                # Car has broken the start beam
                self._handle_start_beam_break(time.ticks_ms())
            
            # Update last known state
            self.last_start_blocked = is_blocked

    def _handle_start_beam_break(self, current_time):
        """Internal helper to handle start beam break logic"""
        self.start_line_broken = True
        self.start_beam_time = current_time
        
        print(f"Lane {self.lane_id}: {'Simulated ' if self.use_simulation else ''}start beam break")
            
        # Check for false start if tree is running but green is not lit
        from race_manager import race_manager  # Import here to avoid circular import
        
        if race_manager.tree_running and not self.get_light_state('green'):
            self.false_start = True
            self.set_light('red', 1)  # Turn on red light
            print(f"Lane {self.lane_id}: RED LIGHT! False start detected.")
            
            # Show false start on display
            if self.display_controller:
                self.display_controller.show_false_start(self.lane_id - 1)
                
        # Calculate reaction time for valid starts (green light is on)
        elif self.start_time is not None:
            self.reaction_time = time.ticks_diff(current_time, self.start_time)
            print(f"Lane {self.lane_id}: Reaction {self.reaction_time} ms")
            
            # Update the reaction time display if available
            if self.display_controller:
                self.display_controller.show_reaction_time(self.lane_id - 1, self.reaction_time)

    def check_finish(self):
        """Check if the finish line has been crossed"""
        # In simulation mode, check if it's time to simulate a finish beam break
        if self.use_simulation and self.finish_sim_scheduled and not self.finish_line_broken:
            current_time = time.ticks_ms()
            # Get the race time for this lane (default to first lane if index is out of bounds)
            sim_race_time = config.SIMULATION_RACE_TIMES[self.lane_id-1] if self.lane_id <= len(config.SIMULATION_RACE_TIMES) else config.SIMULATION_RACE_TIMES[0]
            
            # Check if enough time has passed since the start beam was broken
            if self.start_beam_time and time.ticks_diff(current_time, self.start_beam_time) >= sim_race_time:
                self._handle_finish_beam_break(current_time)
                self.finish_sim_scheduled = False
                return  # Early return after simulating finish beam
                
            # Return early - in simulation mode, we don't check physical sensors
            return
        
        # Only check physical sensors if NOT in simulation mode
        if not self.use_simulation:
            # Regular finish beam check with digital pin
            is_blocked = self.is_finish_beam_blocked()
            
            # Detect transition from unblocked to blocked (beam break)
            if not self.finish_line_broken and is_blocked and not self.last_finish_blocked:
                # Car has broken the finish beam
                self._handle_finish_beam_break(time.ticks_ms())
            
            # Update last known state
            self.last_finish_blocked = is_blocked

    def _handle_finish_beam_break(self, current_time):
        """Internal helper to handle finish beam break logic"""
        self.finish_line_broken = True
        
        print(f"Lane {self.lane_id}: {'Simulated ' if self.use_simulation else ''}finish beam break")
        
        # Only record finish time if we have a start time
        if self.start_time is not None:
            self.finish_time = time.ticks_diff(current_time, self.start_time)
            print(f"Lane {self.lane_id}: Finish {self.finish_time} ms")

    def calculate_reaction_time(self):
        """Calculate reaction time for false starts at end of race"""
        if self.false_start and self.reaction_time is None and self.start_beam_time is not None:
            # For false starts, calculate how early they jumped before the green light
            if self.start_time is not None:
                # If start_time exists, calculate the reaction time
                self.reaction_time = time.ticks_diff(self.start_beam_time, self.start_time)
                # Note: This will be negative for false starts (broken beam before green light)
            else:
                # If race was aborted before green light, we can't calculate exact reaction time
                self.reaction_time = -1  # Use -1 to indicate "before green light"

    def enable_debug_mode(self, enable=True):
        """Enable or disable debug output"""
        self.debug_mode = enable
        print(f"Lane {self.lane_id}: Debug mode {'enabled' if enable else 'disabled'}")