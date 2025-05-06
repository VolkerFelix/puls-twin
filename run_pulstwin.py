#!/usr/bin/env python
"""
Runner script for the updated Wearable Twin system that uses
an existing state file from the Pulse installation.
"""

import sys
import time
import logging
import warnings
warnings.filterwarnings("ignore", module="google.protobuf.runtime_version")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WearableTwinSystem")

# Add the Pulse Engine path to the Python path
pulse_path = "/Users/volker/Work/Puls/builds/install/python"
if pulse_path not in sys.path:
    sys.path.insert(0, pulse_path)

# Now import our system
try:
    from src.system import WearableTwinSystem
    from src.output.console import ConsoleOutputChannel
    from output.web_output import WebVisualizationOutputChannel
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Make sure you've installed the package with: pip install -e .")
    sys.exit(1)

def main():
    """Run the wearable twin system"""
    logger.info("Starting Wearable Twin System...")
    
    web_output = None
    try:
        web_output = WebVisualizationOutputChannel(host="localhost", port=8000)
    except Exception as e:
        logger.error(f"Failed to create or test web output channel: {e}")
        import traceback
        logger.error(traceback.format_exc())
        web_output = None
    
    # Create console output
    console_output = ConsoleOutputChannel()
    
    # Create and initialize the system with available output channels
    output_channels = [console_output]
    if web_output:
        output_channels.append(web_output)
    
    try:
        logger.info("Initializing system...")
        twin_system = WearableTwinSystem(output_channels)
        
        # Start the system
        logger.info("Starting system...")
        twin_system.start()
        
        logger.info("\nWearable Twin System is running.")
        if web_output:
            logger.info("Web visualization available at: http://localhost:8000")
        logger.info("Press Ctrl+C to stop...")
        
        # Keep running until interrupted
        while True:
            time.sleep(5)
            logger.info("System is still running...")
            
            if web_output and hasattr(web_output, 'data') and hasattr(web_output, 'data_path'):
                hr_points = len(web_output.data['values']['heart_rate'])
                logger.info(f"Web output has {hr_points} heart rate data points")
            
    except KeyboardInterrupt:
        logger.info("\nStopping...")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Clean up
        if 'twin_system' in locals():
            twin_system.stop()
        logger.info("System stopped.")

if __name__ == "__main__":
    main()