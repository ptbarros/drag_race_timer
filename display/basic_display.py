# basic_display.py - A minimal HT16K33 display driver using direct I2C commands
# This bypasses the problematic library and talks directly to the hardware

from machine import I2C
import time

# HT16K33 Commands
CMD_SYSTEM_SETUP = 0x20
CMD_DISPLAY_SETUP = 0x80
CMD_BRIGHTNESS = 0xE0

# Character definitions for 7-segment display (segments a-g + decimal point)
CHARS = {
    '0': 0x3F, '1': 0x06, '2': 0x5B, '3': 0x4F, '4': 0x66,
    '5': 0x6D, '6': 0x7D, '7': 0x07, '8': 0x7F, '9': 0x6F,
    'A': 0x77, 'B': 0x7C, 'C': 0x39, 'D': 0x5E, 'E': 0x79,
    'F': 0x71, 'H': 0x76, 'L': 0x38, 'O': 0x3F, 'P': 0x73,
    'S': 0x6D, 'T': 0x78, 'U': 0x3E, 'Y': 0x6E, '-': 0x40,
    ' ': 0x00, '_': 0x08, 'R': 0x50, 'N': 0x54, '.': 0x80
}

class BasicDisplay:
    def __init__(self, i2c, address=0x70):
        self.i2c = i2c
        self.address = address
        self.buffer = bytearray(16)  # 8 two-byte words = 16 bytes
        
        # Initialize display
        self._write_cmd(CMD_SYSTEM_SETUP | 1)  # Turn on oscillator
        self._write_cmd(CMD_DISPLAY_SETUP | 1)  # Turn on display
        self.set_brightness(8)
        self.clear()
    
    def _write_cmd(self, cmd):
        """Write a single command byte to the device"""
        self.i2c.writeto(self.address, bytes([cmd]))
    
    def _write_buffer(self):
        """Write the entire buffer to the device"""
        self.i2c.writeto(self.address, bytes([0]) + self.buffer)  # First byte is register address (0)
    
    def set_brightness(self, level):
        """Set brightness level (0-15)"""
        level = max(0, min(15, level))
        self._write_cmd(CMD_BRIGHTNESS | level)
    
    def clear(self):
        """Clear the display buffer"""
        for i in range(16):
            self.buffer[i] = 0
        self._write_buffer()
    
    def _set_digit(self, pos, pattern, dot=False):
        """Set a specific digit (0-3) with the given pattern"""
        if 0 <= pos < 4:
            if dot:
                pattern |= 0x80  # Set decimal point
            # Map positions - this mapping might need adjustment for your specific display
            pos_map = {0: 0, 1: 2, 2: 6, 3: 8}  # These are word addresses in the HT16K33
            self.buffer[pos_map[pos]] = pattern
            self.buffer[pos_map[pos] + 1] = 0  # Clear the high byte
    
    def show_text(self, text):
        """Show text on the display"""
        self.clear()
        
        # Process text to handle decimal points
        processed = []
        for i, char in enumerate(text):
            if char == '.' and i > 0:
                # Attach decimal point to previous character
                processed[-1] = (processed[-1][0], True)
            else:
                processed.append((char, False))
        
        # Right-justify and truncate to 4 characters
        while len(processed) < 4:
            processed.insert(0, (' ', False))
        if len(processed) > 4:
            processed = processed[-4:]
        
        # Display each character
        for i, (char, dot) in enumerate(processed):
            pattern = CHARS.get(char, 0)
            self._set_digit(i, pattern, dot)
        
        self._write_buffer()
    
    def show_number(self, number, decimal_places=2):
        """Show a number with the specified decimal places"""
        if decimal_places > 0:
            text = "{:.{dp}f}".format(number, dp=decimal_places)
        else:
            text = str(int(number))
        
        self.show_text(text)
