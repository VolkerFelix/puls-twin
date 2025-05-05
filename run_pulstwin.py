#!/usr/bin/env python
"""
Main runner script for the Pulse Twin system.
This script runs from the project root, so imports work as expected.
"""

import os
import sys

# Add the Pulse Engine path to the Python path
pulse_path = "/Users/volker/Work/Puls/builds/install/python"
if pulse_path not in sys.path:
    sys.path.insert(0, pulse_path)

# Now import our system
try:
    from src.system import WearableTwinSystem
    from src.output.console import ConsoleOutputChannel
    from src.output.json_api import JsonAPIOutputChannel
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you've installed the package with: pip install -e .")
    sys.exit(1)

def main():
    """Run the wearable twin system"""
    print("Starting Wearable Twin System...")
    
    # Create output channels
    console_output = ConsoleOutputChannel()
    json_output = JsonAPIOutputChannel(output_path="avatar_state.json")
    
    # Create system
    twin_system = WearableTwinSystem()
    
    # Initialize and start the system
    try:
        twin_system.start()
        
        print("\nWearable Twin System is running.")
        print("Press Ctrl+C to stop...")
        
        # Keep running until interrupted
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        if 'twin_system' in locals():
            twin_system.stop()
        print("System stopped.")

if __name__ == "__main__":
    main()