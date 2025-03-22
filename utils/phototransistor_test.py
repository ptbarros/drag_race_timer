import time
import machine

# Configuration
ADC_PIN_LANE1_START = 26      # ADC0
ADC_PIN_LANE1_FINISH = 27     # ADC1
THRESHOLD = 800              # Threshold for determining BLOCKED or OPEN
UPDATE_INTERVAL_MS = 500      # How often to update the display (ms)
SAMPLE_COUNT = 5              # Number of samples to average
SAMPLE_INTERVAL_MS = 20       # Time between samples (ms)

# Initialize the ADC pins
lane1_start_sensor = machine.ADC(ADC_PIN_LANE1_START)
lane1_finish_sensor = machine.ADC(ADC_PIN_LANE1_FINISH)

# Initialize tracking variables
start_min = 65535
start_max = 0
finish_min = 65535
finish_max = 0
start_transitions = 0
finish_transitions = 0
last_start_blocked = False
last_finish_blocked = False
last_console_update = 0
last_value_list_update = 0

# Initialize value lists for averaging
start_values = []
finish_values = []

def get_status_text(value, threshold=THRESHOLD):
    """Return BLOCKED or OPEN based on the value and threshold"""
    return "BLOCKED" if value > threshold else "OPEN"

def print_sensor_summary(start_value, finish_value, start_min, start_max, finish_min, finish_max, 
                         start_transitions, finish_transitions, threshold):
    """Print a formatted summary of sensor readings to the console"""
    print("\n--- SENSOR SUMMARY ---")
    print("Sensor Name      | Current | Value  | Min     | Max     | Transitions")
    print("----------------- --------- ------- --------- --------- ------------")
    
    start_status = get_status_text(start_value, threshold)
    finish_status = get_status_text(finish_value, threshold)
    
    print(f"Lane 1 Start    | {start_status:<7} | {int(start_value):<7} | {start_min:<7} | {start_max:<7} | {start_transitions:<10}")
    print(f"Lane 1 Finish   | {finish_status:<7} | {int(finish_value):<7} | {finish_min:<7} | {finish_max:<7} | {finish_transitions:<10}")
    
    print("----------------------------------------------------------")
    print(f"Current threshold: {threshold} (values above = BLOCKED)")
    print("----------------------------------------------------------")

def update_min_max(value, current_min, current_max):
    """Update minimum and maximum values"""
    return min(value, current_min), max(value, current_max)

def main():
    global start_min, start_max, finish_min, finish_max
    global start_transitions, finish_transitions
    global last_start_blocked, last_finish_blocked
    global last_console_update, last_value_list_update
    global start_values, finish_values
    
    print("Starting phototransistor test (console-only version). Press Ctrl+C to exit.")
    print(f"Using threshold value of {THRESHOLD}")
    
    try:
        while True:
            current_time = time.ticks_ms()
            
            # Get current sensor readings
            start_value = lane1_start_sensor.read_u16()
            finish_value = lane1_finish_sensor.read_u16()
            
            # Add values to lists for averaging (limit frequency of updates)
            if time.ticks_diff(current_time, last_value_list_update) > SAMPLE_INTERVAL_MS:
                start_values.append(start_value)
                finish_values.append(finish_value)
                # Keep lists at SAMPLE_COUNT length
                if len(start_values) > SAMPLE_COUNT:
                    start_values.pop(0)
                if len(finish_values) > SAMPLE_COUNT:
                    finish_values.pop(0)
                last_value_list_update = current_time
            
            # Calculate current averages
            start_avg = sum(start_values) / len(start_values) if start_values else start_value
            finish_avg = sum(finish_values) / len(finish_values) if finish_values else finish_value
            
            # Update min and max values
            start_min, start_max = update_min_max(start_value, start_min, start_max)
            finish_min, finish_max = update_min_max(finish_value, finish_min, finish_max)
            
            # Check for transitions
            current_start_blocked = start_value > THRESHOLD
            current_finish_blocked = finish_value > THRESHOLD
            
            if current_start_blocked != last_start_blocked:
                start_transitions += 1
                last_start_blocked = current_start_blocked
                
            if current_finish_blocked != last_finish_blocked:
                finish_transitions += 1
                last_finish_blocked = current_finish_blocked
            
            # Print to console periodically (every second)
            if time.ticks_diff(current_time, last_console_update) > 1000:
                print_sensor_summary(
                    start_avg, finish_avg,
                    start_min, start_max,
                    finish_min, finish_max,
                    start_transitions, finish_transitions,
                    THRESHOLD
                )
                last_console_update = current_time
                
            # Small delay to prevent hogging CPU
            time.sleep_ms(10)
            
    except KeyboardInterrupt:
        print("\nTest terminated by user")

if __name__ == "__main__":
    main()