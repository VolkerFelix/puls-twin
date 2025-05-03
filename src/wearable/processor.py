import os
import sys
import time
import json
import numpy as np
from threading import Thread

# Assuming pulse_engine is the imported Pulse Physiology Engine package
# This would be the appropriate import for your specific implementation
try:
    # Platform-specific imports based on installation method
    from pulse_engine import PhysiologyEngine, SEScalarTypes as Types
    from pulse_engine import SEHeartRateData, SERespirationRateData
    from pulse_engine import SEPatientActionCollection as Actions
except ImportError:
    print("Error: Pulse Physiology Engine package not found")
    print("Please install the Pulse Engine SDK from: https://pulse.kitware.com/")
    sys.exit(1)

class WearableDataProcessor:
    """
    Processes incoming data from wearable devices and maps them to 
    Pulse Physiology Engine parameters.
    """
    
    def __init__(self, engine=None, data_source=None):
        """
        Initialize the wearable data processor with connection to the Pulse Engine
        
        Args:
            engine: An initialized Pulse PhysiologyEngine instance
            data_source: Source of wearable data (API, BLE connection, etc.)
        """
        self.engine = engine
        self.data_source = data_source
        self.running = False
        self.processing_thread = None
        
        # Default values for when data isn't available
        self.default_heart_rate = 70  # bpm
        self.default_resp_rate = 14   # breaths per minute
        self.default_activity = 0     # MET (metabolic equivalent of task)
        
        # For smoothing input data
        self.hr_buffer = []
        self.rr_buffer = []
        self.activity_buffer = []
        self.buffer_size = 5  # Number of samples to average
        
    def start_processing(self, interval=1.0):
        """Start processing wearable data at specified interval (seconds)"""
        if self.processing_thread is not None and self.processing_thread.is_alive():
            print("Already processing wearable data")
            return
            
        self.running = True
        self.processing_thread = Thread(target=self._process_loop, args=(interval,))
        self.processing_thread.daemon = True
        self.processing_thread.start()
        print(f"Started wearable data processing with {interval}s interval")
        
    def stop_processing(self):
        """Stop processing wearable data"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=3.0)
        print("Stopped wearable data processing")
        
    def _process_loop(self, interval):
        """Main processing loop that runs at the specified interval"""
        while self.running:
            try:
                # 1. Get latest data from wearable
                wearable_data = self._fetch_wearable_data()
                
                # 2. Process and apply to Pulse Engine
                if wearable_data and self.engine:
                    self._update_engine_parameters(wearable_data)
                
                # 3. Wait for next interval
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error in wearable data processing: {e}")
                time.sleep(1)  # Prevent rapid error looping
    
    def _fetch_wearable_data(self):
        """
        Fetch latest data from wearable source
        Override this method with your specific wearable data source implementation
        """
        if self.data_source is None:
            # Generate mock data for testing
            return {
                'heart_rate': np.random.normal(70, 5),  # Mean 70, std 5
                'respiratory_rate': np.random.normal(14, 2),
                'activity_level': max(0, np.random.normal(1.5, 1.0))  # MET value, non-negative
            }
        
        # Implement your specific wearable data source interface here
        # Example for JSON data from an API:
        # response = requests.get(f"{self.data_source}/latest")
        # if response.status_code == 200:
        #     return response.json()
        
        return None
    
    def _smooth_data(self, value, buffer):
        """Apply smoothing to reduce noise in sensor data"""
        buffer.append(value)
        if len(buffer) > self.buffer_size:
            buffer.pop(0)
        return sum(buffer) / len(buffer)
    
    def _update_engine_parameters(self, wearable_data):
        """
        Update Pulse Engine parameters based on wearable data
        This maps wearable metrics to the appropriate Pulse Engine parameters
        """
        if self.engine is None:
            print("No Pulse Engine instance available")
            return
            
        try:
            # 1. Process Heart Rate
            if 'heart_rate' in wearable_data:
                hr = self._smooth_data(wearable_data['heart_rate'], self.hr_buffer)
                # Set heart rate in the engine
                # The exact API call depends on the Pulse API version
                self._set_heart_rate(hr)
                
            # 2. Process Respiratory Rate
            if 'respiratory_rate' in wearable_data:
                rr = self._smooth_data(wearable_data['respiratory_rate'], self.rr_buffer)
                # Set respiratory rate in the engine
                self._set_respiratory_rate(rr)
                
            # 3. Process Activity Level (as metabolic demand)
            if 'activity_level' in wearable_data:
                activity = self._smooth_data(wearable_data['activity_level'], self.activity_buffer)
                # Convert activity level to metabolic demand
                # Typical MET values: 1.0 (rest), 3-6 (moderate), 6+ (vigorous)
                self._set_metabolic_demand(activity)
                
        except Exception as e:
            print(f"Error updating engine parameters: {e}")
    
    def _set_heart_rate(self, heart_rate):
        """Set the heart rate parameter in the Pulse Engine"""
        try:
            # In newer versions of Pulse, you would use the action interface
            # to set target heart rate
            action = Actions.create(Actions.HeartRate)
            action.HeartRate.HeartRate(Types.FrequencyUnit.PerMinute, heart_rate)
            self.engine.execute_action(action)
            print(f"Set heart rate to {heart_rate} bpm")
        except Exception as e:
            print(f"Error setting heart rate: {e}")
            
    def _set_respiratory_rate(self, resp_rate):
        """Set the respiratory rate parameter in the Pulse Engine"""
        try:
            # Similar to heart rate, we use the action interface
            action = Actions.create(Actions.RespiratoryRate)
            action.RespiratoryRate.RespiratoryRate(Types.FrequencyUnit.PerMinute, resp_rate)
            self.engine.execute_action(action)
            print(f"Set respiratory rate to {resp_rate} breaths/min")
        except Exception as e:
            print(f"Error setting respiratory rate: {e}")
            
    def _set_metabolic_demand(self, met_value):
        """
        Set metabolic demand based on activity level
        MET values indicate intensity:
        - 1.0: Resting
        - 1-3: Light activity
        - 3-6: Moderate activity 
        - 6+: Vigorous activity
        """
        try:
            # Convert MET to oxygen consumption (mL/min)
            # Standard formula: VO2 (mL/min) = MET * 3.5 * weight (kg)
            # We can get the patient weight from the engine
            weight_kg = 70  # Default if we can't get it from the engine
            try:
                patient = self.engine.get_patient()
                weight_kg = patient.get_weight(Types.MassUnit.kg)
            except:
                pass
                
            o2_consumption = met_value * 3.5 * weight_kg
            
            # Set the exercise level in the engine
            action = Actions.create(Actions.Exercise)
            # Using exercise intensity level (0.0 to 1.0)
            # Map MET range (1-10) to intensity (0-1)
            intensity = min(1.0, (met_value - 1) / 9.0)
            action.Exercise.Intensity(intensity)
            self.engine.execute_action(action)
            print(f"Set exercise intensity to {intensity:.2f} (MET: {met_value:.1f})")
        except Exception as e:
            print(f"Error setting metabolic demand: {e}")


def initialize_pulse_engine():
    """Initialize and return a Pulse Physiology Engine instance"""
    try:
        # Create the engine - specifics depend on your Pulse installation
        engine = PhysiologyEngine()
        
        # Initialize with default patient parameters
        # This can be customized based on your requirements
        engine.initialize_engine()
        
        print("Pulse Physiology Engine initialized successfully")
        return engine
    except Exception as e:
        print(f"Failed to initialize Pulse Engine: {e}")
        return None


# Example usage
if __name__ == "__main__":
    # 1. Initialize Pulse Engine
    pulse_engine = initialize_pulse_engine()
    
    # 2. Create wearable data processor
    # For real implementation, replace with actual data source
    wearable_processor = WearableDataProcessor(
        engine=pulse_engine,
        data_source=None  # Using mock data for testing
    )
    
    # 3. Start processing wearable data
    wearable_processor.start_processing(interval=1.0)  # 1-second interval
    
    # 4. Run for some time
    try:
        print("Processing wearable data. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        # 5. Clean up
        wearable_processor.stop_processing()
        print("Done.")