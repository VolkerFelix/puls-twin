from .base import OutputChannel
import json
import os
import time
import threading
import logging
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial

logger = logging.getLogger("WearableTwinSystem")

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that can handle non-serializable objects"""
    def default(self, obj):
        # Handle booleans explicitly
        if isinstance(obj, bool):
            return int(obj)  # Convert to 0 or 1
        # For any other non-serializable objects, convert to string
        try:
            return float(obj)
        except (TypeError, ValueError):
            return str(obj)

class WebVisualizationOutputChannel(OutputChannel):
    """
    Output channel that visualizes avatar state in a web browser using charts.
    Receives data directly from the Pulse Engine via the update_avatar_state method.
    """
    
    def __init__(self, host="localhost", port=8000, auto_open_browser=True):
        """Initialize web visualization output channel"""
        self.host = host
        self.port = port
        self.auto_open_browser = auto_open_browser
        
        # Get absolute path to web directory
        self.web_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "web"))
        logger.info(f"Using web directory: {self.web_dir}")
        
        # Create web directory if it doesn't exist
        os.makedirs(self.web_dir, exist_ok=True)
        
        # Create data file path
        self.data_path = os.path.join(self.web_dir, "data.json")
        logger.info(f"Data file path: {self.data_path}")
        
        # Initialize data structure with empty series
        self.data = {
            "states": [],
            "values": {
                "heart_rate": [],
                "systolic_pressure": [],
                "diastolic_pressure": [],
                "mean_pressure": [],
                "oxygen_saturation": [],
                "respiratory_rate": []
            },
            "current_state": {
                "primary_state": "neutral",
                "description": "Twin is in a neutral state",
                "all_states": {
                    "is_dizzy": 0,
                    "is_chill": 0,
                    "is_beast_mode": 0
                }
            },
            "latest_record": None
        }
        
        # Write initial data file
        try:
            with open(self.data_path, 'w') as f:
                json.dump(self.data, f, indent=2, cls=CustomJSONEncoder)
            logger.info(f"Created initial data file at {self.data_path}")
        except Exception as e:
            logger.error(f"Failed to create initial data file: {e}")
            raise
        
        # Set up HTTP server
        self.server = None
        self.server_thread = None
        self._start_http_server()
        
        # Open browser if requested
        if self.auto_open_browser:
            self._open_browser()
    
    def _start_http_server(self):
        """Start the HTTP server in a separate thread"""
        # Create a custom handler that serves from our web directory
        class CustomHandler(SimpleHTTPRequestHandler):
            def __init__(self, web_dir, *args, **kwargs):
                self.web_dir = web_dir
                super().__init__(*args, **kwargs)
            
            def translate_path(self, path):
                # Translate URL paths to local file system paths
                path = SimpleHTTPRequestHandler.translate_path(self, path)
                rel_path = os.path.relpath(path, os.getcwd())
                return os.path.join(self.web_dir, rel_path)
            
            def log_message(self, format, *args):
                # Suppress default logging
                return
        
        # Create a partial function with the web_dir already set
        handler = partial(CustomHandler, self.web_dir)
        
        # Create and start the server
        try:
            self.server = HTTPServer((self.host, self.port), handler)
            
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            logger.info(f"Started web visualization server at http://{self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")
    
    def _open_browser(self):
        """Open the browser to display the visualization"""
        url = f"http://{self.host}:{self.port}"
        try:
            # Wait a moment to ensure the server is running
            time.sleep(0.5)
            webbrowser.open(url)
            logger.info(f"Open the web visualization at {url} to see the avatar state.")
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")
    
    def update_avatar_state(self, state_record):
        """
        Update avatar state based on data from the Pulse Engine.
        This method is called by the mini_system with each new state update.
        """
        try:
            # Get timestamp
            timestamp = time.time()
            if 'timestamp' in state_record:
                timestamp = timestamp
            
            # Get physiological values
            values = state_record.get('physiological_values', {})
            
            # Update each value in the data structure
            if 'heart_rate' in values:
                try:
                    self.data['values']['heart_rate'].append({
                        'x': float(timestamp),
                        'y': float(values['heart_rate'])
                    })
                    if len(self.data['values']['heart_rate']) > 100:
                        self.data['values']['heart_rate'] = self.data['values']['heart_rate'][-100:]
                except (ValueError, TypeError) as e:
                    logger.error(f"Error processing heart_rate value: {e}")
            
            if 'systolic_pressure' in values:
                try:
                    self.data['values']['systolic_pressure'].append({
                        'x': float(timestamp),
                        'y': float(values['systolic_pressure'])
                    })
                    if len(self.data['values']['systolic_pressure']) > 100:
                        self.data['values']['systolic_pressure'] = self.data['values']['systolic_pressure'][-100:]
                except (ValueError, TypeError) as e:
                    logger.error(f"Error processing systolic_pressure value: {e}")
            
            if 'diastolic_pressure' in values:
                try:
                    self.data['values']['diastolic_pressure'].append({
                        'x': float(timestamp),
                        'y': float(values['diastolic_pressure'])
                    })
                    if len(self.data['values']['diastolic_pressure']) > 100:
                        self.data['values']['diastolic_pressure'] = self.data['values']['diastolic_pressure'][-100:]
                except (ValueError, TypeError) as e:
                    logger.error(f"Error processing diastolic_pressure value: {e}")
            
            if 'mean_pressure' in values:
                try:
                    self.data['values']['mean_pressure'].append({
                        'x': float(timestamp),
                        'y': float(values['mean_pressure'])
                    })
                    if len(self.data['values']['mean_pressure']) > 100:
                        self.data['values']['mean_pressure'] = self.data['values']['mean_pressure'][-100:]
                except (ValueError, TypeError) as e:
                    logger.error(f"Error processing mean_pressure value: {e}")
            
            if 'oxygen_saturation' in values:
                try:
                    self.data['values']['oxygen_saturation'].append({
                        'x': float(timestamp),
                        'y': float(values['oxygen_saturation'])
                    })
                    if len(self.data['values']['oxygen_saturation']) > 100:
                        self.data['values']['oxygen_saturation'] = self.data['values']['oxygen_saturation'][-100:]
                except (ValueError, TypeError) as e:
                    logger.error(f"Error processing oxygen_saturation value: {e}")
            
            if 'respiratory_rate' in values:
                try:
                    self.data['values']['respiratory_rate'].append({
                        'x': float(timestamp),
                        'y': float(values['respiratory_rate'])
                    })
                    if len(self.data['values']['respiratory_rate']) > 100:
                        self.data['values']['respiratory_rate'] = self.data['values']['respiratory_rate'][-100:]
                except (ValueError, TypeError) as e:
                    logger.error(f"Error processing respiratory_rate value: {e}")
            
            # Update current state
            primary_state = state_record.get('primary_state', 'neutral')
            state_description = state_record.get('state_description', 'Unknown state')
            
            self.data['current_state'] = {
                'primary_state': primary_state,
                'description': state_description,
                'all_states': state_record.get('all_states', {})
            }
            
            # Add to state history
            self.data['states'].append({
                'timestamp': float(timestamp),
                'state': primary_state,
                'description': state_description
            })
            
            # Keep only the last 100 states
            if len(self.data['states']) > 100:
                self.data['states'] = self.data['states'][-100:]
            
            # Update latest record
            self.data['latest_record'] = state_record
            
            # Write updated data to file using custom encoder
            with open(self.data_path, 'w') as f:
                json.dump(self.data, f, indent=2, cls=CustomJSONEncoder)
                        
        except Exception as e:
            logger.error(f"Error updating visualization data: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def __del__(self):
        """Clean up when the object is deleted"""
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
                logger.info("Stopped web visualization server")
            except Exception as e:
                logger.error(f"Error stopping web server: {e}")