import time
import machine

# Configuration
DIG_PIN_LANE1_START = 0       # GPIO 0 for digital start sensor
DIG_PIN_LANE1_FINISH = 1      # GPIO 1 for digital finish sensor
LOG_FILENAME = "digital_sensor_log.txt"  # Filename for logging

# Initialize pins with pull-up resistors (like in the Derby Timer)
# This is the key difference from your previous setup
lane1_start = machine.Pin(DIG_PIN_LANE1_START, machine.Pin.IN, machine.Pin.PULL_UP)
lane1_finish = machine.Pin(DIG_PIN_LANE1_FINISH, machine.Pin.IN, machine.Pin.PULL_UP)

# Initialize tracking variables
start_transitions = 0
finish_transitions = 0
last_start_value = None
last_finish_value = None
last_log_update = 0

def log_to_file(message):
    """Append message to log file"""
    try:
        with open(LOG_FILENAME, "a") as log_file:
            log_file.write(f"{time.localtime()}: {message}\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")

def main():
    global start_transitions, finish_transitions
    global last_start_value, last_finish_value, last_log_update
    
    print(f"Starting digital phototransistor test (Derby-style). Press Ctrl+C to exit.")
    print(f"Using internal pull-ups on pins: Start={DIG_PIN_LANE1_START}, Finish={DIG_PIN_LANE1_FINISH}")
    print(f"Log file: {LOG_FILENAME}")
    
    # Clear log file at start
    try:
        with open(LOG_FILENAME, "w") as log_file:
            log_file.write(f"=== Digital Phototransistor Test Started at {time.localtime()} ===\n")
            log_file.write(f"Digital pins with PULL_UP: Start={DIG_PIN_LANE1_START}, Finish={DIG_PIN_LANE1_FINISH}\n")
            log_file.write(f"BEAM BROKEN = HIGH (1), BEAM CLEAR = LOW (0)\n")
    except Exception as e:
        print(f"Error initializing log file: {e}")
    
    try:
        # Initialize last values
        last_start_value = lane1_start.value()
        last_finish_value = lane1_finish.value()
        
        while True:
            current_time = time.ticks_ms()
            
            # Read current values
            start_value = lane1_start.value()
            finish_value = lane1_finish.value()
            
            # Check for transitions (beam broken or unbroken)
            if start_value != last_start_value:
                start_transitions += 1
                status = "BROKEN" if start_value == 1 else "CLEAR"
                transition_msg = f"[TRANSITION] Start sensor: {last_start_value} -> {start_value} (Beam {status})"
                print(transition_msg)
                log_to_file(transition_msg)
                last_start_value = start_value
                
            if finish_value != last_finish_value:
                finish_transitions += 1
                status = "BROKEN" if finish_value == 1 else "CLEAR"
                transition_msg = f"[TRANSITION] Finish sensor: {last_finish_value} -> {finish_value} (Beam {status})"
                print(transition_msg)
                log_to_file(transition_msg)
                last_finish_value = finish_value
            
            # Print status periodically (every second)
            if time.ticks_diff(current_time, last_log_update) > 1000:
                start_status = "BROKEN" if start_value == 1 else "CLEAR"
                finish_status = "BROKEN" if finish_value == 1 else "CLEAR"
                
                status_msg = f"""
--- SENSOR STATUS ---
Sensor Name      | State   | Value | Transitions
----------------- --------- ------- ------------
Lane 1 Start     | {start_status:<7} | {start_value}     | {start_transitions}
Lane 1 Finish    | {finish_status:<7} | {finish_value}     | {finish_transitions}
------------------------------------------
"""
                print(status_msg)
                log_to_file(status_msg)
                last_log_update = current_time
                
            # Small delay to prevent hogging CPU
            time.sleep_ms(50)
            
    except KeyboardInterrupt:
        print("\nTest terminated by user")
        print(f"Check {LOG_FILENAME} for complete test data")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Add a delay before exit to allow reading any final output
        print("Waiting 5 seconds before exit...")
        time.sleep(5)

if __name__ == "__main__":
    main()