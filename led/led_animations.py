# LED animation functions for WS2812B LED strip
import time
import config
from led.ws2812b import pixels_set, pixels_show, pixels_fill

def display_startup_sequence():
    """Display a startup animation on the LED strip"""
    # Clear all LEDs
    pixels_fill(config.BLACK)
    pixels_show()
    
    # Define lane colors for the animation
    lane_colors = [config.RED, config.BLUE, config.GREEN, config.YELLOW, config.WHITE]
    
    # Animate each lane sequentially
    for lane_idx in range(1, config.NUM_LANES + 1):
        # Get the starting LED for this lane from the mapping
        if lane_idx in config.LED_MAPPING:
            # Use first LED (amber1) as reference for lane's starting position
            start_led = config.LED_MAPPING[lane_idx]["amber1"]
            lane_color = lane_colors[(lane_idx - 1) % len(lane_colors)]
            
            # Light up this lane's LEDs one by one
            for i in range(config.LEDS_PER_LANE):
                pixels_set(start_led + i, lane_color)
                pixels_show()
                time.sleep_ms(50)  # Faster animation to accommodate all lanes
    
    # Flash all separators to highlight lane divisions
    for lane_idx in range(1, config.NUM_LANES):
        # Calculate separator start position (end of one lane to start of next)
        separator_start = (lane_idx * config.LEDS_PER_LANE) + ((lane_idx - 1) * config.SEPARATION_LEDS)
        
        # Light up separator LEDs
        for i in range(config.SEPARATION_LEDS):
            pixels_set(separator_start + i, config.WHITE)
        
    pixels_show()
    time.sleep_ms(500)
    
    # Flash all lanes 3 times in their respective colors
    for _ in range(3):
        # Turn off all LEDs
        pixels_fill(config.BLACK)
        pixels_show()
        time.sleep_ms(200)
        
        # Turn on all lane LEDs with their respective colors
        for lane_idx in range(1, config.NUM_LANES + 1):
            if lane_idx in config.LED_MAPPING:
                start_led = config.LED_MAPPING[lane_idx]["amber1"]
                lane_color = lane_colors[(lane_idx - 1) % len(lane_colors)]
                
                for i in range(config.LEDS_PER_LANE):
                    pixels_set(start_led + i, lane_color)
        
        pixels_show()
        time.sleep_ms(200)
    
    # Test each light in each lane with all colors
    colors = [config.RED, config.YELLOW, config.GREEN, config.BLUE, config.WHITE]
    
    # For each lane
    for lane_idx in range(1, config.NUM_LANES + 1):
        if lane_idx in config.LED_MAPPING:
            # Get this lane's LEDs
            lane_leds = [config.LED_MAPPING[lane_idx][light] for light in ["amber1", "amber2", "amber3", "green", "red"]]
            
            # Clear this lane
            for led in lane_leds:
                pixels_set(led, config.BLACK)
            pixels_show()
            time.sleep_ms(100)
            
            # Test each color
            for color in colors:
                # Light all LEDs in this lane with test color
                for led in lane_leds:
                    pixels_set(led, color)
                pixels_show()
                time.sleep_ms(50)  # Shorter delay to keep animation length reasonable
                
                # Clear for next color
                for led in lane_leds:
                    pixels_set(led, config.BLACK)
                pixels_show()
                time.sleep_ms(50)
    
    # Return to all off
    pixels_fill(config.BLACK)
    pixels_show()

def win_animation(lane_id):
    """Display a winning animation for the specified lane"""
    # Find the LEDs for this lane
    lane_leds = []
    if lane_id in config.LED_MAPPING:
        lane_leds = [config.LED_MAPPING[lane_id][light] for light in config.LED_MAPPING[lane_id]]
    
    # Flash the lane's LEDs in green 5 times
    for _ in range(5):
        # Turn on all LEDs for this lane
        for led in lane_leds:
            pixels_set(led, config.GREEN)
        pixels_show()
        time.sleep_ms(200)
        
        # Turn off all LEDs for this lane
        for led in lane_leds:
            pixels_set(led, config.BLACK)
        pixels_show()
        time.sleep_ms(200)

def false_start_animation(lane_id):
    """Display a false start animation for the specified lane"""
    # Find the red LED for this lane
    if lane_id in config.LED_MAPPING and "red" in config.LED_MAPPING[lane_id]:
        red_led = config.LED_MAPPING[lane_id]["red"]
        
        # Flash the red LED 5 times
        for _ in range(5):
            pixels_set(red_led, config.RED)
            pixels_show()
            time.sleep_ms(200)
            
            pixels_set(red_led, config.BLACK)
            pixels_show()
            time.sleep_ms(200)
        
        # Leave the red LED on
        pixels_set(red_led, config.RED)
        pixels_show()
