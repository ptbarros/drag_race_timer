# Helper functions for Raspberry Pi Pico Drag Race Controller

def format_time(time_ms, decimal_places=3):
    """Format time in milliseconds to a readable string"""
    time_sec = time_ms / 1000.0
    
    if decimal_places == 2:
        return f"{time_sec:.2f}s"
    elif decimal_places == 3:
        return f"{time_sec:.3f}s"
    else:
        return f"{time_sec:.1f}s"

def is_false_start(reaction_time):
    """Determine if a reaction time is a false start (negative value)"""
    return reaction_time < 0

def scan_i2c(i2c_id=0, sda_pin=None, scl_pin=None):
    """Scan I2C bus and return list of device addresses"""
    from machine import I2C, Pin
    import config
    
    if sda_pin is None:
        sda_pin = config.I2C_SDA_PIN
    if scl_pin is None:
        scl_pin = config.I2C_SCL_PIN
    
    # Initialize I2C
    print(f"Scanning I2C{i2c_id} on SDA={sda_pin}, SCL={scl_pin}")
    i2c = I2C(i2c_id, sda=Pin(sda_pin), scl=Pin(scl_pin))
    
    # Scan bus
    devices = i2c.scan()
    print(f"Found {len(devices)} I2C devices:")
    for device in devices:
        print(f"  Device at address 0x{device:02x} (decimal: {device})")
    
    return devices

# (Add any additional functions below this)