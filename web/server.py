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
            
            # Print headers for debugging (first 5 lines)
            print("Headers:")
            for i, line in enumerate(request_lines[1:6]):
                if line.strip():
                    print(f"  {line.strip()}")
            
        except Exception as e:
            print(f"Error parsing request: {e}")
            # Try to extract path directly
            if '/' in request:
                path = request[request.index('/'):request.index(' HTTP/') if ' HTTP/' in request else -1]
                method = "GET"  # Assume GET
                print(f"Recovered path: {path}")
            else:
                send_response(client_socket, 400, 'text/plain', 'Bad Request')
                return
        
        # API endpoints
        if path.startswith('/api/'):
            print(f"API request: {path}")
            handle_api_request(client_socket, method, path)
            return
        
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
            
        # Serve static files
        elif path == '/' or path == '/index.html':
            send_response(client_socket, 200, 'text/html', html_files['index'])
        elif path == '/race.html':
            send_response(client_socket, 200, 'text/html', html_files['race'])
        else:
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

def handle_api_request(client_socket, method, path):
    """Handle API requests with enhanced debugging"""
    global race_manager
    
    print("\n==== API REQUEST RECEIVED ====")
    print(f"Method: {method}")
    print(f"Path: {path}")
    
    # Extract API endpoint
    try:
        api_path = path.split('/api/')[1]
        
        # Strip any query params
        if '?' in api_path:
            api_path = api_path.split('?')[0]
            
        print(f"API endpoint: {api_path}")
    except:
        print("Could not parse API path")
        api_path = ""
    
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