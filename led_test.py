import time
import array
from machine import Pin
import rp2

# WS2812B pin - Using the same pin as in your config
WS2812B_PIN = 28

# Number of LEDs on your strip - Adjust this to match your actual setup
NUM_LEDS = 37  # Based on your config for 4 lanes + separators

# Colors (in GRB order for WS2812B)
RED = 0x00FF00     # GRB: G=00, R=FF, B=00
GREEN = 0xFF0000   # GRB: G=FF, R=00, B=00
BLUE = 0x0000FF    # GRB: G=00, R=00, B=FF
YELLOW = 0xFFFF00  # GRB: G=FF, R=FF, B=00
WHITE = 0xFFFFFF   # White
BLACK = 0x000000   # Off

# PIO state machine for WS2812B
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()

# Initialize the state machine with the ws2812 program
sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(WS2812B_PIN))
sm.active(1)

# Create the LED array
ar = array.array("I", [0 for _ in range(NUM_LEDS)])

def pixels_show():
    """Update the LED strip with current values"""
    sm.put(ar, 8)
    time.sleep_ms(10)

def pixels_set(i, color):
    """Set a specific LED to the given color"""
    if 0 <= i < NUM_LEDS:
        ar[i] = color

def pixels_fill(color):
    """Set all LEDs to the same color"""
    for i in range(NUM_LEDS):
        ar[i] = color

def test_individual_leds():
    """Test each LED individually"""
    print("Testing each LED individually...")
    
    # Turn off all LEDs
    pixels_fill(BLACK)
    pixels_show()
    time.sleep(1)
    
    # Light each LED one by one
    for i in range(NUM_LEDS):
        pixels_fill(BLACK)  # Clear all
        pixels_set(i, WHITE)
        pixels_show()
        print(f"LED {i} should be lit")
        time.sleep(0.5)
    
    # Turn off all LEDs
    pixels_fill(BLACK)
    pixels_show()
    time.sleep(1)

def test_lane_4_leds():
    """Special test for Lane 4 LEDs (based on your config)"""
    print("\nSpecifically testing Lane 4 LEDs...")
    
    # First, get the LED indices for Lane 4 from your config
    # Based on your shared config file
    lane_4_leds = {
        "prestage": 21,
        "stage": 22,
        "amber1": 23,
        "amber2": 24,
        "amber3": 25,
        "green": 26,
        "red": 27
    }
    
    # Turn off all LEDs
    pixels_fill(BLACK)
    pixels_show()
    time.sleep(1)
    
    # Test each Lane 4 LED with different colors
    colors = [RED, GREEN, BLUE, YELLOW, WHITE]
    
    for light_name, led_idx in lane_4_leds.items():
        print(f"Testing Lane 4 {light_name} (LED {led_idx})")
        
        for color in colors:
            pixels_fill(BLACK)  # Clear all
            pixels_set(led_idx, color)
            pixels_show()
            time.sleep(0.5)
    
    # Turn off all LEDs
    pixels_fill(BLACK)
    pixels_show()

def color_wipe(color):
    """Fill the strip one LED at a time with the specified color"""
    print(f"Color wipe with color value: {color}")
    for i in range(NUM_LEDS):
        pixels_set(i, color)
        pixels_show()
        time.sleep(0.05)

def chase(color):
    """Create a theater chase effect with the specified color"""
    print(f"Theater chase with color value: {color}")
    for j in range(10):  # Do 10 cycles
        for q in range(3):
            for i in range(0, NUM_LEDS, 3):
                if i + q < NUM_LEDS:
                    pixels_set(i + q, color)
            pixels_show()
            time.sleep(0.05)
            for i in range(0, NUM_LEDS, 3):
                if i + q < NUM_LEDS:
                    pixels_set(i + q, 0)

def test_color_range():
    """Test a range of LEDs with different colors"""
    print("\nTesting all LEDs with color cycling...")
    
    # Cycle through colors
    color_wipe(RED)
    color_wipe(GREEN)
    color_wipe(BLUE)
    color_wipe(YELLOW)
    color_wipe(WHITE)
    color_wipe(BLACK)  # Turn off all LEDs
    
    # Do a theater chase
    chase(RED)
    chase(GREEN)
    chase(BLUE)
    
    # Turn off all LEDs
    pixels_fill(BLACK)
    pixels_show()

def main():
    print("Starting WS2812B LED test...")
    print(f"Testing {NUM_LEDS} LEDs on pin {WS2812B_PIN}")
    
    # Run the tests
    test_individual_leds()
    test_lane_4_leds()
    test_color_range()
    
    print("Test complete. All LEDs should have been tested.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Test interrupted by user")
        # Turn off all LEDs before exiting
        pixels_fill(BLACK)
        pixels_show()