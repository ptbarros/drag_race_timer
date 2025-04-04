# web/server.py - With enhanced diagnostics for troubleshooting API issues
import network
import socket
import time
import json
import gc
import _thread
from machine import Pin
import os

# Network configuration - configurable in config.py
HOME_SSID = None
HOME_PASSWORD = None
AP_SSID = 'DragRaceTimer'
AP_PASSWORD = 'race123456'
AP_IP = '192.168.4.1'

# LED to indicate WiFi status
led = Pin("LED", Pin.OUT)

# Race manager reference
race_manager = None

# HTML templates
html_files = {}

# Server state
server_running = False
server_thread = None
current_ip = None  # Will store the active IP address

def load_configuration():
    """Load web server configuration from config.py if available"""
    global HOME_SSID, HOME_PASSWORD, AP_SSID, AP_PASSWORD, AP_IP
    
    try:
        import config
        
        # Try to get home network settings
        if hasattr(config, 'HOME_WIFI_SSID'):
            HOME_SSID = config.HOME_WIFI_SSID
        elif hasattr(config, 'WIFI_SSID') and not hasattr(config, 'AP_WIFI_SSID'):
            HOME_SSID = config.WIFI_SSID
            
        if hasattr(config, 'HOME_WIFI_PASSWORD'):
            HOME_PASSWORD = config.HOME_WIFI_PASSWORD
        elif hasattr(config, 'WIFI_PASSWORD') and not hasattr(config, 'AP_WIFI_PASSWORD'):
            HOME_PASSWORD = config.WIFI_PASSWORD
            
        # Get fallback AP settings
        if hasattr(config, 'AP_WIFI_SSID'):
            AP_SSID = config.AP_WIFI_SSID
        elif hasattr(config, 'WIFI_SSID') and hasattr(config, 'AP_WIFI_SSID'):
            AP_SSID = config.WIFI_SSID
            
        if hasattr(config, 'AP_WIFI_PASSWORD'):
            AP_PASSWORD = config.AP_WIFI_PASSWORD
        elif hasattr(config, 'WIFI_PASSWORD') and hasattr(config, 'AP_WIFI_SSID'):
            AP_PASSWORD = config.WIFI_PASSWORD
            
        if hasattr(config, 'WIFI_IP'):
            AP_IP = config.WIFI_IP
            
        print(f"Loaded network configuration from config.py")
        
        # Print what we're using
        if HOME_SSID:
            print(f"Will try to connect to home network: {HOME_SSID}")
        print(f"Fallback AP: {AP_SSID}")
        
    except Exception as e:
        print(f"Error loading configuration: {e}")
        print("Using default network configuration")

def load_html_files():
    """Load HTML files into memory"""
    try:
        print("Current directory:", os.getcwd())
        print("Files in web directory:", os.listdir('web'))
        
        # Load main HTML files 
        with open('./web/index.html', 'r') as file:
            content = file.read()
            html_files['index'] = content
            print(f"Loaded index.html, size: {len(content)} bytes")
        
        # Try to load test.html if it exists
        try:
            with open('./web/test.html', 'r') as file:
                content = file.read()
                html_files['test'] = content
                print(f"Loaded test.html, size: {len(content)} bytes")
        except:
            print("test.html not found, it will be generated dynamically")
            
        # Use same file for race.html for now
        html_files['race'] = html_files['index']
        print("HTML files loaded successfully")
        
    except OSError as e:
        print(f"Error loading HTML files: {e}")
        print("Using fallback HTML templates...")
        # Create basic HTML if files don't exist
        html_files['index'] = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Drag Race Timer</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                h1 { color: #333; }
                .button {
                    background-color: #4CAF50;
                    border: none;
                    color: white;
                    padding: 15px 32px;
                    text-align: center;
                    display: inline-block;
                    font-size: 16px;
                    margin: 4px 2px;
                    cursor: pointer;
                    border-radius: 4px;
                }
                .button-reset {
                    background-color: #f44336;
                }
                .button-start {
                    background-color: #4CAF50;
                }
                .race-status {
                    background-color: #f0f0f0;
                    padding: 10px;
                    margin-top: 10px;
                    border-radius: 4px;
                }
                .lane {
                    background-color: #f9f9f9;
                    padding: 10px;
                    margin-top: 10px;
                    border-radius: 4px;
                }
            </style>
        </head>
        <body>
            <h1>Drag Race Timer</h1>
            <div>
                <button class="button button-start" onclick="startRace()">Start Race</button>
                <button class="button button-reset" onclick="resetRace()">Reset Race</button>
            </div>
            
            <div class="race-status">
                <h2>Race Status</h2>
                <div id="status">Ready</div>
                <div id="lightSequence">Waiting to start</div>
            </div>
            
            <div id="lanes"></div>
            
            <script>
                // Update status periodically
                setInterval(updateStatus, 500);
                
                function startRace() {
                    fetch('/api/start')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('status').innerHTML = 'Race started!';
                        });
                }
                
                function resetRace() {
                    fetch('/api/reset')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('status').innerHTML = 'Race reset';
                        });
                }
                
                function updateStatus() {
                    fetch('/api/status')
                        .then(response => response.json())
                        .then(data => {
                            // Update race status
                            if (data.race_started) {
                                document.getElementById('status').innerHTML = 'Race in progress';
                            } else {
                                document.getElementById('status').innerHTML = 'Ready';
                            }
                            
                            // Update light sequence
                            if (data.tree_running) {
                                document.getElementById('lightSequence').innerHTML = 
                                    'Light sequence: ' + (data.light_sequence || 'Running');
                            }
                            
                            // Update lanes
                            let lanesHtml = '';
                            for (let lane of data.lanes || []) {
                                let status = lane.false_start ? 'FALSE START' : 
                                             (lane.place === 1 ? 'WINNER!' : 
                                             (lane.place ? 'Place: ' + lane.place : 'Ready'));
                                             
                                let reactionTime = lane.reaction_time !== null ? 
                                    (lane.reaction_time / 1000).toFixed(3) + 's' : 'N/A';
                                    
                                let finishTime = lane.finish_time !== null ? 
                                    (lane.finish_time / 1000).toFixed(3) + 's' : 'N/A';
                                
                                lanesHtml += `
                                    <div class="lane">
                                        <h3>Lane ${lane.lane_id}</h3>
                                        <p>Status: ${status}</p>
                                        <p>Reaction Time: ${reactionTime}</p>
                                        <p>Finish Time: ${finishTime}</p>
                                    </div>
                                `;
                            }
                            
                            document.getElementById('lanes').innerHTML = lanesHtml;
                        });
                }
            </script>
        </body>
        </html>
        """
        html_files['race'] = html_files['index']  # Use same basic template for now

def connect_to_home_network():
    """Try to connect to home WiFi network"""
    global current_ip
    
    # Check if we have home network credentials
    if not HOME_SSID:
        print("No home network SSID configured, skipping home network connection")
        return False
    
    print(f"\nAttempting to connect to home network: {HOME_SSID}")
    
    # Initialize station interface
    sta_if = network.WLAN(network.STA_IF)
    
    # Activate station interface
    sta_if.active(True)
    time.sleep(1)
    
    # Try to connect to the home network
    try:
        print(f"Connecting to {HOME_SSID}...")
        sta_if.connect(HOME_SSID, HOME_PASSWORD)
        
        # Wait for connection with timeout
        max_wait = 10  # 10 seconds timeout - shorter to avoid waiting too long
        while max_wait > 0:
            if sta_if.isconnected():
                break
            max_wait -= 1
            print("Waiting for WiFi connection...")
            
            # Blink LED to show connection attempt
            led.toggle()
            time.sleep(1)
        
        # Check if connected
        if sta_if.isconnected():
            current_ip = sta_if.ifconfig()[0]
            print(f"Connected to {HOME_SSID}!")
            print(f"IP address: {current_ip}")
            
            # Turn LED on solid to indicate connected
            led.on()
            return True
        else:
            print(f"Failed to connect to {HOME_SSID}")
            sta_if.active(False)  # Turn off station interface
            time.sleep(1)
            return False
            
    except Exception as e:
        print(f"Error connecting to home network: {e}")
        try:
            sta_if.active(False)  # Turn off station interface
        except:
            pass
        time.sleep(1)
        return False

def setup_access_point():
    """Set up WiFi access point with proven reliable approach"""
    global current_ip
    
    # Initialize the WLAN interface in access point mode
    wlan = network.WLAN(network.AP_IF)
    
    # Disable it first for a clean start
    print("Deactivating any existing AP...")
    wlan.active(False)
    time.sleep(1)
    
    # Configure the access point - simple reliable configuration
    print(f"Configuring access point: SSID={AP_SSID}, password={AP_PASSWORD}")
    wlan.config(ssid=AP_SSID, password=AP_PASSWORD)
    
    # Activate the interface
    print("Activating access point...")
    wlan.active(True)
    time.sleep(2)  # Allow time for activation
    
    # Wait for it to become active
    max_wait = 10
    while max_wait > 0:
        if wlan.active():
            break
        max_wait -= 1
        print('Waiting for WiFi access point to be active...')
        time.sleep(1)
    
    if wlan.active():
        print(f'Access Point active: {AP_SSID}')
        current_ip = AP_IP
        
        print(f'IP address: {current_ip}')
        return True
    else:
        print('Failed to establish access point')
        return False

def handle_request(client_socket):
    """Handle incoming HTTP requests with enhanced debugging"""
    try:
        # Get request data
        try:
            request_data = client_socket.recv(1024)
            if not request_data:
                return
            
            # Decode the request with enhanced error handling
            try:
                request = request_data.decode('utf-8')
            except UnicodeError:
                print("Warning: Could not decode request as UTF-8. Using ISO-8859-1")
                request = request_data.decode('iso-8859-1')
                
        except Exception as e:
            print(f"Error receiving request: {e}")
            return
        
        # Parse the request line
        try:
            request_lines = request.split('\n')
            if not request_lines:
                print("Empty request received")
                return
                
            request_line = request_lines[0]
            parts = request_line.split(' ')
            
            if len(parts) < 2:
                print(f"Invalid request line: {request_line}")
                return
                
            method, path = parts[0], parts[1]
            print(f"Request: {method} {path}")
            
            # Extract headers into a dictionary
            headers = {}
            for line in request_lines[1:]:
                line = line.strip()
                if line and ': ' in line:
                    key, value = line.split(': ', 1)
                    headers[key] = value
            
            # Print headers for debugging (first 5 lines)
            print("Headers:")
            header_count = 0
            for key, value in headers.items():
                if header_count < 5:
                    print(f"  {key}: {value}")
                    header_count += 1
            
        except Exception as e:
            print(f"Error parsing request: {e}")
            # Try to extract path directly
            if '/' in request:
                path = request[request.index('/'):request.index(' HTTP/') if ' HTTP/' in request else -1]
                method = "GET"  # Assume GET
                print(f"Recovered path: {path}")
                headers = {}
            else:
                send_response(client_socket, 400, 'text/plain', 'Bad Request')
                return
        
        # API endpoints
        if path.startswith('/api/'):
            print(f"API request: {path}")
            handle_api_request(client_socket, method, path, headers, request)
            return
        
        # Serve control page
        elif path == '/control.html':
            try:
                if race_manager:
                    # Fetch current status
                    status = {
                        'race_started': race_manager.race_started,
                        'tree_running': race_manager.tree_running,
                        'light_sequence': race_manager.current_stage
                    }
                    
                    # Generate lane HTML
                    
                    # Generate lane HTML with a simpler approach
                    lanes_html = ""
                    print(f"Processing {len(race_manager.lanes)} lanes for display")

                    # First generate the HTML for each lane separately
                    lane_htmls = []
                    for i, lane in enumerate(race_manager.lanes):
                        lane_id = lane.lane_id
                        print(f"Generating HTML for Lane {lane_id} (index {i})")
                        
                        # Determine lane status
                        status_text = 'Ready'
                        status_class = ''
                        
                        if lane.false_start:
                            status_text = 'FALSE START'
                            status_class = 'false-start'
                        elif lane.place == 1:
                            status_text = 'WINNER!'
                            status_class = 'lane-winner'
                        elif lane.place:
                            status_text = f'Place: {lane.place}'
                        elif lane.staged and lane.prestaged:
                            status_text = 'Staged'
                        elif lane.prestaged:
                            status_text = 'Pre-staged'
                        
                        # Format times nicely
                        reaction_time = f"{(lane.reaction_time / 1000):.3f}s" if lane.reaction_time is not None else "N/A"
                        finish_time = f"{(lane.finish_time / 1000):.3f}s" if lane.finish_time is not None else "N/A"
                        
                        # Use a simple string for each lane
                        lane_html = f"""<div class="lane">
                    <h3>Lane {lane_id}</h3>
                    <div class="lane-status"><span>Status:</span><span class="{status_class}">{status_text}</span></div>
                    <div class="lane-status"><span>Reaction Time:</span><span>{reaction_time}</span></div>
                    <div class="lane-status"><span>Finish Time:</span><span>{finish_time}</span></div>
                    </div>"""
                        
                        lane_htmls.append(lane_html)
                        print(f"Added lane {lane_id} HTML ({len(lane_html)} chars)")

                    # Now combine all lane HTMLs together
                    lanes_html = "\n".join(lane_htmls)
                    print(f"Total lanes HTML length: {len(lanes_html)} chars")
                    
#                     # Inside the handle_request function, replace the lane HTML generation section:
# 
#                     # Generate lane HTML with debugging
#                     lanes_html = ""
#                     print(f"Processing {len(race_manager.lanes)} lanes for display")
#                     for i, lane in enumerate(race_manager.lanes):
#                         lane_id = lane.lane_id
#                         print(f"Generating HTML for Lane {lane_id} (index {i})")
#                         
#                         # Determine lane status
#                         status_text = 'Ready'
#                         status_class = ''
#                         
#                         if lane.false_start:
#                             status_text = 'FALSE START'
#                             status_class = 'false-start'
#                         elif lane.place == 1:
#                             status_text = 'WINNER!'
#                             status_class = 'lane-winner'
#                         elif lane.place:
#                             status_text = f'Place: {lane.place}'
#                         elif lane.staged and lane.prestaged:
#                             status_text = 'Staged'
#                         elif lane.prestaged:
#                             status_text = 'Pre-staged'
#                         
#                         # Format times nicely
#                         reaction_time = f"{(lane.reaction_time / 1000):.3f}s" if lane.reaction_time is not None else "N/A"
#                         finish_time = f"{(lane.finish_time / 1000):.3f}s" if lane.finish_time is not None else "N/A"
#                         
#                         # Create simplified lane HTML structure
#                         lane_html = f"""
#                         <div class="lane">
#                             <h3>Lane {lane_id}</h3>
#                             <div class="lane-status">
#                                 <span>Status:</span>
#                                 <span class="{status_class}">{status_text}</span>
#                             </div>
#                             <div class="lane-status">
#                                 <span>Reaction Time:</span>
#                                 <span>{reaction_time}</span>
#                             </div>
#                             <div class="lane-status">
#                                 <span>Finish Time:</span>
#                                 <span>{finish_time}</span>
#                             </div>
#                         </div>
#                         """
#                         
#                         lanes_html += lane_html
#                         print(f"Added lane {lane_id} HTML ({len(lane_html)} chars)")
# 
#                     print(f"Total lanes HTML length: {len(lanes_html)} chars")            
#             
# #                     lanes_html = ""
# #                     print(f"Processing {len(race_manager.lanes)} lanes for display")
# #                     for lane in race_manager.lanes:
# #                         lane_id = lane.lane_id
# #                         print(f"Generating HTML for Lane {lane_id}")
# #                         
# #                         # Determine lane status
# #                         status_text = 'Ready'
# #                         status_class = ''
# #                         
# #                         if lane.false_start:
# #                             status_text = 'FALSE START'
# #                             status_class = 'false-start'
# #                         elif lane.place == 1:
# #                             status_text = 'WINNER!'
# #                             status_class = 'lane-winner'
# #                         elif lane.place:
# #                             status_text = f'Place: {lane.place}'
# #                         elif lane.staged and lane.prestaged:
# #                             status_text = 'Staged'
# #                         elif lane.prestaged:
# #                             status_text = 'Pre-staged'
# #                         
# #                         # Format times nicely
# #                         reaction_time = f"{(lane.reaction_time / 1000):.3f}s" if lane.reaction_time is not None else "N/A"
# #                         finish_time = f"{(lane.finish_time / 1000):.3f}s" if lane.finish_time is not None else "N/A"
# #                         
# #                         # Create lane HTML with lane ID class for specific styling if needed
# #                         lanes_html += f"""
# #                         <div class="lane lane-{lane_id}">
# #                             <h3>Lane {lane_id}</h3>
# #                             <div class="lane-status">
# #                                 <span>Status:</span>
# #                                 <span class="{status_class}">{status_text}</span>
# #                             </div>
# #                             <div class="lane-status">
# #                                 <span>Reaction Time:</span>
# #                                 <span>{reaction_time}</span>
# #                             </div>
# #                             <div class="lane-status">
# #                                 <span>Finish Time:</span>
# #                                 <span>{finish_time}</span>
# #                             </div>
# #                         </div>
# #                         """
                    
                    
                    # Read the template
                    with open('./web/control.html', 'r') as file:
                        html_content = file.read()
                    
                    # Update status text
                    if status['race_started']:
                        status_text = "In Progress"
                    else:
                        status_text = "Ready"
                        
                    # Update light sequence
                    if status['tree_running']:
                        light_text = f"Light sequence: {status['light_sequence'] or 'Running'}"
                    elif status['race_started']:
                        light_text = "Race in progress"
                    else:
                        light_text = "Waiting to start"
                        
                    # Replace placeholders with actual content
                    html_content = html_content.replace('<span id="raceStatusText"><!-- Status will be filled by server side--></span>', 
                                                     f'<span id="raceStatusText">{status_text}</span>')
                    html_content = html_content.replace('<div id="lightSequence"><!-- Sequence will be filled by server side--></div>', 
                                                     f'<div id="lightSequence">{light_text}</div>')
#                     html_content = html_content.replace('<div class="lanes-container" id="lanesContainer">', 
#                                                      f'<div class="lanes-container" id="lanesContainer">{lanes_html}')
                    html_content = html_content.replace('<!-- LANE_HTML_PLACEHOLDER -->', lanes_html)                    
                    # Add a timestamp to the generated page
                    import time
                    current_time = time.localtime()
                    time_string = f"{current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}"
                    html_content = html_content.replace('<!-- TIME_STAMP -->', time_string)
                    
                    send_response(client_socket, 200, 'text/html', html_content)
                else:
                    # Race manager not available
                    with open('./web/control.html', 'r') as file:
                        html_content = file.read()
                        
                    html_content = html_content.replace('<span id="raceStatusText"><!-- Status will be filled by server side--></span>', 
                                                     '<span id="raceStatusText">Race manager not available</span>')
                    
                    # Add timestamp even when race manager isn't available
                    import time
                    current_time = time.localtime()
                    time_string = f"{current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}"
                    html_content = html_content.replace('<!-- TIME_STAMP -->', time_string)
                    
                    send_response(client_socket, 200, 'text/html', html_content)
            except Exception as e:
                print(f"Error generating control page: {e}")
                send_response(client_socket, 500, 'text/plain', f"Server error: {str(e)}")
        
        # Serve test page
        elif path == '/test' or path == '/test.html':
            if 'test' in html_files:
                send_response(client_socket, 200, 'text/html', html_files['test'])
            else:
                # Generate simple test page
                test_page = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>API Test</title>
                </head>
                <body>
                    <h1>API Test Page</h1>
                    <p>Click the links to test API:</p>
                    <a href="/api/start">Start Race</a><br>
                    <a href="/api/reset">Reset Race</a><br>
                    <a href="/api/status">Get Status</a>
                </body>
                </html>
                """
                send_response(client_socket, 200, 'text/html', test_page)
            
        # Serve minimal test page
        elif path == '/minimal_test.html':
            try:
                with open('./web/minimal_test.html', 'r') as file:
                    minimal_test_content = file.read()
                send_response(client_socket, 200, 'text/html', minimal_test_content)
            except:
                # Fallback minimal test page
                minimal_test_content = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Minimal Test</title>
                    <style>
                        body { font-family: Arial; padding: 20px; }
                        button { padding: 10px; margin: 5px; }
                        #log { background: #f0f0f0; padding: 10px; height: 200px; overflow: auto; }
                    </style>
                </head>
                <body>
                    <h1>Minimal Test Page</h1>
                    
                    <div>
                        <h2>Simple Tests</h2>
                        <button id="testButton">Test Button (click me first)</button>
                        <button id="alertButton">Show Alert</button>
                        <a href="/api/start" id="directLink">Direct Link (this should work)</a>
                    </div>
                    
                    <div>
                        <h2>Simple API Tests</h2>
                        <button id="fetchButton">Test Fetch API</button>
                        <button id="xhrButton">Test XMLHttpRequest</button>
                    </div>
                    
                    <div>
                        <h2>Debug Log</h2>
                        <div id="log"></div>
                    </div>
                    
                    <script>
                        // Try several different ways to write to the log
                        // Method 1: Basic DOM manipulation
                        document.getElementById('log').innerHTML += "Page loaded<br>";
                        
                        // Method 2: Function for logging
                        function log(message) {
                            var logElement = document.getElementById('log');
                            logElement.innerHTML += message + "<br>";
                            logElement.scrollTop = logElement.scrollHeight;
                            console.log(message); // Also log to console
                        }
                        
                        log("Log function defined");
                        
                        // Method 3: Direct event handler
                        document.getElementById('testButton').onclick = function() {
                            log("Test button clicked via onclick property");
                        };
                        
                        // Method 4: addEventListener
                        document.getElementById('alertButton').addEventListener('click', function() {
                            log("Alert button clicked via addEventListener");
                            alert("This is a test alert");
                        });
                        
                        // Method 5: Direct onclick in HTML
                        function handleFetch() {
                            log("Fetch button clicked");
                            
                            fetch('/api/status')
                                .then(function(response) {
                                    log("Fetch response received: " + response.status);
                                    return response.json();
                                })
                                .then(function(data) {
                                    log("Data received: " + JSON.stringify(data).slice(0, 50) + "...");
                                })
                                .catch(function(error) {
                                    log("Fetch error: " + error);
                                });
                        }
                        
                        // Method 6: XMLHttpRequest
                        function handleXHR() {
                            log("XHR button clicked");
                            
                            var xhr = new XMLHttpRequest();
                            xhr.open('GET', '/api/status', true);
                            
                            xhr.onload = function() {
                                log("XHR response received: " + xhr.status);
                                if (xhr.status === 200) {
                                    log("XHR data: " + xhr.responseText.slice(0, 50) + "...");
                                }
                            };
                            
                            xhr.onerror = function() {
                                log("XHR error occurred");
                            };
                            
                            xhr.send();
                            log("XHR request sent");
                        }
                        
                        // Add event listeners using a different approach
                        document.getElementById('fetchButton').onclick = handleFetch;
                        document.getElementById('xhrButton').onclick = handleXHR;
                        
                        // Check if the document is loaded
                        log("Document ready state: " + document.readyState);
                    </script>
                </body>
                </html>
                """
                send_response(client_socket, 200, 'text/html', minimal_test_content)
                
        # Serve static files
        elif path == '/' or path == '/index.html':
            send_response(client_socket, 200, 'text/html', html_files['index'])
        elif path == '/race.html':
            send_response(client_socket, 200, 'text/html', html_files['race'])
        else:
            # Try to serve the file from the web directory
            try:
                file_path = path.lstrip('/')
                if file_path.startswith('web/'):
                    file_path = file_path[4:]  # Remove 'web/' prefix
                
                full_path = f'./web/{file_path}'
                with open(full_path, 'r') as file:
                    content = file.read()
                
                # Determine content type based on file extension
                content_type = 'text/plain'
                if file_path.endswith('.html'):
                    content_type = 'text/html'
                elif file_path.endswith('.css'):
                    content_type = 'text/css'
                elif file_path.endswith('.js'):
                    content_type = 'application/javascript'
                
                send_response(client_socket, 200, content_type, content)
            except:
                # 404 Not Found
                send_response(client_socket, 404, 'text/plain', 'File not found')
            
    except Exception as e:
        print(f"Error handling request: {e}")
        try:
            send_response(client_socket, 500, 'text/plain', f"Server error: {str(e)}")
        except:
            pass
    finally:
        try:
            client_socket.close()
        except:
            pass

def handle_api_request(client_socket, method, path, headers, request):
    """Handle API requests with enhanced debugging"""
    global race_manager
    
    print("\n==== API REQUEST RECEIVED ====")
    print(f"Method: {method}")
    print(f"Path: {path}")
    
    # Extract API endpoint
    try:
        api_path = path.split('/api/')[1]
        
        # Strip any query params for endpoint detection
        if '?' in api_path:
            api_path = api_path.split('?')[0]
            
        print(f"API endpoint: {api_path}")
    except:
        print("Could not parse API path")
        api_path = ""
    
    # Check for a return parameter
    return_page = None
    if '?' in path:
        query_string = path.split('?')[1]
        params = query_string.split('&')
        for param in params:
            if param.startswith('return='):
                return_page = param.split('=')[1]
                print(f"Return page specified: {return_page}")
    
    # Create JSON response
    response = {'status': 'error', 'message': 'Unknown command'}
    
    if api_path.startswith('start'):
        print("START RACE requested")
        
        # Check race manager status
        if race_manager is None:
            print("ERROR: race_manager is None")
            response = {'status': 'error', 'message': 'Race manager not available'}
        elif race_manager.race_started:
            print("ERROR: Race already in progress")
            response = {'status': 'error', 'message': 'Race already in progress'}
        else:
            print("Calling race_manager.start_race()")
            try:
                race_manager.start_race()
                print("race_manager.start_race() completed successfully")
                response = {'status': 'success', 'message': 'Race started'}
            except Exception as e:
                print(f"ERROR in race_manager.start_race(): {e}")
                response = {'status': 'error', 'message': f'Error starting race: {str(e)}'}
            
        # If there's a return page, send HTML response instead of JSON
        
        # If there's a return page, send a redirect response
        if return_page:
            print(f"Redirecting to {return_page}")
            redirect_response = f'HTTP/1.1 302 Found\r\n'
            redirect_response += f'Location: /{return_page}\r\n'
            redirect_response += 'Connection: close\r\n\r\n'
            
            try:
                client_socket.send(redirect_response.encode('utf-8'))
            except Exception as e:
                print(f"Error sending redirect: {e}")
            return        



#         if return_page:
#             try:
#                 with open(f'./web/action_response.html', 'r') as file:
#                     html_content = file.read()
#                     html_content = html_content.replace('PLACEHOLDER_MESSAGE', f"Race Started Successfully!")
#                     send_response(client_socket, 200, 'text/html', html_content)
#                     return
#             except Exception as e:
#                 print(f"Error generating HTML response: {e}")
            
    elif api_path.startswith('reset'):
        print("RESET RACE requested")
        
        # Check race manager status
        if race_manager is None:
            print("ERROR: race_manager is None")
            response = {'status': 'error', 'message': 'Race manager not available'}
        else:
            print("Calling race_manager.reset_race()")
            try:
                race_manager.reset_race()
                print("race_manager.reset_race() completed successfully")
                response = {'status': 'success', 'message': 'Race reset'}
            except Exception as e:
                print(f"ERROR in race_manager.reset_race(): {e}")
                response = {'status': 'error', 'message': f'Error resetting race: {str(e)}'}
        
        # If there's a return page, send HTML response instead of JSON
        
        # If there's a return page, send a redirect response
        if return_page:
            print(f"Redirecting to {return_page}")
            redirect_response = f'HTTP/1.1 302 Found\r\n'
            redirect_response += f'Location: /{return_page}\r\n'
            redirect_response += 'Connection: close\r\n\r\n'
            
            try:
                client_socket.send(redirect_response.encode('utf-8'))
            except Exception as e:
                print(f"Error sending redirect: {e}")
            return
        
        
#         if return_page:
#             try:
#                 with open(f'./web/action_response.html', 'r') as file:
#                     html_content = file.read()
#                     html_content = html_content.replace('PLACEHOLDER_MESSAGE', f"Race Reset Successfully!")
#                     send_response(client_socket, 200, 'text/html', html_content)
#                     return
#             except Exception as e:
#                 print(f"Error generating HTML response: {e}")
        
    elif api_path.startswith('status'):
        # Get race status (omit detailed debug for this frequent call)
        if race_manager:
            try:
                status = {
                    'race_started': race_manager.race_started,
                    'tree_running': race_manager.tree_running,
                    'light_sequence': race_manager.current_stage,
                    'lanes': []
                }
                
                # Add lane information
                for i, lane in enumerate(race_manager.lanes):
                    lane_status = {
                        'lane_id': lane.lane_id,
                        'finish_time': lane.finish_time,
                        'reaction_time': lane.reaction_time,
                        'false_start': lane.false_start,
                        'place': lane.place,
                        'staged': lane.staged,
                        'prestaged': lane.prestaged
                    }
                    status['lanes'].append(lane_status)
                    
                response = status
            except Exception as e:
                print(f"Error generating status: {e}")
                response = {'status': 'error', 'message': f'Error generating status: {str(e)}'}
        else:
            response = {'status': 'error', 'message': 'Race manager not available'}
    
    else:
        print(f"Unknown API endpoint: {api_path}")
    
    # Send JSON response
    print(f"Sending response: {response if not api_path.startswith('status') else '(status data)'}")
    send_response(client_socket, 200, 'application/json', json.dumps(response))

def send_response(client_socket, status_code, content_type, content):
    """Send HTTP response"""
    status_message = {
        200: 'OK',
        404: 'Not Found',
        500: 'Internal Server Error',
        400: 'Bad Request'
    }.get(status_code, 'Unknown')
    
    response = f'HTTP/1.1 {status_code} {status_message}\r\n'
    response += f'Content-Type: {content_type}\r\n'
    response += 'Connection: close\r\n'
    response += 'Access-Control-Allow-Origin: *\r\n'  # Allow cross-origin requests
    
    # Add content length
    content_bytes = content.encode('utf-8') if isinstance(content, str) else content
    response += f'Content-Length: {len(content_bytes)}\r\n\r\n'
    
    # Send headers
    try:
        client_socket.send(response.encode('utf-8'))
        
        # Send content
        client_socket.send(content_bytes)
        
    except Exception as e:
        print(f"Error sending response: {e}")

def server_thread_function():
    """Server thread function with enhanced debugging"""
    global server_running
    
    # Create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind and listen
    try:
        server_address = ('0.0.0.0', 80)
        server_socket.bind(server_address)
        server_socket.listen(5)
        print(f"Server started on http://{current_ip}:80")
        
        # Blink LED to indicate server is running
        for _ in range(5):
            led.on()
            time.sleep(0.1)
            led.off()
            time.sleep(0.1)
        
        # Leave LED on to indicate server is running
        led.on()
        
        # Main server loop
        while server_running:
            try:
                # Simple blocking accept - proven to be most reliable
                client_socket, client_address = server_socket.accept()
                print(f"\nClient connected: {client_address}")
                
                # Handle the request
                handle_request(client_socket)
                
            except Exception as e:
                print(f"Error in server loop: {e}")
                time.sleep(0.5)
                
            # Collect garbage occasionally
            if time.time() % 10 < 0.5:  # Every ~10 seconds
                gc.collect()
            
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_socket.close()
        print("Server thread stopped")
        led.off()

def start_server(race_mgr=None):
    """Start the web server with improved reliability"""
    global race_manager, server_running, server_thread, current_ip
    
    # Set race manager reference
    race_manager = race_mgr
    
    # Load configuration
    load_configuration()
    
    # Load HTML files
    load_html_files()
    
    # Turn on LED to indicate starting
    led.on()
    
    # First try to connect to home network if available
    home_network_connected = connect_to_home_network()
    
    # If not connected to home network, set up access point
    if not home_network_connected:
        print("\nFalling back to access point mode...")
        if not setup_access_point():
            print("Failed to set up WiFi. Check your network configuration.")
            led.off()
            return False
    
    # Flash LED to indicate WiFi is ready
    for _ in range(3):
        led.on()
        time.sleep(0.3)
        led.off()
        time.sleep(0.3)
    
    # Start server thread
    server_running = True
    try:
        server_thread = _thread.start_new_thread(server_thread_function, ())
        print("Server thread started")
        return True
    except Exception as e:
        print(f"Failed to start server thread: {e}")
        server_running = False
        led.off()
        return False

def stop_server():
    """Stop the web server"""
    global server_running
    
    if server_running:
        server_running = False
        print("Server stopping...")
        time.sleep(1)  # Give server thread time to stop
        led.off()
        return True
    else:
        print("Server not running")
        return False