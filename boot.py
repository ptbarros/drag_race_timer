# boot.py - Runs before main.py to set up system
import machine
import gc

# Increase CPU frequency for better WiFi stability
machine.freq(240000000)  # Set to maximum 240MHz

# Run aggressive garbage collection to free memory
gc.collect()

# Print status
print(f"CPU frequency set to {machine.freq()/1000000}MHz")
print(f"Free memory: {gc.mem_free()} bytes")

# Disable LED for now (you may not need this)
from machine import Pin
led = Pin("LED", Pin.OUT)
led.off()

# Print boot banner
print("\n=== Pico W Race Controller ===")
print("boot.py executed - system initialized")