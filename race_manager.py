# Race Manager for Raspberry Pi Pico Drag Race Controller
from machine import Pin
import time
import config
from led.ws2812b import pixels_fill

# Create a global race_manager instance that will be initialized in main.py
race_manager = None

class RaceManager:
    def __init__(self, lanes, start_btn_pin, reset_btn_pin, display_controller=None):
        self.lanes = lanes
        self.start_btn = Pin(start_btn_pin, Pin.IN, Pin.PULL_UP)
        self.reset_btn = Pin(reset_btn_pin, Pin.IN, Pin.PULL_UP)
        self.display_controller = display_controller
        self.race_started = False
        self.tree_running = False
        self.tree_sequence_complete = False
        self.current_stage = None
        self.next_stage_time = 0
        self.race_start_time = 0
        self.race_timeout = config.RACE_TIMEOUT
        self.place_counter = 1  # Counter for assigning finishing positions
        
        # Button state tracking
        self.last_start_btn_state = 1
        self.last_reset_btn_state = 1
        self.player_btn_states = [1] * len(lanes)  # Initial state for all player buttons
        
        # Button event queue
        self.button_events = []

        # Add staging variables
        self.all_staged = False
        self.staging_start_time = None
        self.staging_delay = None

        # Set the global race_manager reference
        global race_manager
        race_manager = self

    def reset_race(self):
        """Reset the race to its initial state"""
        for lane in self.lanes:
            lane.reset()
        print("Race reset.")
        self.race_started = False
        self.tree_running = False
        self.tree_sequence_complete = False
        self.current_stage = None
        self.next_stage_time = 0
        self.race_start_time = 0
        self.place_counter = 1
        
        # Clear button event queue
        self.button_events.clear()
        
        # Clear all displays
        if self.display_controller:
            self.display_controller.clear_all()
            
            # Show ready status on displays
            for i in range(len(self.lanes)):
                self.display_controller.show_ready(i)
                
        # Reset staging variables
        self.all_staged = False
        self.staging_start_time = None
        self.staging_delay = None

    def start_race(self):
        """Start a new race with the light sequence"""
        if not self.race_started and not self.tree_running:
            print("Starting tree sequence...")
            
            # Keep staging lights on if enabled, but reset other lights
            for lane in self.lanes:
                for light in ["amber1", "amber2", "amber3", "green", "red"]:
                    lane.set_light(light, 0)
            
            # Add a delay before starting the sequence
            print(f"{config.PRE_START_DELAY//1000}-second delay before starting...")
            time.sleep_ms(config.PRE_START_DELAY)
            print("Starting light sequence now!")
            
            # Set up the first stage
            self.current_stage = "amber1_on"
            self.next_stage_time = time.ticks_add(time.ticks_ms(), 0)  # Start immediately
            
            self.tree_running = True
            self.race_started = True
            self.race_start_time = time.ticks_ms()

    def update_tree(self):
        """Update the light tree sequence"""
        if not self.tree_running or self.current_stage is None:
            # Check if staging delay has elapsed before starting race
            if not self.race_started and self.all_staged and self.staging_start_time is not None:
                if time.ticks_diff(time.ticks_ms(), self.staging_start_time) >= self.staging_delay:
                    # Clear staging timer
                    self.staging_start_time = None
                    self.staging_delay = None
                    
                    # Start race sequence
                    self.start_race()
            return

        current_time = time.ticks_ms()
        
        # Process the current stage if it's time
        if time.ticks_diff(current_time, self.next_stage_time) >= 0:
            self.process_stage()

    def process_stage(self):
        """Process the current stage of the light sequence"""
        print(f"Processing stage: {self.current_stage}")
        
        if self.current_stage == "amber1_on":
            self.set_light_on("amber1")
            self.current_stage = "amber1_off"
            self.next_stage_time = time.ticks_add(time.ticks_ms(), config.LIGHT_ON_DURATION)
            
        elif self.current_stage == "amber1_off":
            self.set_light_off("amber1")
            self.current_stage = "amber2_on"
            self.next_stage_time = time.ticks_add(time.ticks_ms(), config.TRANSITION_DELAY)
            
        elif self.current_stage == "amber2_on":
            self.set_light_on("amber2")
            self.current_stage = "amber2_off"
            self.next_stage_time = time.ticks_add(time.ticks_ms(), config.LIGHT_ON_DURATION)
            
        elif self.current_stage == "amber2_off":
            self.set_light_off("amber2")
            self.current_stage = "amber3_on"
            self.next_stage_time = time.ticks_add(time.ticks_ms(), config.TRANSITION_DELAY)
            
        elif self.current_stage == "amber3_on":
            self.set_light_on("amber3")
            self.current_stage = "amber3_off"
            self.next_stage_time = time.ticks_add(time.ticks_ms(), config.LIGHT_ON_DURATION)
         
        elif self.current_stage == "amber3_off":
            self.set_light_off("amber3")
            self.current_stage = "green_on"
            self.next_stage_time = time.ticks_add(time.ticks_ms(), config.TRANSITION_DELAY)
            
        elif self.current_stage == "green_on":
            self.set_light_on("green")
            print("Green light! GO!")
            self.current_stage = None  # Changed from "sequence_complete" to None to stop processing
            self.tree_sequence_complete = True
            
            # Set start time for all lanes when green light comes on
            current_time = time.ticks_ms()
            for lane in self.lanes:
                if lane.start_time is None:
                    lane.start_time = current_time

    def set_light_on(self, light_name):
        """Turn on a specific light in all lanes"""
        print(f"Setting {light_name} ON at {time.ticks_ms()}")
        for lane in self.lanes:
            lane.set_light(light_name, 1)
            print(f"Lane {lane.lane_id} {light_name} set to {lane.get_light_state(light_name)}")

    def set_light_off(self, light_name):
        """Turn off a specific light in all lanes"""
        print(f"Setting {light_name} OFF at {time.ticks_ms()}")
        for lane in self.lanes:
            lane.set_light(light_name, 0)
            print(f"Lane {lane.lane_id} {light_name} set to {lane.get_light_state(light_name)}")
    
    def is_light_on(self, light_name):
        """Check if a specific light is on in the first lane"""
        # Just check the first lane since all lanes' lights should be synchronized
        if self.lanes:
            return self.lanes[0].get_light_state(light_name) == 1
        return False

    def reset_all_lights(self):
        """Turn off all lights in all lanes"""
        # Turn off all LEDs in the strip
        pixels_fill(config.BLACK)
        
        # Reset lane light states
        for lane in self.lanes:
            for light in lane.tree_state:
                lane.tree_state[light] = 0

    def check_player_buttons(self):
        """Check all player buttons for state changes"""
        for i, lane in enumerate(self.lanes):
            current_state = lane.player_btn.value()
            
            # Button just pressed (transition from 1 to 0)
            if current_state == 0 and self.player_btn_states[i] == 1:
                if not self.race_started and config.STAGING_LIGHTS_ENABLED:
                    # If race hasn't started, activate staging lights
                    if not lane.prestaged:
                        lane.prestaged = True
                        lane.set_light("prestage", 1)
                        print(f"Lane {lane.lane_id}: Pre-staged")
                        
                    # After pre-staged, move to staged
                    elif not lane.staged:
                        lane.staged = True
                        lane.set_light("stage", 1)
                        print(f"Lane {lane.lane_id}: Staged")
                        
                        # Check if all lanes are staged
                        self.check_all_staged()
                
                # MODIFIED: Allow button press once race has started, regardless of tree sequence state
                # This allows false starts during amber lights
                elif self.race_started and not config.RELEASE_TO_START_MODE:
                    # Queue the button press for processing
                    self.button_events.append(('player', i))
                    print(f"Lane {lane.lane_id}: Player button press detected and queued")
                    
            # Button just released (transition from 0 to 1)
            elif current_state == 1 and self.player_btn_states[i] == 0:
                # In release-to-start mode, fire servo on button release
                if self.race_started and config.RELEASE_TO_START_MODE:
                    self.button_events.append(('player', i))
                    print(f"Lane {lane.lane_id}: Player button release detected and queued")
                    
                # If button released before race starts, turn off staging lights
                elif not self.race_started:
                    if lane.staged or lane.prestaged:
                        print(f"Lane {lane.lane_id}: Staging cancelled")
                        lane.staged = False
                        lane.prestaged = False
                        lane.set_light("stage", 0)
                        lane.set_light("prestage", 0)
            
            # Update last known state
            self.player_btn_states[i] = current_state
        
        # Process any queued button events
        self.process_button_events()    
    
    def check_all_staged(self):
        """Check if all lanes are staged and start sequence timer if needed"""
        if self.race_started or not config.STAGING_AUTO_SEQUENCE:
            return
            
        # Check if all lanes are staged
        all_staged = True
        for lane in self.lanes:
            if not lane.staged:
                all_staged = False
                break
                
        # If all lanes are now staged and we haven't started the timer yet
        if all_staged and not self.all_staged:
            self.all_staged = True
            print("All lanes staged! Starting delay sequence...")
            self.staging_start_time = time.ticks_ms()
            
            # Set random staging delay
            import random
            self.staging_delay = random.randint(
                config.STAGING_DELAY_MIN, 
                config.STAGING_DELAY_MAX
            )
            print(f"Staging delay: {self.staging_delay}ms")
    
    def process_button_events(self):
        """Process any queued button events"""
        # Process up to 5 events per cycle (to prevent getting stuck if many events queue up)
        for _ in range(min(5, len(self.button_events))):
            if not self.button_events:
                break
                
            event_type, lane_index = self.button_events.pop(0)  # Get first event (FIFO)
            
            if event_type == 'player' and not self.lanes[lane_index].gate_released:
                print(f"Lane {self.lanes[lane_index].lane_id}: Processing queued button press")
                self.lanes[lane_index].fire_servo()
    
    def check_start_line_sensors(self):
        """Check all start line sensors"""
        for lane in self.lanes:
            lane.check_start_line()

    def check_finish_line_sensors(self):
        """Check all finish line sensors"""
        for lane in self.lanes:
            # Only check for finish if not already finished
            if not lane.finish_line_broken:
                lane.check_finish()
                
                # Assign place position if lane just finished and doesn't have a place yet
                if lane.finish_line_broken and not lane.false_start and lane.place is None:
                    lane.place = self.place_counter
                    self.place_counter += 1
                    
                    # Update display with position and time
                    if self.display_controller:
                        self.display_controller.show_position(lane.lane_id - 1, lane.place)
                        if lane.finish_time is not None:
                            self.display_controller.show_time(lane.lane_id - 1, lane.finish_time)

    def is_race_complete(self):
        """Check if the race is complete"""
        # Check if race has timed out
        if time.ticks_diff(time.ticks_ms(), self.race_start_time) > self.race_timeout:
            print("Race timed out!")
            return True
            
        # Check if all lanes have finished
        all_finished = True
        for lane in self.lanes:
            if not lane.finish_line_broken and not lane.false_start:
                all_finished = False
                break
        
        # If all lanes either red-lighted or finished, race is complete
        return all_finished

    def get_position_text(self, lane):
        """Get the position text for a lane (1st, 2nd, 3rd, etc.)"""
        if lane.false_start:
            return "RED LIGHT!"
        elif lane.place is None:
            return "DNF"  # Did Not Finish
        elif lane.place == 1:
            return "1st!"
        elif lane.place == 2:
            return "2nd"
        elif lane.place == 3:
            return "3rd"
        else:
            return f"{lane.place}th"

    def monitor_race(self):
        """Monitor the progress of the current race"""
        if self.race_started:
            # Check start line sensors to detect red lights or reaction times
            self.check_start_line_sensors()
            
            # Check finish line sensors
            self.check_finish_line_sensors()
            
            # Check if auxiliary LED functions are available
            has_aux_leds = hasattr(config, 'AUX_LED_MAPPING')
            
            # Update reaction time displays for lanes that have broken the start beam
            for lane in self.lanes:
                if lane.reaction_time is not None and self.display_controller:
                    self.display_controller.show_reaction_time(lane.lane_id - 1, lane.reaction_time)
                
                # Update false start indicators using auxiliary LEDs
                if has_aux_leds and lane.false_start:
                    # Import only if we need it (to avoid circular imports)
                    from led.aux_lighting import set_false_start_indicator
                    set_false_start_indicator(lane.lane_id, True)
            
            # Check if race is complete
            if self.is_race_complete():
                print("Race complete!")
                
                # Calculate reaction times for false starts before displaying results
                for lane in self.lanes:
                    lane.calculate_reaction_time()
                    
                    # Update reaction time display if display controller exists
                    if lane.reaction_time is not None and self.display_controller:
                        self.display_controller.show_reaction_time(lane.lane_id - 1, lane.reaction_time)
                
                # Display results
                print("Results:")
                for lane in self.lanes:
                    position_text = self.get_position_text(lane)
                    print(f"Lane {lane.lane_id}: {position_text}")
                    
                    # Set winner indicator using auxiliary LEDs
                    if has_aux_leds and lane.place == 1:
                        # Import only if we need it (to avoid circular imports)
                        from led.aux_lighting import set_lane_winner
                        set_lane_winner(lane.lane_id, True)
                    
                    # Display race time (if available)
                    if lane.finish_time is not None:
                        print(f"  Race time: {lane.finish_time} ms")
                        # Update final time on display for lanes that finished properly
                        if not lane.false_start and self.display_controller:
                            self.display_controller.show_time(lane.lane_id - 1, lane.finish_time)
                    elif lane.false_start and lane.finish_line_broken:
                        # For false starts that still finished, show their finish time
                        print(f"  Race time: {lane.finish_time} ms (DQ)")
                    else:
                        print("  Race time: Did not finish")
                    
                    # Display reaction time
                    if lane.reaction_time is not None:
                        if lane.reaction_time < 0 and lane.false_start:
                            print(f"  Reaction time: {abs(lane.reaction_time)} ms EARLY")
                        else:
                            print(f"  Reaction time: {lane.reaction_time} ms")
                
                # End race state
                self.tree_running = False
                self.race_started = False
                return True  # Race is done
        return False  # Race still in progress

    def update_servos(self):
        """Update all servo positions (non-blocking)"""
        for lane in self.lanes:
            lane.update_servo()