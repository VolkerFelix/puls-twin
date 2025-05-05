import os
import sys
import time
import json
import numpy as np
from threading import Thread, Lock

# try:
#     from pulse.cdm.engine import PhysiologyEngine, SEScalarTypes as Types
#     from pulse.cdm.engine import SECardiovascularSystem, SERespiratorySystem
#     from pulse.cdm.engine import SEBloodChemistrySystem, SESubstanceManager
# except ImportError:
#     print("Simulation Error: Pulse Physiology Engine package not found")
#     print("Please install the Pulse Engine SDK from: https://pulse.kitware.com/")
#     sys.exit(1)

class PulseSimulationController:
    """
    Controls the Pulse Physiology Engine simulation and extracts physiological outputs.
    Runs the simulation tick-by-tick and provides methods to get physiological states.
    """
    
    def __init__(self, engine=None):
        """
        Initialize the Pulse simulation controller
        
        Args:
            engine: An initialized Pulse PhysiologyEngine instance
        """
        self.engine = engine
        self.running = False
        self.simulation_thread = None
        self.simulation_lock = Lock()
        
        # Store latest physiological values
        self.latest_values = {
            'heart_rate': 0.0,           # beats per minute
            'systolic_pressure': 0.0,     # mmHg
            'diastolic_pressure': 0.0,    # mmHg
            'mean_pressure': 0.0,         # mmHg
            'stroke_volume': 0.0,         # mL
            'cardiac_output': 0.0,        # L/min
            'oxygen_saturation': 0.0,     # percentage
            'blood_oxygen': 0.0,          # mL O2 / dL blood
            'respiratory_rate': 0.0,      # breaths per minute
            'tidal_volume': 0.0,          # mL
            'oxygen_consumption': 0.0,    # mL/min
            'hrv': 0.0,                   # Heart Rate Variability (ms)
            'last_update_time': 0.0       # timestamp
        }
        
        # Computed states based on physiological values
        self.current_states = {
            'is_dizzy': False,            # Low O₂
            'is_chill': False,            # High HRV
            'is_beast_mode': False        # Elevated cardiac output
        }
        
        # Thresholds for determining states
        self.thresholds = {
            'low_oxygen_threshold': 90.0,         # SpO2 % - below this is low
            'high_hrv_threshold': 70.0,           # ms - above this is "chill"
            'elevated_cardiac_output': 6.0        # L/min - above this is "beast mode"
        }
        
    def start_simulation(self, time_step=0.02, update_interval=0.1):
        """
        Start running the Pulse simulation
        
        Args:
            time_step: Simulation time step in seconds (e.g., 0.02 = 50Hz)
            update_interval: How often to update physiological values in seconds
        """
        if self.simulation_thread is not None and self.simulation_thread.is_alive():
            print("Simulation is already running")
            return
            
        self.running = True
        self.simulation_thread = Thread(
            target=self._simulation_loop, 
            args=(time_step, update_interval)
        )
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        print(f"Started Pulse simulation with {time_step}s time step")
        
    def stop_simulation(self):
        """Stop the Pulse simulation"""
        self.running = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=3.0)
        print("Stopped Pulse simulation")
        
    def _simulation_loop(self, time_step, update_interval):
        """
        Main simulation loop that advances the Pulse engine
        
        Args:
            time_step: Simulation time step in seconds
            update_interval: How often to update values in seconds
        """
        last_update = 0.0
        while self.running:
            try:
                # Use lock to prevent conflicts with parameter updates
                with self.simulation_lock:
                    # Advance the simulation by one time step
                    self.engine.advance_time_s(time_step)
                
                # Update physiological values at specified interval
                current_time = time.time()
                if current_time - last_update >= update_interval:
                    self._update_physiological_values()
                    self._compute_states()
                    last_update = current_time
                    
                # Prevent CPU overload
                time.sleep(time_step / 10)
                
            except Exception as e:
                print(f"Error in simulation loop: {e}")
                time.sleep(0.1)  # Prevent rapid error looping
    
    def _update_physiological_values(self):
        """Update the latest physiological values from the Pulse engine"""
        if self.engine is None:
            return
            
        try:
            # Get system references
            cv_system = self.engine.get_cardiovascular_system()
            resp_system = self.engine.get_respiratory_system()
            blood_chem = self.engine.get_blood_chemistry_system()
            
            # Update cardiovascular values
            self.latest_values['heart_rate'] = cv_system.get_heart_rate(Types.FrequencyUnit.PerMinute)
            self.latest_values['systolic_pressure'] = cv_system.get_systolic_arterial_pressure(Types.PressureUnit.mmHg)
            self.latest_values['diastolic_pressure'] = cv_system.get_diastolic_arterial_pressure(Types.PressureUnit.mmHg)
            self.latest_values['mean_pressure'] = cv_system.get_mean_arterial_pressure(Types.PressureUnit.mmHg)
            self.latest_values['stroke_volume'] = cv_system.get_stroke_volume(Types.VolumeUnit.mL)
            self.latest_values['cardiac_output'] = cv_system.get_cardiac_output(Types.VolumePerTimeUnit.L_Per_min)
            
            # Update respiratory values
            self.latest_values['respiratory_rate'] = resp_system.get_respiration_rate(Types.FrequencyUnit.PerMinute)
            self.latest_values['tidal_volume'] = resp_system.get_tidal_volume(Types.VolumeUnit.mL)
            
            # Update blood chemistry values
            self.latest_values['oxygen_saturation'] = blood_chem.get_oxygen_saturation()
            self.latest_values['blood_oxygen'] = blood_chem.get_arterial_oxygen_concentration(Types.MassPerVolumeUnit.mg_Per_dL)
            
            # Calculate HRV (simplified simulation)
            # In a real implementation, this would compute from beat intervals
            # Here we use a simplified model based on current physiological state
            rest_level = 1.0 - min(1.0, self._calculate_stress_level())
            baseline_hrv = 50.0  # ms
            max_hrv = 100.0      # ms
            self.latest_values['hrv'] = baseline_hrv + rest_level * (max_hrv - baseline_hrv)
            
            # Update timestamp
            self.latest_values['last_update_time'] = time.time()
            
        except Exception as e:
            print(f"Error updating physiological values: {e}")
    
    def _calculate_stress_level(self):
        """
        Calculate an approximate stress level based on physiological values
        Returns a value between 0.0 (completely relaxed) and 1.0 (maximum stress)
        """
        # This is a simplified model - a real implementation would be more sophisticated
        
        # 1. Contribution from heart rate (normalized between rest and max)
        rest_hr = 60.0
        max_hr = 180.0
        hr_component = min(1.0, max(0.0, (self.latest_values['heart_rate'] - rest_hr) / (max_hr - rest_hr)))
        
        # 2. Contribution from blood pressure (systolic)
        normal_systolic = 120.0
        max_systolic = 180.0
        bp_component = min(1.0, max(0.0, (self.latest_values['systolic_pressure'] - normal_systolic) / 
                                  (max_systolic - normal_systolic)))
        
        # 3. Contribution from respiratory rate
        rest_rr = 12.0
        max_rr = 30.0
        rr_component = min(1.0, max(0.0, (self.latest_values['respiratory_rate'] - rest_rr) / 
                                  (max_rr - rest_rr)))
        
        # Weighted combination (can be adjusted based on importance)
        stress_level = 0.5 * hr_component + 0.3 * bp_component + 0.2 * rr_component
        return stress_level
        
    def _compute_states(self):
        """Compute the avatar states based on physiological values and thresholds"""
        # 1. Low O₂ → "Twin is dizzy"
        self.current_states['is_dizzy'] = (
            self.latest_values['oxygen_saturation'] < self.thresholds['low_oxygen_threshold']
        )
        
        # 2. High HRV → "Twin is chill"
        self.current_states['is_chill'] = (
            self.latest_values['hrv'] > self.thresholds['high_hrv_threshold']
        )
        
        # 3. Elevated cardiac output → "Twin is in beast mode"
        self.current_states['is_beast_mode'] = (
            self.latest_values['cardiac_output'] > self.thresholds['elevated_cardiac_output']
        )
    
    def get_latest_values(self):
        """Get the latest physiological values"""
        return self.latest_values.copy()
    
    def get_current_states(self):
        """Get the current avatar states"""
        return self.current_states.copy()
    
    def set_thresholds(self, threshold_dict):
        """
        Update the thresholds used for state determination
        
        Args:
            threshold_dict: Dictionary of threshold values to update
        """
        for key, value in threshold_dict.items():
            if key in self.thresholds:
                self.thresholds[key] = value
                
    def get_thresholds(self):
        """Get the current thresholds"""
        return self.thresholds.copy()


# Example usage
if __name__ == "__main__":
    # 1. Initialize Pulse Engine (pseudo-code)
    from pulse_engine import PhysiologyEngine
    pulse_engine = PhysiologyEngine()
    pulse_engine.initialize_engine()
    
    # 2. Create simulation controller
    simulation = PulseSimulationController(engine=pulse_engine)
    
    # 3. Start simulation
    simulation.start_simulation(time_step=0.02, update_interval=0.1)
    
    # 4. Run for some time and periodically check values/states
    try:
        print("Simulation running. Press Ctrl+C to stop...")
        for _ in range(10):  # Run for 10 seconds
            time.sleep(1)
            print("\nLatest physiological values:")
            for key, value in simulation.get_latest_values().items():
                if key != 'last_update_time':  # Skip timestamp
                    print(f"  {key}: {value:.2f}")
            
            print("\nCurrent states:")
            for key, value in simulation.get_current_states().items():
                print(f"  {key}: {value}")
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # 5. Clean up
        simulation.stop_simulation()
        print("Done.")