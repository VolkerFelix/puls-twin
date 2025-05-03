class WearableTwinSystem:
    """
    Main system class that integrates wearable data with Pulse Engine
    and manages the digital twin avatar state
    """
    
    def __init__(self):
        """Initialize the wearable twin system"""
        self.pulse_engine = None
        self.wearable_processor = None
        self.simulation = None
        self.avatar_manager = None
        self.running = False
        
        # Output channels
        self.output_channels = []
        
    def initialize(self, pulse_engine=None, wearable_source=None, 
                  output_channels=None, config_file=None):
        """
        Initialize the system with the provided components
        
        Args:
            pulse_engine: Initialized Pulse PhysiologyEngine instance
            wearable_source: Source of wearable data
            output_channels: List of output channels for avatar state
            config_file: Path to configuration file (optional)
        """
        logger.info("Initializing Wearable Twin System")
        
        # Load configuration if provided
        config = {}
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
        
        # Initialize or use provided Pulse Engine
        self.pulse_engine = pulse_engine
        if not self.pulse_engine:
            try:
                # Import and initialize Pulse Engine
                from pulse_engine import PhysiologyEngine
                self.pulse_engine = PhysiologyEngine()
                self.pulse_engine.initialize_engine()
                logger.info("Initialized Pulse Engine")
            except Exception as e:
                logger.error(f"Failed to initialize Pulse Engine: {e}")
                raise RuntimeError("Pulse Engine initialization failed")
        
        # Initialize components
        self.wearable_processor = WearableDataProcessor(
            engine=self.pulse_engine,
            data_source=wearable_source
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
        
    def register_output_channel(self, channel):
        """Register an output channel"""
        if isinstance(channel, OutputChannel):
            self.output_channels.append(channel)
            self.avatar_manager.register_output_channel(channel)
            logger.info(f"Registered output channel: {channel.__class__.__name__}")
            return True
        logger.warning(f"Invalid output channel: {channel}")
        return False
        
    def start(self, wearable_interval=1.0, simulation_step=0.02, 
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
    
    def stop(self):
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
        

# Example usage
if __name__ == "__main__":
    # Create system
    twin_system = WearableTwinSystem()
    
    # Initialize with output channels
    console_output = ConsoleOutputChannel()
    json_output = JsonAPIOutputChannel(output_path="avatar_state.json")
    
    twin_system.initialize(
        output_channels=[console_output, json_output]
    )
    
    # Start the system
    twin_system.start()
    
    # Run for demonstration
    try:
        print("\nWearable Twin System is running.")
        print("Press Ctrl+C to stop...")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Clean up
        twin_system.stop()
        print("System stopped.")