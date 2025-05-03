from base import OutputChannel

class JsonAPIOutputChannel(OutputChannel):
    """
    Provides a JSON API for external systems to access avatar state
    This could be implemented as a REST API, WebSocket, or file-based interface
    """
    
    def __init__(self, output_path=None):
        """
        Initialize JSON API output channel
        
        Args:
            output_path: Path to write JSON state file (None for in-memory only)
        """
        self.output_path = output_path
        self.current_state = {}
        self.lock = Lock()
        
    def update_avatar_state(self, state_record):
        """Update current state and write to file if configured"""
        with self.lock:
            self.current_state = state_record
            
            # Write to file if path is configured
            if self.output_path:
                try:
                    with open(self.output_path, 'w') as f:
                        json.dump(state_record, f, indent=2)
                except Exception as e:
                    logger.error(f"Error writing state to file: {e}")
    
    def get_current_state(self):
        """Get the current state (for API endpoints)"""
        with self.lock:
            return self.current_state.copy()