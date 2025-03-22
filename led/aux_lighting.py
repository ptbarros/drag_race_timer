# Auxiliary lighting functions for additional LEDs
import time
import config
from led.ws2812b import pixels_set, pixels_show

def get_lane_indicator_leds(lane_id):
    """Get all indicator LEDs for a specific lane"""
    led_indices = []
    
    # Check for the three indicator LEDs
    for i in range(1, 4):  # Looking for indicator1, indicator2, indicator3
        led_name = f"lane{lane_id}_indicator{i}"
        if led_name in config.AUX_LED_MAPPING:
            led_indices.append(config.AUX_LED_MAPPING[led_name])
    
    return led_indices

def set_display_indicator(lane_id, color):
    """Set the display indicator LED for a lane"""
    led_name = f"lane{lane_id}_display"
    if led_name in config.AUX_LED_MAPPING:
        led_index = config.AUX_LED_MAPPING[led_name]
        pixels_set(led_index, color)
        pixels_show()

def set_lane_winner(lane_id, is_winner=True):
    """Show winning animation for a lane using all three indicator LEDs"""
    # Get all indicator LEDs for this lane
    led_indices = get_lane_indicator_leds(lane_id)
    
    if not led_indices:
        print(f"Warning: No indicator LEDs found for lane {lane_id}")
        return
    
    if is_winner:
        # Blink green on all the indicator LEDs
        for _ in range(5):
            # Turn on all indicators
            for led_index in led_indices:
                pixels_set(led_index, config.GREEN)
            pixels_show()
            time.sleep_ms(200)
            
            # Turn off all indicators
            for led_index in led_indices:
                pixels_set(led_index, config.BLACK)
            pixels_show()
            time.sleep_ms(200)
    else:
        # Turn off all indicator LEDs
        for led_index in led_indices:
            pixels_set(led_index, config.BLACK)
        pixels_show()

def set_false_start_indicator(lane_id, state=True):
    """Set the false start indicator for a lane using all three indicator LEDs"""
    # Get all indicator LEDs for this lane
    led_indices = get_lane_indicator_leds(lane_id)
    
    if not led_indices:
        print(f"Warning: No indicator LEDs found for lane {lane_id}")
        return
    
    if state:
        # Set all indicators to red
        for led_index in led_indices:
            pixels_set(led_index, config.RED)
    else:
        # Turn off all indicators
        for led_index in led_indices:
            pixels_set(led_index, config.BLACK)
    
    pixels_show()

def illuminate_sensors(state=True):
    """Turn on/off LEDs for sensor illumination"""
    color = config.WHITE if state else config.BLACK
    
    # Set all sensor illumination LEDs
    for led_name, led_index in config.AUX_LED_MAPPING.items():
        if "sensor" in led_name:
            pixels_set(led_index, color)
    
    pixels_show()

def illuminate_spacers(color=None):
    """Set spacer LEDs to a specific color or turn them off"""
    if color is None:
        color = config.BLACK
    
    # Set all spacer LEDs
    for led_name, led_index in config.AUX_LED_MAPPING.items():
        if "spacer" in led_name:
            pixels_set(led_index, color)
    
    pixels_show()

def clear_all_aux_leds():
    """Turn off all auxiliary LEDs"""
    for _, led_index in config.AUX_LED_MAPPING.items():
        pixels_set(led_index, config.BLACK)
    pixels_show()