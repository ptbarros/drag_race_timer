from machine import Pin, ADC
import time

# Digital pins
start_pin = Pin(0, Pin.IN)  # Lane 1 Start
finish_pin = Pin(1, Pin.IN)  # Lane 1 Finish

# ADC pins
start_adc = ADC(Pin(26))  # ADC0
finish_adc = ADC(Pin(27))  # ADC1

# Test loop
print("Starting phototransistor test...")
print("Block and unblock sensors to see readings")
print("Press Ctrl+C to exit")

try:
    while True:
        # Read values
        start_digital = start_pin.value()
        finish_digital = finish_pin.value()
        start_analog = start_adc.read_u16()
        finish_analog = finish_adc.read_u16()
        
        # Print values
        print(f"Start: Digital={start_digital}, Analog={start_analog}")
        print(f"Finish: Digital={finish_digital}, Analog={finish_analog}")
        print("-" * 40)
        
        # Short delay
        time.sleep(0.5)
        
except KeyboardInterrupt:
    print("Test complete")