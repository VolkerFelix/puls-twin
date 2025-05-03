"""
Example script that demonstrates the Wearable-Driven Digital Twin System
with mock wearable data to simulate different scenarios.
"""

import os
import sys
import time
import json
import numpy as np
from threading import Thread

# Import the main system
from wearable_twin_system import (
    WearableTwinSystem, 
    ConsoleOutputChannel, 
    JsonAPIOutputChannel
)

class MockWearableSource:
    """
    Mocks a wearable device with programmable scenarios for testing the system
    """
    
    def __init__(self):
        """Initialize the mock wearable source"""
        self.current_scenario = "normal"
        self.connected = True
        
        # Define scenarios with physiological parameter ranges
        self.scenarios = {
            "normal": {
                "heart_rate": (65, 75),           # bpm
                "respiratory_rate": (12, 16),     # breaths per minute
                "activity_level": (1.0, 1.5)      # MET
            },
            "exercise": {
                "heart_rate": (120, 150),
                "respiratory_rate": (20, 30),
                "activity_level": (6.0, 8.0)
            },
            "relaxed": {
                "heart_rate": (55, 65),
                "respiratory_rate": (10, 14),
                "activity_level": (1.0, 1.2)
            },
            "oxygen_deprived": {
                "heart_rate": (85, 100),
                "respiratory_rate": (18, 25),
                "activity_level": (1.5, 2.5)
            }
        }
        
    def set_scenario(self, scenario_name):
        """
        Set the current simulation scenario
        
        Args:
            scenario_name: Name of the scenario to simulate
        
        Returns:
            Boolean indicating success/failure
        """
        if scenario_name in self.scenarios:
            self.current_scenario = scenario_name
            print(f"Switched to scenario: {scenario_name}")
            return True
        return False
        
    def get_available_scenarios(self):
        """Get list of available scenarios"""
        return list(self.scenarios.keys())
    
    def get_latest_data(self):
        """Get latest mock wearable data based on the current scenario"""
        if not self.connected:
            return None
            
        scenario = self.scenarios.get(self.current_scenario, self.scenarios["normal"])
        
        # Generate random values within scenario ranges with some noise
        hr_min, hr_max = scenario["heart_rate"]
        rr_min, rr_max = scenario["respiratory_rate"]
        al_min, al_max = scenario["activity_level"]
        
        return {
            'heart_rate': np.random.uniform(hr_min, hr_max),
            'respiratory_rate': np.random.uniform(rr_min, rr_max),
            'activity_level': np.random.uniform(al_min, al_max)
        }


class ScenarioController:
    """
    Controls the demonstration by switching between scenarios
    """
    
    def __init__(self, mock_source, sequence=None, duration=10):
        """
        Initialize the scenario controller
        
        Args:
            mock_source: MockWearableSource instance
            sequence: List of scenario names to run in sequence
            duration: Duration of each scenario in seconds
        """
        self.mock_source = mock_source
        self.sequence = sequence or ["normal", "exercise", "relaxed", "oxygen_deprived"]
        self.duration = duration
        self.running = False
        self.control_thread = None
        
    def start(self):
        """Start the scenario sequence"""
        if self.control_thread is not None and self.control_thread.is_alive():
            print("Scenario controller is already running")
            return
            
        self.running = True
        self.control_thread = Thread(target=self._control_loop)
        self.control_thread.daemon = True
        self.control_thread.start()
        
    def stop(self):
        """Stop the scenario sequence"""
        self.running = False
        if self.control_thread:
            self.control_thread.join(timeout=3.0)
        
    def _control_loop(self):
        """Main control loop that cycles through scenarios"""
        while self.running:
            for scenario in self.sequence:
                if not self.running:
                    break
                    
                # Switch to the next scenario
                self.mock_source.set_scenario(scenario)
                
                # Run for the specified duration
                start_time = time.time()
                while self.running and (time.time() - start_time) < self.duration:
                    time.sleep(0.5)


def main():
    """Main demonstration function"""
    print("Starting Wearable-Driven Digital Twin Demonstration")
    
    # 1. Create mock wearable source
    mock_wearable = MockWearableSource()
    
    # 2. Create system with necessary output channels
    twin_system = WearableTwinSystem()
    
    console_output = ConsoleOutputChannel()
    json_output = JsonAPIOutputChannel(output_path="avatar_state.json")
    
    # 3. Initialize system with mock wearable data source
    twin_system.initialize(
        wearable_source=mock_wearable,
        output_channels=[console_output, json_output]
    )
    
    # 4. Create scenario controller for the demonstration
    scenario_ctrl = ScenarioController(
        mock_source=mock_wearable,
        duration=30  # 30 seconds per scenario
    )
    
    # 5. Start system and demonstration
    twin_system.start()
    time.sleep(2)  # Allow system to stabilize
    scenario_ctrl.start()
    
    # 6. Run until interrupted
    try:
        print("\nWearable Twin Demonstration is running.")
        print("Available scenarios:", mock_wearable.get_available_scenarios())
        print("Press Ctrl+C to stop...")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping demonstration...")
    finally:
        # 7. Clean up
        scenario_ctrl.stop()
        twin_system.stop()
        print("Demonstration stopped.")


if __name__ == "__main__":
    main()