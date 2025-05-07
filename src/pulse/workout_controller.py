import time
import logging
from threading import Lock

from pulse.cdm.patient_actions import SEExercise

logger = logging.getLogger("WearableTwinSystem")

class WorkoutController:
    """
    Controls workout simulations in the Pulse Engine by applying
    exercise actions with varying intensity levels.
    """
    
    def __init__(self, pulse_engine=None):
        """
        Initialize workout controller
        
        Args:
            pulse_engine: Reference to the Pulse Engine instance
        """
        self.engine = pulse_engine
        self.lock = Lock()
        self.reset()
        
    def reset(self):
        """Reset all workout parameters to defaults"""
        with self.lock:
            self.active = False
            self.intensity = 0.0
            self.end_time = 0
            self.duration_minutes = 0
            self.start_time = 0
            self.workout_type = "none"
    
    def start_workout(self, workout_type="constant", intensity=0.5, duration_minutes=10):
        """
        Start a simulated workout
        
        Args:
            workout_type: Type of workout ("constant", "interval", "ramp_up", "ramp_down")
            intensity: Value from 0.0 to 1.0 indicating max workout intensity
            duration_minutes: Total workout duration in minutes
        
        Returns:
            True if workout started successfully, False otherwise
        """
        if self.engine is None:
            logger.error("No Pulse Engine instance available")
            return False
            
        with self.lock:
            # Validate parameters
            intensity = max(0.0, min(1.0, intensity))
            duration_minutes = max(0.1, duration_minutes)
            
            # Set workout parameters
            self.active = True
            self.intensity = intensity
            self.duration_minutes = duration_minutes
            self.start_time = time.time()
            self.end_time = self.start_time + (duration_minutes * 60)
            self.workout_type = workout_type
            
            logger.info(f"Starting {workout_type} workout with intensity {intensity} for {duration_minutes} minutes")
            return True
    
    def stop_workout(self):
        """Stop the current workout"""
        with self.lock:
            was_active = self.active
            self.active = False
            
            if was_active:
                logger.info("Workout stopped")
                return True
            return False
    
    def get_current_intensity(self):
        """
        Calculate the current workout intensity based on workout type and elapsed time
        
        Returns:
            Current intensity value between 0.0 and 1.0
        """
        with self.lock:
            if not self.active:
                return 0.0
                
            # Check if workout should end
            current_time = time.time()
            if current_time >= self.end_time:
                self.active = False
                logger.info("Workout complete")
                return 0.0
                
            # Calculate elapsed fraction (0.0 to 1.0)
            total_duration = (self.end_time - self.start_time)
            elapsed = (current_time - self.start_time)
            fraction = min(1.0, elapsed / total_duration)
            
            # Determine intensity based on workout type
            if self.workout_type == "constant":
                return self.intensity
                
            elif self.workout_type == "interval":
                # Alternates between high and low intensity every 2 minutes
                interval_duration = 120  # 2 minutes in seconds
                interval_phase = (elapsed % interval_duration) / interval_duration
                return self.intensity if interval_phase < 0.5 else self.intensity * 0.4
                
            elif self.workout_type == "ramp_up":
                # Gradually increases from 0.2*intensity to full intensity
                return (0.2 * self.intensity) + (0.8 * self.intensity * fraction)
                
            elif self.workout_type == "ramp_down":
                # Gradually decreases from full intensity to 0.2*intensity
                return self.intensity - (0.8 * self.intensity * fraction)
                
            else:
                # Default to constant intensity
                return self.intensity
                
    def apply_to_engine(self):
        """
        Apply the current workout intensity to the Pulse Engine
        
        Returns:
            True if workout was applied, False otherwise
        """
        if self.engine is None:
            return False
            
        try:
            # Get current intensity
            intensity = self.get_current_intensity()
            
            # Only apply non-zero intensity
            if intensity > 0.001:
                exercise = SEExercise()
                exercise.get_intensity().set_value(intensity)
                self.engine.process_action(exercise)

                return True
                
        except Exception as e:
            logger.error(f"Error applying workout to engine: {e}")
            
        return False