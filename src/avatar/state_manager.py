import os
import sys
import time
import json
from threading import Thread
from datetime import datetime

class AvatarStateManager:
    """
    Manages the avatar's visual state based on physiological parameters.
    Maps physiological states to avatar visualizations and provides
    an interface for external systems (e.g., game engines, visualization tools).
    """
    
    def __init__(self, simulation_controller=None):
        """
        Initialize the avatar state manager
        
        Args:
            simulation_controller: PulseSimulationController instance to get physiological states
        """
        self.simulation = simulation_controller
        self.running = False
        self.display_thread = None
        
        # Avatar state history for trend analysis
        self.state_history = []
        self.max_history_length = 100  # Store last 100 states
        
        # Avatar state descriptions
        self.state_descriptions = {
            'is_dizzy': "Twin is dizzy",
            'is_chill': "Twin is chill",
            'is_beast_mode': "Twin is in beast mode",
            'neutral': "Twin is in a neutral state"
        }
        
        # Initialize output channels
        self.output_channels = []
    
    def register_output_channel(self, channel):
        """
        Register an output channel to receive avatar state updates
        
        Args:
            channel: Object with an update_avatar_state(state_dict) method
        """
        if hasattr(channel, 'update_avatar_state') and callable(channel.update_avatar_state):
            self.output_channels.append(channel)
            return True
        return False
    
    def start_display(self, update_interval=0.5):
        """
        Start the avatar state display thread
        
        Args:
            update_interval: How often to update the avatar state in seconds
        """
        if self.display_thread is not None and self.display_thread.is_alive():
            print("Avatar display is already running")
            return
            
        self.running = True
        self.display_thread = Thread(
            target=self._display_loop, 
            args=(update_interval,)
        )
        self.display_thread.daemon = True
        self.display_thread.start()
        print(f"Started avatar state display with {update_interval}s update interval")
        
    def stop_display(self):
        """Stop the avatar state display"""
        self.running = False
        if self.display_thread:
            self.display_thread.join(timeout=3.0)
        print("Stopped avatar state display")
        
    def _display_loop(self, update_interval):
        """
        Main display loop that updates the avatar state
        
        Args:
            update_interval: How often to update the state in seconds
        """
        while self.running:
            try:
                # Get current physiological states from the simulation
                if self.simulation:
                    physiological_values = self.simulation.get_latest_values()
                    states = self.simulation.get_current_states()
                    
                    # Update avatar state
                    self._update_avatar_state(states, physiological_values)
                    
                # Wait for next update
                time.sleep(update_interval)
                
            except Exception as e:
                print(f"Error in display loop: {e}")
                time.sleep(0.1)  # Prevent rapid error looping
    
    def _update_avatar_state(self, states, values):
        """
        Update the avatar's state based on physiological states
        
        Args:
            states: Dictionary of Boolean state flags
            values: Dictionary of physiological values
        """
        # Determine the current primary state
        current_state = self._determine_primary_state(states)
        
        # Create state record with timestamp
        state_record = {
            'timestamp': datetime.now().isoformat(),
            'primary_state': current_state,
            'state_description': self.state_descriptions.get(current_state, "Unknown state"),
            'all_states': states.copy(),
            'physiological_values': {
                k: round(v, 2) if isinstance(v, float) else v 
                for k, v in values.items() if k != 'last_update_time'
            }
        }
        
        # Add to history
        self.state_history.append(state_record)
        if len(self.state_history) > self.max_history_length:
            self.state_history.pop(0)
            
        # Notify all registered output channels
        for channel in self.output_channels:
            try:
                channel.update_avatar_state(state_record)
            except Exception as e:
                print(f"Error updating output channel: {e}")
                
    def _determine_primary_state(self, states):
        """
        Determine the primary state of the avatar based on priority rules
        
        Args:
            states: Dictionary of Boolean state flags
        
        Returns:
            String identifier of the primary state
        """
        # Priority order (high to low):
        # 1. Dizzy (health concern)
        # 2. Beast mode (high performance)
        # 3. Chill (relaxed state)
        # 4. Neutral (default)
        
        if states.get('is_dizzy', False):
            return 'is_dizzy'
        elif states.get('is_beast_mode', False):
            return 'is_beast_mode'
        elif states.get('is_chill', False):
            return 'is_chill'
        else:
            return 'neutral'
            
    def get_current_state(self):
        """Get the current avatar state"""
        if not self.state_history:
            return {
                'primary_state': 'neutral',
                'state_description': self.state_descriptions['neutral']
            }
        return self.state_history[-1]
    
    def get_state_history(self):
        """Get the avatar state history"""
        return self.state_history.copy()
    
    def get_state_trend(self, state_key, duration_seconds=60):
        """
        Get trend data for a specific state over time
        
        Args:
            state_key: Key of the state to analyze (e.g., 'is_dizzy')
            duration_seconds: How far back to analyze
        
        Returns:
            Dictionary with trend analysis
        """
        if not self.state_history:
            return {'trend': 'neutral', 'occurrences': 0, 'total_records': 0}
            
        # Filter history to the specified duration
        now = datetime.now()
        filtered_history = []
        
        for record in self.state_history:
            try:
                timestamp = datetime.fromisoformat(record['timestamp'])
                time_diff = (now - timestamp).total_seconds()
                if time_diff <= duration_seconds:
                    filtered_history.append(record)
            except (ValueError, KeyError):
                continue
                
        # Count occurrences of the specified state
        occurrences = sum(1 for record in filtered_history 
                         if record.get('all_states', {}).get(state_key, False))
        
        total_records = len(filtered_history)
        if total_records == 0:
            return {'trend': 'neutral', 'occurrences': 0, 'total_records': 0}
            
        # Calculate frequency
        frequency = occurrences / total_records
        
        # Determine trend
        if frequency < 0.1:
            trend = 'rare'
        elif frequency < 0.3:
            trend = 'occasional'
        elif frequency < 0.7:
            trend = 'frequent'
        else:
            trend = 'dominant'
            
        return {
            'trend': trend,
            'frequency': frequency,
            'occurrences': occurrences,
            'total_records': total_records
        }