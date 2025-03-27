# Web server module for Raspberry Pi Pico W Drag Race Controller
import network
import socket
import time
import json
import gc
import _thread
from machine import Pin
import os

# Network configuration - you can override these in config.py
SSID = 'DragRaceTimer'  # Access point name
PASSWORD = 'racetime123'    # Access point password (must be at least 8 characters)
IP = '192.168.4.1'       # IP address for the access point

# LED to indicate WiFi status
led = Pin("LED", Pin.OUT)

# Race manager reference
race_manager = None

# HTML templates
html_files = {}

# Server state
server_running = False
server_thread = None

def load_configuration():
    """Load web server configuration from config.py if available"""
    global SSID, PASSWORD, IP
    
    try:
        import config
        if hasattr(config, 'WIFI_SSID'):
            SSID = config.WIFI_SSID
        if hasattr(config, 'WIFI_PASSWORD'):
            PASSWORD = config.WIFI_PASSWORD
        if hasattr(config, 'WIFI_IP'):
            IP = config.WIFI_IP
        print(f"Loaded network configuration from config.py")
    except:
        print("Using default network configuration")

def load_html_files():
    """Load HTML files into memory"""
    try:
        print("Current directory:", os.getcwd())
        print("Files in web directory:", os.listdir('web'))
        
        # Use relative path with explicit opening method
        with open('./web/index.html', 'r') as file:
            content = file.read()
            html_files['index'] = content
            print(f"Loaded index.html, size: {len(content)} bytes")
            
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

def setup_access_point():
    """Set up WiFi access point with improved stability"""
    # Initialize the WLAN interface in access point mode
    wlan = network.WLAN(network.AP_IF)
    
    # Disable it first for a clean start
    wlan.active(False)
    time.sleep(1)
    
    # Configure the access point
    print(f"Configuring access point: SSID={SSID}, password={PASSWORD}")
    wlan.config(essid=SSID, password=PASSWORD, security=network.AUTH_WPA_WPA2_PSK)
    
    # Set a static IP address
    wlan.ifconfig((IP, '255.255.255.0', IP, '8.8.8.8'))
    
    # Activate the interface
    wlan.active(True)
    
    # Wait for it to become active
    max_wait = 10
    while max_wait > 0:
        if wlan.active():
            break
        max_wait -= 1
        print('Waiting for WiFi access point to be active...')
        time.sleep(1)
    
    if wlan.active():
        print(f'Access Point active: {SSID}')
        
        # Get and print the configuration details
        config_details = wlan.ifconfig()
        print(f'IP address: {config_details[0]}')
        print(f'Subnet mask: {config_details[1]}')
        print(f'Gateway: {config_details[2]}')
        print(f'DNS: {config_details[3]}')
        
        return True
    else:
        print('Failed to establish access point')
        return False

def handle_request(client_socket):
    """Handle incoming HTTP requests"""
    try:
        # Set a timeout for the client socket
        client_socket.settimeout(3.0)
        
        # Get request data
        request = client_socket.recv(1024).decode('utf-8')
        if not request:
            return
            
        request_line = request.split('\n')[0]
        method, path = request_line.split(' ')[:2]
        
        print(f"Request: {method} {path}")
        
        # API endpoints
        if path.startswith('/api/'):
            handle_api_request(client_socket, method, path)
            return
            
        # Serve static files
        if path == '/' or path == '/index.html':
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
    """Handle API requests"""
    # Extract API endpoint
    api_path = path.split('/api/')[1]
    
    # Create JSON response
    response = {'status': 'error', 'message': 'Unknown command'}
    
    if api_path.startswith('start'):
        # Start race (non-blocking)
        if race_manager and not race_manager.race_started:
            race_manager.start_race()
            response = {'status': 'success', 'message': 'Race started'}
        else:
            response = {'status': 'error', 'message': 'Race already in progress or race manager not available'}
            
    elif api_path.startswith('reset'):
        # Reset race
        if race_manager:
            race_manager.reset_race()
            response = {'status': 'success', 'message': 'Race reset'}
        else:
            response = {'status': 'error', 'message': 'Race manager not available'}
        
    elif api_path.startswith('status'):
        # Get race status
        if race_manager:
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
        else:
            response = {'status': 'error', 'message': 'Race manager not available'}
    
    # Send JSON response
    send_response(client_socket, 200, 'application/json', json.dumps(response))

def send_response(client_socket, status_code, content_type, content):
    """Send HTTP response"""
    status_message = {
        200: 'OK',
        404: 'Not Found',
        500: 'Internal Server Error'
    }.get(status_code, 'Unknown')
    
    response = f'HTTP/1.1 {status_code} {status_message}\r\n'
    response += f'Content-Type: {content_type}\r\n'
    response += 'Connection: close\r\n\r\n'
    
    # Send headers
    client_socket.send(response.encode('utf-8'))
    
    # Send content
    if isinstance(content, str):
        client_socket.send(content.encode('utf-8'))
    else:
        client_socket.send(content)

def server_thread_function():
    """Server thread function"""
    global server_running
    
    # Create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind and listen
    try:
        server_address = ('0.0.0.0', 80)
        server_socket.bind(server_address)
        server_socket.listen(5)
        print(f"Server started on http://{IP}:80")
        
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
            # Collect garbage to free memory
            gc.collect()
            
            # Set a timeout for accept to allow for server stop
            server_socket.settimeout(0.1)
            
            try:
                # Accept client connection
                client_socket, client_address = server_socket.accept()
                print(f"Client connected: {client_address}")
                
                # Handle the request
                handle_request(client_socket)
                
            except OSError as e:
                # Socket timeout or other socket error - continue
                pass
                
            # Small delay
            time.sleep(0.01)
            
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_socket.close()
        print("Server thread stopped")
        led.off()

def start_server(race_mgr=None):
    """Start the web server in a separate thread"""
    global race_manager, server_running, server_thread
    
    # Set race manager reference
    race_manager = race_mgr
    
    # Load configuration
    load_configuration()
    
    # Load HTML files
    load_html_files()
    
    # Set up access point
    if not setup_access_point():
        print("Failed to set up WiFi. Check your network configuration.")
        return False
    
    # Start server thread
    server_running = True
    try:
        server_thread = _thread.start_new_thread(server_thread_function, ())
        print("Server thread started")
        return True
    except Exception as e:
        print(f"Failed to start server thread: {e}")
        server_running = False
        return False

def stop_server():
    """Stop the web server"""
    global server_running
    
    if server_running:
        server_running = False
        print("Server stopping...")
        time.sleep(1)  # Give server thread time to stop
        return True
    else:
        print("Server not running")
        return False