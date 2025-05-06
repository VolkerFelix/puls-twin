import os
import time
import logging
from threading import Thread

from pulse.engine.PulseEngine import PulseEngine
from pulse.cdm.engine import SEDataRequest, SEDataRequestManager
from pulse.cdm.scalars import FrequencyUnit, PressureUnit, VolumePerTimeUnit
from pulse.cdm.patient import SEPatient

from output.console import ConsoleOutputChannel
from output.base import OutputChannel

STATE_FILE_PATH = "/Users/volker/Work/Puls/builds/install/bin/states/StandardMale@0s.json"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WearableTwinSystem")

class WearableTwinSystem:
    """
    System class using an existing state file
    """
    
    def __init__(self, output_channels=None):
        """Initialize the wearable twin system"""
        self.running = False
        self.output_channels = []
        
        # Create required directories
        os.makedirs("./logs", exist_ok=True)
        os.makedirs("./test_results", exist_ok=True)
        
        # Initialize Pulse Engine
        try:
            self.pulse_engine = PulseEngine()
            logger.info("Pulse Engine created successfully")

            # Set up logging
            self.pulse_engine.set_log_filename("./logs/pulse_engine.log")
            self.pulse_engine.log_to_console(True)

            # Set up data requests
            self._set_data_mgr()
            
            # Initialize engine with existing state file
            self._init_engine()
            
            # Register output channels
            if output_channels:
                for channel in output_channels:
                    self._register_output_channel(channel)
            
            # Register default console output if no channels provided
            if not self.output_channels:
                self._register_output_channel(ConsoleOutputChannel())
                
            logger.info("Wearable Twin System initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing system: {e}")
            raise RuntimeError(f"Failed to initialize Wearable Twin System: {e}")
    
    def _set_data_mgr(self):
        """Set up data request manager with physiological parameters"""
        data_requests = [
            SEDataRequest.create_physiology_request("HeartRate", unit=FrequencyUnit.Per_min),
            SEDataRequest.create_physiology_request("MeanArterialPressure", unit=PressureUnit.mmHg),
            SEDataRequest.create_physiology_request("RespirationRate", unit=FrequencyUnit.Per_min),
            SEDataRequest.create_physiology_request("OxygenSaturation"),
            SEDataRequest.create_physiology_request("SystolicArterialPressure", unit=PressureUnit.mmHg),
            SEDataRequest.create_physiology_request("DiastolicArterialPressure", unit=PressureUnit.mmHg),
            SEDataRequest.create_physiology_request("CardiacOutput", unit=VolumePerTimeUnit.L_Per_min),
        ]
        self.data_req_mgr = SEDataRequestManager(data_requests)
        self.data_req_mgr.set_results_filename("./test_results/WearableTwin.csv")

    def _init_engine(self):
        """Initialize the Pulse Engine with an existing state file"""
        # Path to an existing state file in the Pulse installation
        state_file_path = STATE_FILE_PATH
        
        try:
            # Check that the file exists
            if not os.path.exists(state_file_path):
                logger.error(f"State file not found: {state_file_path}")
                raise FileNotFoundError(f"State file not found: {state_file_path}")
                
            logger.info(f"Loading state file: {state_file_path}")
            success = self.pulse_engine.serialize_from_file(state_file_path, self.data_req_mgr)
            
            if not success:
                logger.error(f"Failed to load state file: {state_file_path}")
                raise RuntimeError(f"Failed to load state file: {state_file_path}")
                
            logger.info("Successfully loaded state file")
            
            # Log initial patient info
            initial_patient = SEPatient()
            self.pulse_engine.get_initial_patient(initial_patient)
            logger.info(f"Patient: {initial_patient.get_name()}")
            logger.info(f"Sex: {initial_patient.get_sex()}")
            logger.info(f"Age: {initial_patient.get_age()}")
            logger.info(f"Height: {initial_patient.get_height()}")
            logger.info(f"Weight: {initial_patient.get_weight()}")
            
        except Exception as e:
            logger.error(f"Error initializing engine: {e}")
            raise RuntimeError(f"Failed to initialize engine: {e}")
    
    def _register_output_channel(self, channel):
        """Register an output channel to receive avatar state updates"""
        
        if isinstance(channel, OutputChannel):
            self.output_channels.append(channel)
            logger.info(f"Registered output channel: {channel.__class__.__name__}")
            return True
        logger.warning(f"Invalid output channel: {type(channel).__name__}")
        return False
        
    def start(self):
        """Start a minimal simulation"""
        if self.running:
            logger.warning("System is already running")
            return False
            
        try:
            # Start a basic simulation thread to advance time
            self.running = True
            self.simulation_thread = Thread(target=self._simulation_loop)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
            
            logger.info("Simulation started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting system: {e}")
            self.running = False
            return False
    
    def _simulation_loop(self):
        """Main simulation loop that advances time and updates outputs"""
        update_interval = 0.5  # How often to update in seconds
        time_step = 0.02       # Simulation time step in seconds
        
        while self.running:
            try:
                # Advance time
                self.pulse_engine.advance_time_s(time_step)
                
                # Get physiological values periodically
                results = self.pulse_engine.pull_data()
                
                # Update output channels with the data
                state_record = {
                    'timestamp': time.time(),
                    'primary_state': 'neutral',
                    'state_description': 'Twin is in a neutral state',
                    'all_states': {
                        'is_dizzy': False, 
                        'is_chill': results[1] < 80,  # Heart rate below 80 = chill
                        'is_beast_mode': results[1] > 90  # Heart rate above 90 = beast mode
                    },
                    'physiological_values': {
                        'heart_rate': float(results[1]),
                        'mean_pressure': float(results[2]),
                        'respiratory_rate': float(results[3]),
                        'oxygen_saturation': float(results[4]),
                        'systolic_pressure': float(results[5]),
                        'diastolic_pressure': float(results[6]),
                        'cardiac_output': float(results[7])
                    }
                }
                
                # Determine primary state
                if state_record['all_states']['is_dizzy']:
                    state_record['primary_state'] = 'is_dizzy'
                    state_record['state_description'] = 'Twin is dizzy'
                elif state_record['all_states']['is_beast_mode']:
                    state_record['primary_state'] = 'is_beast_mode'
                    state_record['state_description'] = 'Twin is in beast mode'
                elif state_record['all_states']['is_chill']:
                    state_record['primary_state'] = 'is_chill'
                    state_record['state_description'] = 'Twin is chill'

                # Update all output channels
                for i, channel in enumerate(self.output_channels):
                    try:
                        channel.update_avatar_state(state_record)
                    except Exception as e:
                        logger.error(f"Error updating output channel {i+1}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                
                # Sleep to control simulation speed
                time.sleep(update_interval)
                
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                time.sleep(0.1)  # Prevent rapid error looping
    
    def stop(self):
        """Stop the system"""
        logger.info("Stopping Wearable Twin System")
        self.running = False
        
        # Wait for simulation thread to end
        if hasattr(self, 'simulation_thread') and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=3.0)
        
        # Clean up
        if hasattr(self, 'pulse_engine'):
            self.pulse_engine.clear()
        
        logger.info("System stopped")