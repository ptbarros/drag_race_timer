# WS2812B LED strip controller for Raspberry Pi Pico
import array, time
from machine import Pin
import rp2
import config

# State machine and LED array (global variables)
led_sm = None
led_array = None

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    """PIO assembly program for driving WS2812B LED strips"""
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

def init():
    """Initialize the WS2812B LED controller"""
    global led_sm, led_array
    # Create the StateMachine
    led_sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(config.WS2812B_PIN))
    led_sm.active(1)
    
    # Create the LED array
    led_array = array.array("I", [0 for _ in range(config.NUM_LEDS)])
    
    # Turn off all LEDs initially
    pixels_fill(config.BLACK)
    pixels_show()
    print(f"WS2812B LED strip initialized with {config.NUM_LEDS} LEDs on pin {config.WS2812B_PIN}")

def pixels_show():
    """Update the LED strip with current values"""
    led_sm.put(led_array, 8)
    time.sleep_ms(10)

def pixels_set(i, color):
    """Set a specific LED to the given color"""
    if 0 <= i < config.NUM_LEDS:
        led_array[i] = color

def pixels_fill(color):
    """Set all LEDs to the same color"""
    for i in range(len(led_array)):
        led_array[i] = color
        
def set_lane_light(lane_id, light_name, state):
    """Set a light in a specific lane to on/off state"""
    if lane_id in config.LED_MAPPING and light_name in config.LED_MAPPING[lane_id]:
        led_index = config.LED_MAPPING[lane_id][light_name]
        if state:
            pixels_set(led_index, config.TREE_COLORS[light_name])
        else:
            pixels_set(led_index, config.TREE_COLORS["off"])
        pixels_show()
