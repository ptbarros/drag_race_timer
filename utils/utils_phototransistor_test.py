# Modified Phototransistor Test Program for Direct Connection
# For PT334-6C phototransistors with Collector to GND, Emitter to ADC
from machine import Pin, I2C, ADC
import time
import config

# Define ADC pins to use for sensors
ADC_PINS = [
    {"name": "Lane 1 Start", "pin": 26},  # ADC0
    {"name": "Lane 1 Finish", "pin": 27}, # ADC1
#    {"name": "Lane 2 Start", "pin": 26},  # Reusing ADC0 for testing
#    {"name": "Lane 2 Finish", "pin": 27}  # Reusing ADC1 for testing
]

# Threshold for detecting blocked vs unblocked
# Adjust based on your observed values (somewhere between blocked and unblocked readings)
BLOCKED_THRESHOLD = 7500  # Values above this are considered blocked

# Try to import display controller
try:
    from display.controller import DisplayController, DISPLAY_LIBRARIES_AVAILABLE
    from display.basic_display import BasicDisplay
except ImportError:
    print("Display libraries not available - falling back to console output only")
    DISPLAY_LIBRARIES_AVAILABLE = False

# Initialize the LED strip if available
try:
    from led.ws2812b import init as init_leds, pixels_set, pixels_show, pixels_fill
    from led.animations import display_startup_sequence
    LED_AVAILABLE = True
    init_leds()
    # Set all LEDs to off initially
    pixels_fill(config.BLACK)
    pixels_show()
except ImportError:
    LED_AVAILABLE = False
    print("LED libraries not available")

# Initialize display controller if available
display_controller = None
if DISPLAY_LIBRARIES_AVAILABLE and config.DISPLAY_ENABLED:
    try:
        # Initialize I2C
        i2c = I2C(0, sda=Pin(config.I2C_SDA_PIN), scl=Pin(config.I2C_SCL_PIN))
        
        # Scan I2C bus
        devices = i2c.scan()
        print(f"Found {len(devices)} I2C devices: {[hex(d) for d in devices]}")
        
        display_controller = DisplayController(config.NUM_LANES)
        print("Display controller initialized")
    except Exception as e:
        print(f"Error initializing display controller: {e}")
        display_controller = None

def initialize_sensors():
    """Initialize ADC pins for sensors"""
    sensors = []
    
    for sensor_info in ADC_PINS:
        try:
            adc_pin = ADC(Pin(sensor_info["pin"]))
            sensors.append({
                "name": sensor_info["name"],
                "adc_pin": adc_pin,
                "value": 0,
                "is_blocked": False,
                "last_is_blocked": False,
                "transitions": 0,
                "blocked_count": 0,
                "unblocked_count": 0,
                "last_transition": time.ticks_ms(),
                "min_value": 65535,
                "max_value": 0
            })
            print(f"Initialized {sensor_info['name']} on ADC{sensor_info['pin']}")
        except Exception as e:
            print(f"Error initializing ADC for {sensor_info['name']}: {e}")
    
    return sensors

def check_sensor_values(sensors):
    """Read and report sensor values"""
    current_time = time.ticks_ms()
    
    for i, sensor in enumerate(sensors):
        # Read analog value
        value = sensor["adc_pin"].read_u16()
        sensor["value"] = value
        
        # Update min/max values
        if value < sensor["min_value"]:
            sensor["min_value"] = value
        if value > sensor["max_value"]:
            sensor["max_value"] = value
        
        # Determine if blocked based on threshold
        is_blocked = value > BLOCKED_THRESHOLD
        sensor["is_blocked"] = is_blocked
        
        # Check if blocked state has changed
        if is_blocked != sensor["last_is_blocked"]:
            transition_time = time.ticks_diff(current_time, sensor["last_transition"])
            state_text = "BLOCKED" if is_blocked else "UNBLOCKED"
            
            print(f"{sensor['name']}: {state_text} (was {transition_time}ms) - Value: {value}")
            
            # Update LED if available
            if LED_AVAILABLE and i < 2:  # Just use for first two sensors
                lane_id = i + 1  # Lane 1 or 2
                led_index = config.LED_MAPPING[lane_id]["red" if is_blocked else "green"]
                # Turn on the appropriate LED
                pixels_fill(config.BLACK)  # Clear all LEDs
                pixels_set(led_index, config.RED if is_blocked else config.GREEN)
                pixels_show()
            
            # Update transition counter
            sensor["transitions"] += 1
            
            # Update blocked/unblocked counters
            if is_blocked:
                sensor["blocked_count"] += 1
            else:
                sensor["unblocked_count"] += 1
            
            # Update last transition time
            sensor["last_transition"] = current_time
            
            # Update last blocked state
            sensor["last_is_blocked"] = is_blocked
        
        # Always update the display with latest values
        lane_idx = i // 2  # Lane 1 or Lane 2
        display_idx = i % 2  # Primary (Start) or Secondary (Finish)
        
        if display_controller and lane_idx < len(display_controller.displays):
            # Scale analog value to display
            scaled_value = min(9999, value // 7)
            
            if display_idx == 0 and display_controller.displays[lane_idx][0]:
                display_controller.displays[lane_idx][0].show_number(scaled_value, decimal_places=0)
                
                # Small display to show state
                if len(display_controller.displays[lane_idx]) > 1 and display_controller.displays[lane_idx][1]:
                    display_controller.displays[lane_idx][1].show_text("BLCK" if is_blocked else "OPEN")
            elif display_idx == 1 and len(display_controller.displays[lane_idx]) > 1 and display_controller.displays[lane_idx][1]:
                display_controller.displays[lane_idx][1].show_number(scaled_value, decimal_places=0)

def print_sensor_summary(sensors):
    """Print a summary of sensor readings"""
    print("\n--- SENSOR SUMMARY ---")
    print("Sensor Name      | Current | Value  | Min     | Max     | Transitions")
    print("----------------- --------- ------- --------- --------- ------------")
    
    for sensor in sensors:
        current = "BLOCKED" if sensor["is_blocked"] else "OPEN   "
        value_str = f"{sensor['value']:<7}"
        min_str = f"{sensor['min_value']:<7}"
        max_str = f"{sensor['max_value']:<7}"
        
        print(f"{sensor['name']:<15} | {current} | {value_str} | {min_str} | {max_str} | {sensor['transitions']:<11}")
    
    print("----------------------------------------------------------")
    print(f"Current threshold: {BLOCKED_THRESHOLD} (values above = BLOCKED)")
    print("----------------------------------------------------------")

def main():
    print("Initializing Modified Phototransistor Test Program...")
    print("Using DIRECT CONNECTION: Collector to GND, Emitter to ADC")
    
    # Initialize sensors
    sensors = initialize_sensors()
    
    # Display startup animation if LEDs available
    if LED_AVAILABLE:
        display_startup_sequence()
    
    print("\nSensor test running. Press Ctrl+C to stop.")
    print(f"Current threshold: {BLOCKED_THRESHOLD} (values above = BLOCKED)")
    print("Block and unblock sensors to see readings.\n")
    
    last_summary_time = time.ticks_ms()
    
    # Main loop
    try:
        while True:
            # Check sensor values
            check_sensor_values(sensors)
            
            # Print summary every 5 seconds
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_summary_time) >= 5000:
                print_sensor_summary(sensors)
                last_summary_time = current_time
            
            # Small delay to avoid excessive polling
            time.sleep_ms(50)
    
    except KeyboardInterrupt:
        print("\nTest program stopped by user.")
        # Print final summary
        print_sensor_summary(sensors)
        # Turn off all LEDs
        if LED_AVAILABLE:
            pixels_fill(config.BLACK)
            pixels_show()
        # Clear displays
        if display_controller:
            display_controller.clear_all()

if __name__ == "__main__":
    main()