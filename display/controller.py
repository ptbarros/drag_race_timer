# Display Controller for Raspberry Pi Pico Drag Race Controller
from machine import I2C, Pin
import time
import config

# Import display libraries - add a try-except block to handle missing libraries gracefully
try:
    from display.basic_display import BasicDisplay
    DISPLAY_LIBRARIES_AVAILABLE = True
except ImportError:
    print("Warning: Display libraries not available. Install necessary libraries for display support.")
    DISPLAY_LIBRARIES_AVAILABLE = False

class DisplayController:
    def __init__(self, num_lanes):
        print("DisplayController: Initializing...")
        self.displays = []  # Will be a 2D array: [lane][display_index]
        self.num_lanes = num_lanes
        
        # Add display cycling variables
        self.cycle_enabled = config.DISPLAY_CYCLE_ENABLED
        self.cycle_interval = config.DISPLAY_CYCLE_INTERVAL
        self.cycle_last_change = [0] * num_lanes  # Last change time for each lane
        self.cycle_current_mode = [0] * num_lanes  # Current display mode for each lane
                                                   # 0 = reaction time, 1 = status
        
        print(f"DisplayController: DISPLAY_ENABLED={config.DISPLAY_ENABLED}, LIBRARIES_AVAILABLE={DISPLAY_LIBRARIES_AVAILABLE}")
        
        if not config.DISPLAY_ENABLED or not DISPLAY_LIBRARIES_AVAILABLE:
            print("DisplayController: Displays disabled or libraries not available")
            return
            
        try:
            # Initialize I2C0 on GPIO 20 (SDA) and GPIO 21 (SCL)
            print(f"DisplayController: Initializing I2C on SDA={config.I2C_SDA_PIN}, SCL={config.I2C_SCL_PIN}")
            i2c = I2C(0, sda=Pin(config.I2C_SDA_PIN), scl=Pin(config.I2C_SCL_PIN))
            
            # Scan I2C bus and find available display addresses
            discovered_addresses = i2c.scan()
            print(f"DisplayController: I2C scan found {len(discovered_addresses)} devices: {[hex(d) for d in discovered_addresses]}")
            
            # Calculate number of displays we need
            total_displays_needed = num_lanes * config.DISPLAYS_PER_LANE
            
            # Check if we have enough displays
            if len(discovered_addresses) < total_displays_needed:
                print(f"WARNING: Found only {len(discovered_addresses)} displays, but need {total_displays_needed} for {num_lanes} lanes with {config.DISPLAYS_PER_LANE} displays per lane")
                print("Some lanes may not have all required displays")
            
            # Auto-assign addresses to lanes
            assigned_addresses = []
            
            # If DISPLAY_ADDRESSES is defined in config, use it as a priority order
            # This allows users to still control ordering if needed
            if hasattr(config, 'DISPLAY_ADDRESSES') and config.DISPLAY_ADDRESSES:
                # Use configured addresses as priority list, but only if they exist
                for addr in config.DISPLAY_ADDRESSES:
                    if addr in discovered_addresses:
                        assigned_addresses.append(addr)
                        
                # Add any additional discovered addresses not in the config list
                for addr in discovered_addresses:
                    if addr not in assigned_addresses:
                        assigned_addresses.append(addr)
            else:
                # Just use discovered addresses in the order found
                assigned_addresses = discovered_addresses
            
            print(f"DisplayController: Using displays with addresses: {[hex(a) for a in assigned_addresses]}")
            
            # Initialize displays grouped by lane
            for lane_id in range(1, num_lanes + 1):
                lane_displays = []
                
                for disp_idx in range(config.DISPLAYS_PER_LANE):
                    # Calculate the address index
                    addr_idx = (lane_id - 1) * config.DISPLAYS_PER_LANE + disp_idx
                    
                    if addr_idx < len(assigned_addresses):
                        address = assigned_addresses[addr_idx]
                        
                        # Create and configure the display
                        try:
                            # Create a basic display instance
                            display = BasicDisplay(i2c, address)
                            display.set_brightness(config.DISPLAY_BRIGHTNESS)
                            lane_displays.append(display)
                            print(f"Initialized display {disp_idx+1} for Lane {lane_id} at address 0x{address:02x}")
                        except Exception as e:
                            print(f"Error initializing display {disp_idx+1} for Lane {lane_id}: {e}")
                            lane_displays.append(None)  # Add None placeholder to maintain array structure
                    else:
                        print(f"No display available for display {disp_idx+1} on lane {lane_id}")
                        lane_displays.append(None)
                
                self.displays.append(lane_displays)
            
        except Exception as e:
            print(f"Error initializing displays: {e}")
            self.displays = []
            
    def show_message(self, lane_index, message, display_index=None):
        """
        Show a text message on a lane's display(s)
        If display_index is None, show on all displays for the lane
        """
        if not config.DISPLAY_ENABLED or not self.displays or lane_index >= len(self.displays):
            return
            
        # Get the displays for this lane
        lane_displays = self.displays[lane_index]
        
        if display_index is not None:
            # Update specific display if requested
            if display_index < len(lane_displays) and lane_displays[display_index] is not None:
                try:
                    lane_displays[display_index].show_text(message)
                except Exception as e:
                    print(f"Error updating display {display_index} for lane {lane_index}: {e}")
        else:
            # Update all displays for this lane
            for i, display in enumerate(lane_displays):
                if display is not None:
                    try:
                        display.show_text(message)
                    except Exception as e:
                        print(f"Error updating display {i} for lane {lane_index}: {e}")
            
    def show_time(self, lane_index, time_ms):
        """Show race time on a lane's primary display"""
        if not config.DISPLAY_ENABLED or not self.displays or lane_index >= len(self.displays):
            return
                
        time_sec = time_ms / 1000.0
        
        # Format time with appropriate decimal places
        try:
            if time_sec < 10:
                # For shorter times, show 3 decimal places
                if len(self.displays[lane_index]) > 0 and self.displays[lane_index][0] is not None:
                    self.displays[lane_index][0].show_number(time_sec, decimal_places=3)
            else:
                # For longer times, show 2 decimal places
                if len(self.displays[lane_index]) > 0 and self.displays[lane_index][0] is not None:
                    self.displays[lane_index][0].show_number(time_sec, decimal_places=2)
                        
            # Show "RACE" on second display if available
            if len(self.displays[lane_index]) > 1 and self.displays[lane_index][1] is not None:
                self.displays[lane_index][1].show_text("RACE")
                    
            # Reset cycle timing to start the cycle again
            self.cycle_last_change[lane_index] = time.ticks_ms()
            self.cycle_current_mode[lane_index] = 1  # Start with status
        except Exception as e:
            print(f"Error updating time displays for lane {lane_index}: {e}")
    
    def _centered_position_str(self, position):
        """Create a centered position string (for 4-digit display)"""
        # For single digit positions (1-9)
        if position < 10:
            # Add leading and trailing spaces to center: [space][space][digit][space]
            return f"  {position} "
        # For double digit positions (10-99)
        else:
            # Add leading spaces to right-align: [space][space][digit][digit]
            return f"  {position}"
            
    def show_position(self, lane_index, position):
        """Show race position as a centered number on a lane's display"""
        if not config.DISPLAY_ENABLED or not self.displays or lane_index >= len(self.displays):
            return
            
        # Format position as a centered number
        pos_str = self._centered_position_str(position)
            
        try:
            # If only one display per lane, show position briefly and then 
            # let cycling show race time alternating with position
            if len(self.displays[lane_index]) == 1 and self.displays[lane_index][0] is not None:
                self.displays[lane_index][0].show_text(pos_str)
            else:
                # Show position on primary display if in dual display mode
                if len(self.displays[lane_index]) > 0 and self.displays[lane_index][0] is not None:
                    self.displays[lane_index][0].show_text(pos_str)
                    
                # Show "POS" on second display to indicate position is showing
                if len(self.displays[lane_index]) > 1 and self.displays[lane_index][1] is not None:
                    self.displays[lane_index][1].show_text("POS")
                    
            # Reset cycle timing to start the cycle again
            self.cycle_last_change[lane_index] = time.ticks_ms()
            self.cycle_current_mode[lane_index] = 1  # Start with status
        except Exception as e:
            print(f"Error updating position displays for lane {lane_index}: {e}")
    
    def update_reaction_display(self, lane_index, reaction_time_ms):
        """Update just the reaction time display"""
        if len(self.displays[lane_index]) <= 1 or self.displays[lane_index][1] is None:
            return
            
        reaction_time_sec = abs(reaction_time_ms) / 1000.0
        
        try:
            # Show the reaction time on the second display
            self.displays[lane_index][1].show_number(reaction_time_sec, decimal_places=3)
        except Exception as e:
            print(f"Error updating reaction time display for lane {lane_index}: {e}")
            
    def show_reaction_time(self, lane_index, reaction_time_ms):
        """Show reaction time on a lane's secondary display"""
        if not config.DISPLAY_ENABLED or not self.displays or lane_index >= len(self.displays):
            return
            
        # Only proceed if we have a second display
        if len(self.displays[lane_index]) <= 1 or self.displays[lane_index][1] is None:
            return
            
        # Update primary display for early starts
        if reaction_time_ms < 0:
            # For false starts, show "ERLY" label on main display
            if self.displays[lane_index][0] is not None:
                self.displays[lane_index][0].show_text("ERLY")
        
        # Reset cycle timing
        self.cycle_last_change[lane_index] = time.ticks_ms()
        self.cycle_current_mode[lane_index] = 0  # Start with reaction time
        
        # Update the reaction time display
        self.update_reaction_display(lane_index, reaction_time_ms)
            
    def show_ready(self, lane_index):
        """Show 'ready' status on display"""
        if not config.DISPLAY_ENABLED or not self.displays or lane_index >= len(self.displays):
            return
            
        # Show "RDY-" on primary display
        if len(self.displays[lane_index]) > 0 and self.displays[lane_index][0] is not None:
            try:
                self.displays[lane_index][0].show_text("RDY-")
            except Exception as e:
                print(f"Error updating ready display for lane {lane_index}: {e}")
        
        # Show "STBY" on second display if available
        if len(self.displays[lane_index]) > 1 and self.displays[lane_index][1] is not None:
            try:
                self.displays[lane_index][1].show_text("STBY")
            except Exception as e:
                print(f"Error updating standby display for lane {lane_index}: {e}")
        
    def show_false_start(self, lane_index):
        """Show false start indication"""
        if not config.DISPLAY_ENABLED or not self.displays or lane_index >= len(self.displays):
            return
            
        # Show "FOUL" on primary display
        if len(self.displays[lane_index]) > 0 and self.displays[lane_index][0] is not None:
            try:
                self.displays[lane_index][0].show_text("FOUL")
            except Exception as e:
                print(f"Error updating false start display for lane {lane_index}: {e}")
        
        # Show "RED-" on second display if available
        if len(self.displays[lane_index]) > 1 and self.displays[lane_index][1] is not None:
            try:
                self.displays[lane_index][1].show_text("RED-")
            except Exception as e:
                print(f"Error updating false start display for lane {lane_index}: {e}")
    
    def update_displays(self):
        """Update all displays based on cycling logic"""
        if not config.DISPLAY_ENABLED or not self.displays:
            return
        
        current_time = time.ticks_ms()
        
        # Check each lane for cycling
        for lane_idx in range(len(self.displays)):
            # Get the relevant lane object
            from race_manager import race_manager  # Import here to avoid circular import
            
            lane = None
            for l in race_manager.lanes:
                if l.lane_id - 1 == lane_idx:
                    lane = l
                    break
            
            if lane is None:
                continue
            
            # Skip if not enough time passed for cycling
            if time.ticks_diff(current_time, self.cycle_last_change[lane_idx]) < self.cycle_interval:
                continue
                
            # Reset cycle timer
            self.cycle_last_change[lane_idx] = current_time
            
            # Toggle display mode
            self.cycle_current_mode[lane_idx] = (self.cycle_current_mode[lane_idx] + 1) % 2
            
            # If we have only one display per lane
            if len(self.displays[lane_idx]) == 1 and self.displays[lane_idx][0] is not None:
                primary_display = self.displays[lane_idx][0]
                
                # Cycle between time and position on the single display
                if lane.finish_time is not None and lane.place is not None:
                    if self.cycle_current_mode[lane_idx] == 0:
                        # Show race time
                        time_sec = lane.finish_time / 1000.0
                        if time_sec < 10:
                            primary_display.show_number(time_sec, decimal_places=3)
                        else:
                            primary_display.show_number(time_sec, decimal_places=2)
                    else:
                        # Show position as centered number
                        primary_display.show_text(self._centered_position_str(lane.place))
                elif lane.false_start:
                    # For false starts, alternate between "FOUL" and "RED-"
                    if self.cycle_current_mode[lane_idx] == 0:
                        primary_display.show_text("FOUL")
                    else:
                        primary_display.show_text("RED-")
                        
            # If we have dual displays per lane, use the existing logic
            elif len(self.displays[lane_idx]) > 1 and self.displays[lane_idx][1] is not None:
                secondary_display = self.displays[lane_idx][1]
                
                       # Update display based on current mode
                if self.cycle_current_mode[lane_idx] == 0:
                    # Show reaction time if available
                    if lane.reaction_time is not None:
                        self.update_reaction_display(lane_idx, lane.reaction_time)
                    elif lane.false_start:
                        secondary_display.show_text("RED-")
                    else:
                        secondary_display.show_text("STBY")
                else:
                    # Show status info
                    if lane.false_start:
                        secondary_display.show_text("FOUL")
                    elif lane.place is not None:
                        # Show the position number in dual display mode
                        if lane.place < 10:
                            secondary_display.show_text(f" {lane.place}  ")  # Centered single digit
                        else:
                            secondary_display.show_text(f"{lane.place}  ")   # Double digit
                    elif lane.reaction_time is not None:
                        secondary_display.show_text("RACE")
                    else:
                        secondary_display.show_text("STBY")         
                

    
    def update_secondary_displays(self):
        """Update displays based on cycling logic - maintains backward compatibility"""
        if not self.cycle_enabled or not self.displays:
            return
        
        # Use the new generic display update method
        self.update_displays()
        
    def clear_all(self):
        """Clear all displays"""
        if not config.DISPLAY_ENABLED or not self.displays:
            return
            
        for lane_displays in self.displays:
            for display in lane_displays:
                if display is not None:
                    try:
                        display.clear()
                    except Exception as e:
                        print(f"Error clearing display: {e}")