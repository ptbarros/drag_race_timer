# Main program for Raspberry Pi Pico Drag Race Controller
import time
from machine import Pin
import config

# Import components
from lane import Lane
from race_manager import RaceManager
from led.ws2812b import init as init_leds
from led.animations import display_startup_sequence, win_animation, false_start_animation

# Initialize the LED strip
init_leds()

# Import and initialize display controller if available
display_controller = None
try:
    from display.controller import DisplayController, DISPLAY_LIBRARIES_AVAILABLE
    
    if config.DISPLAY_ENABLED and DISPLAY_LIBRARIES_AVAILABLE:
        display_controller = DisplayController(config.NUM_LANES)
        print("Display controller initialized")
except ImportError:
    print("Display support not available")

def initialize_hardware():
    """Initialize all hardware components"""
    # Create lane objects with both digital and ADC inputs
    lanes = [
        Lane(1, 
             start_pin=config.LANE1_START_PIN, 
             finish_pin=config.LANE1_FINISH_PIN, 
             start_adc_pin=config.LANE1_START_ADC_PIN, 
             finish_adc_pin=config.LANE1_FINISH_ADC_PIN, 
             servo_pin=config.LANE1_SERVO_PIN, 
             player_btn_pin=config.LANE1_PLAYER_BTN_PIN, 
             display_controller=display_controller),
             
        Lane(2, 
             start_pin=config.LANE2_START_PIN, 
             finish_pin=config.LANE2_FINISH_PIN, 
             start_adc_pin=None,  # No ADC for additional lanes
             finish_adc_pin=None, 
             servo_pin=config.LANE2_SERVO_PIN, 
             player_btn_pin=config.LANE2_PLAYER_BTN_PIN, 
             display_controller=display_controller),
             
        Lane(3, 
             start_pin=config.LANE3_START_PIN, 
             finish_pin=config.LANE3_FINISH_PIN, 
             start_adc_pin=None,  # No ADC for additional lanes
             finish_adc_pin=None, 
             servo_pin=config.LANE3_SERVO_PIN, 
             player_btn_pin=config.LANE3_PLAYER_BTN_PIN, 
             display_controller=display_controller),
             
        Lane(4, 
             start_pin=config.LANE4_START_PIN, 
             finish_pin=config.LANE4_FINISH_PIN, 
             start_adc_pin=None,  # No ADC for additional lanes
             finish_adc_pin=None, 
             servo_pin=config.LANE4_SERVO_PIN, 
             player_btn_pin=config.LANE4_PLAYER_BTN_PIN, 
             display_controller=display_controller),
             
        # Add Lane 5 if needed
    ]
    
    # Enable debug mode if configured
    if config.SENSOR_DEBUG_MODE:
        for lane in lanes:
            lane.enable_debug_mode(True)
    
    # Create race manager
    race_manager = RaceManager(lanes, config.START_BUTTON_PIN, config.RESET_BUTTON_PIN, display_controller)
    
    return lanes, race_manager

# def initialize_hardware():
#     """Initialize all hardware components"""
#     # Create lane objects based on NUM_LANES in config
#     lanes = []
#     
#     # Lane configuration mapping
#     lane_configs = [
#         (1, config.LANE1_START_PIN, config.LANE1_FINISH_PIN, config.LANE1_SERVO_PIN, config.LANE1_PLAYER_BTN_PIN),
#         (2, config.LANE2_START_PIN, config.LANE2_FINISH_PIN, config.LANE2_SERVO_PIN, config.LANE2_PLAYER_BTN_PIN),
#         (3, config.LANE3_START_PIN, config.LANE3_FINISH_PIN, config.LANE3_SERVO_PIN, config.LANE3_PLAYER_BTN_PIN),
#         (4, config.LANE4_START_PIN, config.LANE4_FINISH_PIN, config.LANE4_SERVO_PIN, config.LANE4_PLAYER_BTN_PIN),
#         (5, config.LANE5_START_PIN, config.LANE5_FINISH_PIN, config.LANE5_SERVO_PIN, config.LANE5_PLAYER_BTN_PIN)
#     ]
#     
#     # Create only the number of lanes defined in config
#     for i in range(min(len(lane_configs), config.NUM_LANES)):
#         lane_id, start_pin, finish_pin, servo_pin, player_btn_pin = lane_configs[i]
#         lanes.append(Lane(lane_id, start_pin, finish_pin, servo_pin, player_btn_pin, display_controller))
#     
#     # Create race manager
#     race_manager = RaceManager(lanes, config.START_BUTTON_PIN, config.RESET_BUTTON_PIN, display_controller)
#     
#     return lanes, race_manager

def main():
    """Main program entry point"""
    print("Initializing Raspberry Pi Pico Drag Race Controller...")
    
    # Scan I2C bus for devices
    from utils.helpers import scan_i2c
    scan_i2c()  # This will print all connected I2C devices
    
    # Initialize hardware
    lanes, race_manager = initialize_hardware()
    
    # Display startup sequence
    display_startup_sequence()
    
    # Initial reset to ensure clean state
    race_manager.reset_race()
    
    print("System ready. Press start or reset buttons to begin.")
   
    if config.SIMULATION_MODE:
        print("SIMULATION MODE ACTIVE - Automatic sensor triggering enabled")
        # Print lane-specific simulation flags if they exist
        if hasattr(config, 'LANE_SIMULATION_ENABLED'):
            for lane_idx in range(min(len(config.LANE_SIMULATION_ENABLED), config.NUM_LANES)):
                if config.LANE_SIMULATION_ENABLED[lane_idx]:
                    print(f"  Lane {lane_idx+1}: SIMULATED")
                else:
                    print(f"  Lane {lane_idx+1}: HARDWARE")
    
    # Main loop
    while True:
        # Check buttons for reset and start race
        reset_button_state = race_manager.reset_btn.value()
        if reset_button_state == 0 and race_manager.last_reset_btn_state == 1:  # Button press detected
            race_manager.reset_race()
            time.sleep_ms(config.BUTTON_DEBOUNCE)  # Debounce
        race_manager.last_reset_btn_state = reset_button_state
        
        start_button_state = race_manager.start_btn.value()
        if start_button_state == 0 and race_manager.last_start_btn_state == 1 and not race_manager.race_started:  # Button press detected
            race_manager.start_race()
            time.sleep_ms(config.BUTTON_DEBOUNCE)  # Debounce
        race_manager.last_start_btn_state = start_button_state
    
        # Update tree lights if race is running
        if race_manager.tree_running:
            race_manager.update_tree()
        
        # Always check for player button presses
        race_manager.check_player_buttons()
        
        # Update servo positions (non-blocking)
        race_manager.update_servos()
        
        # Update secondary displays with cycling info
        if display_controller:
            display_controller.update_secondary_displays()

        # Monitor race progress if race has started
        if race_manager.race_started:
            race_complete = race_manager.monitor_race()
            if race_complete:
                # Display win animation for lane with place = 1
                for lane in race_manager.lanes:
                    if lane.place == 1:
                        win_animation(lane.lane_id)
                    elif lane.false_start:
                        false_start_animation(lane.lane_id)
                
                # Make sure to turn off all lights after animations
                race_manager.reset_all_lights()
                time.sleep_ms(100)  # Short delay
                race_manager.reset_all_lights() # Try again just to be sure
               
                # Wait a moment before allowing a new race
                time.sleep_ms(config.POST_RACE_DELAY)

        time.sleep_ms(config.LOOP_DELAY)  # Small delay for responsive timing

if __name__ == "__main__":
    main()
