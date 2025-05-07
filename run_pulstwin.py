#!/usr/bin/env python
"""
Runner script for the updated Wearable Twin system that uses
an existing state file from the Pulse installation.
"""

import sys
import time
import logging
import click
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

@click.command()
@click.option('--web', is_flag=True, help='Enable web visualization')
@click.option('--console', is_flag=True, help='Enable console output')
@click.option('--workout', is_flag=True, help='Start with a workout')
@click.option('--intensity', type=float, default=0.5, help='Workout intensity (0.0-1.0)')
@click.option('--duration', type=int, default=5, help='Workout duration in minutes')
@click.option('--hangover', is_flag=True, help='Start a hangover recovery simulation')
@click.option('--severity', type=float, default=0.7, help='Hangover severity (0.0-1.0)')
def main(web, console, workout, intensity, duration, hangover, severity):
    """Run the wearable twin system"""
    logger.info("Starting Wearable Twin System...")
    
    web_output = None
    console_output = None
    output_channels = []

    if web:
        try:
            web_output = WebVisualizationOutputChannel(host="localhost", port=8000)
            output_channels.append(web_output)
        except Exception as e:
            logger.error(f"Failed to create or test web output channel: {e}")
        import traceback
        logger.error(traceback.format_exc())
        web_output = None
    
    if console:
        # Create console output
        console_output = ConsoleOutputChannel()
        output_channels.append(console_output)
    
    try:
        logger.info("Initializing system...")
        twin_system = WearableTwinSystem(output_channels)
        
        # Start the system
        logger.info("Starting system...")
        twin_system.start()

        if workout:
            logger.info(f"Starting workout with intensity {intensity} for {duration} minutes")
            if hasattr(twin_system, 'workout_controller'):
                twin_system.workout_controller.start_workout(
                    workout_type="constant",
                    intensity=intensity,
                    duration_minutes=duration
                )
            else:
                twin_system.start_workout(intensity=intensity, duration_minutes=duration)

        if hangover:
            logger.info(f"Starting hangover recovery simulation with severity {severity}")
            if hasattr(twin_system, 'hangover_controller'):
                twin_system.hangover_controller.start_hangover_simulation(severity=severity)
                
                # Apply some default interventions for testing
                twin_system.hangover_controller.apply_intervention('hydration', 0.7)
                twin_system.hangover_controller.apply_intervention('electrolytes', 0.5)
                twin_system.hangover_controller.apply_intervention('rest', 0.8)
                
                logger.info("Applied default recovery interventions (hydration, electrolytes, rest)")
        
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