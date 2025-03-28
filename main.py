# Main program for Raspberry Pi Pico Drag Race Controller
import time
from machine import Pin
import config

# Safety flag - set to True to prevent web server from starting automatically
# Helps avoid getting locked out when developing
SAFE_MODE = False

print("Initializing Drag Race Controller...")
print("Press CTRL+C within 10 seconds to interrupt startup")

# Give 10 seconds to interrupt with CTRL+C before proceeding
for i in range(10, 0, -1):
    print(f"Starting in {i} seconds... (Press CTRL+C to enter safe mode)")
    time.sleep(1)

# Import components
from lane import Lane
from race_manager import RaceManager
from led.ws2812b import init as init_leds
from led.animations import display_startup_sequence, win_animation, false_start_animation
from led.aux_lighting import illuminate_sensors, clear_all_aux_leds

# Import web server (if available)
web_server_available = False
try:
    from web.server import start_server, stop_server
    web_server_available = True
    print("Web server module available")
except ImportError:
    print("Web server module not available")

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
    # Create lane objects with digital inputs only
    lanes = [
        Lane(1, 
             start_pin=config.LANE1_START_PIN, 
             finish_pin=config.LANE1_FINISH_PIN, 
             servo_pin=config.LANE1_SERVO_PIN, 
             player_btn_pin=config.LANE1_PLAYER_BTN_PIN, 
             display_controller=display_controller),
             
        Lane(2, 
             start_pin=config.LANE2_START_PIN, 
             finish_pin=config.LANE2_FINISH_PIN, 
             servo_pin=config.LANE2_SERVO_PIN, 
             player_btn_pin=config.LANE2_PLAYER_BTN_PIN, 
             display_controller=display_controller),
             
        Lane(3, 
             start_pin=config.LANE3_START_PIN, 
             finish_pin=config.LANE3_FINISH_PIN,
             servo_pin=config.LANE3_SERVO_PIN, 
             player_btn_pin=config.LANE3_PLAYER_BTN_PIN, 
             display_controller=display_controller),
             
        Lane(4, 
             start_pin=config.LANE4_START_PIN, 
             finish_pin=config.LANE4_FINISH_PIN,
             servo_pin=config.LANE4_SERVO_PIN, 
             player_btn_pin=config.LANE4_PLAYER_BTN_PIN, 
             display_controller=display_controller),
    ]
    
    # Enable debug mode if configured
    if hasattr(config, 'SENSOR_DEBUG_MODE') and config.SENSOR_DEBUG_MODE:
        for lane in lanes:
            lane.enable_debug_mode(True)
    
    # Create race manager
    race_manager = RaceManager(lanes, config.START_BUTTON_PIN, config.RESET_BUTTON_PIN, display_controller)
    
    return lanes, race_manager

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
    
    # Initialize auxiliary lighting
    if hasattr(config, 'AUX_LED_MAPPING'):
        print("Initializing auxiliary lighting...")
        # Turn on sensor illumination
        illuminate_sensors(True)
    
    # Initial reset to ensure clean state
    race_manager.reset_race()
    
    # Start web server if available and wireless is enabled and not in safe mode
    wireless_enabled = True  # Default to enabled
    if hasattr(config, 'WIRELESS_ENABLED'):
        wireless_enabled = config.WIRELESS_ENABLED
        
    if web_server_available and wireless_enabled and not SAFE_MODE:
        print("\nWill start web server in 10 seconds...")
        print("Hold the START RACE button to SKIP web server startup")
        
        # Check if start button is pressed during countdown
        skip_server = False
        for i in range(10, 0, -1):
            print(f"{i}...")
            # Check if start button is pressed
            if race_manager.start_btn.value() == 0:  # Button is pressed (active low)
                skip_server = True
                print("Web server startup canceled by user")
                break
            time.sleep(1)
            
        if not skip_server:
            print("Starting web server...")
            web_server_success = start_server(race_manager)
            if web_server_success:
                print("Web server started successfully!")
                print(f"Connect to the URL displayed above in any browser to control the race")
            else:
                print("Failed to start web server.")
    elif SAFE_MODE:
        print("Running in SAFE MODE - web server disabled")
    
    print("System ready. Press start or reset buttons to begin.")
    
    # Print simulation status
    if hasattr(config, 'LANE_SIMULATION_ENABLED'):
        sim_count = sum(1 for sim in config.LANE_SIMULATION_ENABLED if sim)
        if sim_count > 0:
            print(f"SIMULATION MODE ACTIVE for {sim_count} lanes")
            for lane_idx in range(min(len(config.LANE_SIMULATION_ENABLED), config.NUM_LANES)):
                status = "SIMULATED" if config.LANE_SIMULATION_ENABLED[lane_idx] else "HARDWARE"
                print(f"  Lane {lane_idx+1}: {status}")
    
    # Main loop
    while True:
        # Check buttons for reset and start race
        reset_button_state = race_manager.reset_btn.value()
        if reset_button_state == 0 and race_manager.last_reset_btn_state == 1:  # Button press detected
            race_manager.reset_race()
            # Also clear any auxiliary LEDs
            if hasattr(config, 'AUX_LED_MAPPING'):
                clear_all_aux_leds()
                # Re-enable sensor illumination
                illuminate_sensors(True)
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
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        print("Entering safe mode - web server will not start")
        # If we reach here, the user pressed CTRL+C during startup
        # Continue with the rest of the program but don't start web server
        SAFE_MODE = True
        main()