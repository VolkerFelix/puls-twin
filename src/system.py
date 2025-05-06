import sys
import os
import json
import time
import logging
from typing import List, Optional

from pulse.engine.PulseEngine import PulseEngine
from pulse.cdm.engine import SEDataRequest, SEDataRequestManager, IEventHandler, ILoggerForward
from pulse.cdm.scalars import FrequencyUnit, LengthUnit, MassUnit, MassPerVolumeUnit, \
                              PressureUnit, TemperatureUnit, TimeUnit, VolumeUnit, VolumePerTimeUnit

from output.console import ConsoleOutputChannel
from output.json_api import JsonAPIOutputChannel
from wearable.processor import WearableDataProcessor
from pulse.simulation import PulseSimulationController
from avatar.state_manager import AvatarStateManager
from pulse.patient import PatientConfiguration, eStartType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WearableTwinSystem")

class LocalEventHandler(IEventHandler):
    def handle_event(self, event, active, time_s):
        logger.info(f"Event {event} {'activated' if active else 'deactivated'} at {time_s}s")

class LocalLogForward(ILoggerForward):
    def forward_debug(self, msg):
        logger.debug(msg)
    def forward_info(self, msg):
        logger.info(msg)
    def forward_warning(self, msg):
        logger.warning(msg)
    def forward_error(self, msg):
        logger.error(msg)
    def forward_fatal(self, msg):
        logger.critical(msg)

class WearableTwinSystem:
    """
    Main system class that integrates wearable data with Pulse Engine
    and manages the digital twin avatar state
    """
    
    def __init__(self, output_channels=None, config_file=None):
        """Initialize the wearable twin system"""
        self.pulse_engine = PulseEngine()
        logger.info("Pulse Engine successfully created")

        # Set up event handler and logger
        self.pulse_engine.set_event_handler(LocalEventHandler())
        self.pulse_engine.set_log_listener(LocalLogForward())
        self.pulse_engine.log_to_console(True)
        self.pulse_engine.set_log_filename("./logs/pulse_engine.log")

        self._set_data_mgr()
        self.patient_config = PatientConfiguration(self.pulse_engine, self.data_req_mgr, eStartType.Stabilize_PatientObject)
        self.patient_config.set_data_root_dir("./data")  # Set the data root directory
        self._init_engine()

        self.wearable_processor = WearableDataProcessor(
            engine=self.pulse_engine,
            #data_source=wearable_source
        )
        
        self.simulation = PulseSimulationController(
            engine=self.pulse_engine
        )
        
        self.avatar_manager = AvatarStateManager(
            simulation_controller=self.simulation
        )
        
        # Register output channels
        if output_channels:
            for channel in output_channels:
                self.register_output_channel(channel)
        
        # Register default console output if no channels provided
        if not self.output_channels:
            self.register_output_channel(ConsoleOutputChannel())
            
        logger.info("Wearable Twin System initialized successfully")
        return True
    
    def _set_data_mgr(self):
        self.data_req_mgr = SEDataRequestManager([])
        data_requests = [
            SEDataRequest.create_physiology_request("HeartRate", unit=FrequencyUnit.Per_min),
            SEDataRequest.create_physiology_request("RespirationRate", unit=FrequencyUnit.Per_min),
            SEDataRequest.create_physiology_request("EndTidalCarbonDioxidePressure",  unit=PressureUnit.mmHg),
            SEDataRequest.create_gas_compartment_substance_request("Carina", "CarbonDioxide", "PartialPressure",  unit=PressureUnit.mmHg),
            SEDataRequest.create_substance_request("Oxygen", "AlveolarTransfer", VolumePerTimeUnit.mL_Per_s),
            SEDataRequest.create_substance_request("CarbonDioxide", "AlveolarTransfer", VolumePerTimeUnit.mL_Per_s),
        ]
        self.data_req_mgr = SEDataRequestManager(data_requests)
        self.data_req_mgr.set_results_filename("./test_results/UseCase1.csv")

    def _load_config(self, config_file):
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")

    def _init_engine(self):
        try:
            self.pulse_engine.initialize_engine(self.patient_config, self.data_req_mgr)
            logger.info("Initialized Pulse Engine")
        except Exception as e:
            logger.error(f"Failed to initialize Pulse Engine: {e}")
            raise RuntimeError("Pulse Engine initialization failed")

        
    def _register_output_channel(self, channel):
        """Register an output channel"""
        if isinstance(channel, OutputChannel):
            self.output_channels.append(channel)
            self.avatar_manager.register_output_channel(channel)
            logger.info(f"Registered output channel: {channel.__class__.__name__}")
            return True
        logger.warning(f"Invalid output channel: {channel}")
        return False
        
    def _start(self, wearable_interval=1.0, simulation_step=0.02, 
             display_interval=0.5):
        """
        Start the wearable twin system
        
        Args:
            wearable_interval: Interval for wearable data updates (seconds)
            simulation_step: Simulation time step (seconds)
            display_interval: Avatar state update interval (seconds)
        """
        if self.running:
            logger.warning("System is already running")
            return False
            
        try:
            # Start components in reverse order (display first, then simulation, then data input)
            logger.info("Starting avatar state display")
            self.avatar_manager.start_display(update_interval=display_interval)
            
            logger.info("Starting Pulse simulation")
            self.simulation.start_simulation(
                time_step=simulation_step,
                update_interval=display_interval
            )
            
            logger.info("Starting wearable data processing")
            self.wearable_processor.start_processing(interval=wearable_interval)
            
            self.running = True
            logger.info("Wearable Twin System started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting system: {e}")
            self.stop()  # Ensure cleanup if partial start
            return False
    
    def _stop(self):
        """Stop the wearable twin system"""
        logger.info("Stopping Wearable Twin System")
        
        # Stop components in forward order (data input first, then simulation, then display)
        if self.wearable_processor:
            self.wearable_processor.stop_processing()
            
        if self.simulation:
            self.simulation.stop_simulation()
            
        if self.avatar_manager:
            self.avatar_manager.stop_display()
            
        self.running = False
        logger.info("Wearable Twin System stopped")
        
    def get_avatar_state(self):
        """Get the current avatar state"""
        if self.avatar_manager:
            return self.avatar_manager.get_current_state()
        return None

    def get_physiological_values(self):
        """Get the current physiological values"""
        if self.simulation:
            return self.simulation.get_latest_values()
        return None
        