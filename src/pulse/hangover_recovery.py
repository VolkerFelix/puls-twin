# src/pulse/hangover_recovery.py
import time
import logging
from threading import Lock

from pulse.cdm.patient_actions import SESubstanceCompound, SESubstanceInfusion, SEDrugAdministration, SEHemorrhage, SEFluidAdministration
from pulse.cdm.properties import SEScalarMassPerVolume, SEScalarMass, SEScalarVolumePerTime, SEScalarVolume
from pulse.cdm.scalars import MassPerVolumeUnit, MassUnit, VolumePerTimeUnit, VolumeUnit

logger = logging.getLogger("WearableTwinSystem")

class HangoverRecoveryController:
    """
    Controls hangover recovery simulations in the Pulse Engine by applying
    physiological effects and recovery interventions.
    """
    
    def __init__(self, pulse_engine=None):
        """
        Initialize hangover recovery controller
        
        Args:
            pulse_engine: Reference to the Pulse Engine instance
        """
        self.engine = pulse_engine
        self.lock = Lock()
        self.reset()
        
    def reset(self):
        """Reset all recovery parameters to defaults"""
        with self.lock:
            self.active = False
            self.severity = 0.0  # 0.0 to 1.0 (none to severe)
            self.recovery_progress = 0.0  # 0.0 to 1.0 (none to full recovery)
            self.start_time = 0
            self.last_update_time = 0
            
            # Track interventions and their effects
            self.interventions = {
                'hydration': 0.0,  # 0.0 to 1.0 (none to optimal)
                'electrolytes': 0.0,
                'nutrients': 0.0,
                'rest': 0.0,
                'exercise': 0.0,
                'medication': 0.0
            }
            
            # Recovery rate multipliers for each intervention
            self.recovery_multipliers = {
                'hydration': 0.5,       # Significant impact
                'electrolytes': 0.3,    # Moderate impact
                'nutrients': 0.3,       # Moderate impact
                'rest': 0.4,            # Moderate-high impact
                'exercise': 0.2,        # Low-moderate impact
                'medication': 0.3       # Moderate impact
            }
            
            # Track when actions were last applied
            self.last_actions = {
                'dehydration': 0,
                'hydration': 0,
                'electrolytes': 0,
                'nutrients': 0,
                'medication': 0
            }
    
    def start_hangover_simulation(self, severity=0.7):
        """
        Start a simulated hangover recovery
        
        Args:
            severity: Value from 0.0 to 1.0 indicating hangover severity
        
        Returns:
            True if simulation started successfully, False otherwise
        """
        if self.engine is None:
            logger.error("No Pulse Engine instance available")
            return False
            
        with self.lock:
            # Validate parameters
            severity = max(0.0, min(1.0, severity))
            
            # Set simulation parameters
            self.active = True
            self.severity = severity
            self.recovery_progress = 0.0
            self.start_time = time.time()
            self.last_update_time = self.start_time
            
            # Reset all interventions
            for key in self.interventions:
                self.interventions[key] = 0.0
                
            # Reset last actions
            for key in self.last_actions:
                self.last_actions[key] = 0
            
            # Apply initial hangover effects
            self._apply_initial_hangover_effects()
            
            logger.info(f"Starting hangover recovery simulation with severity {severity}")
            return True
    
    def _apply_initial_hangover_effects(self):
        """Apply initial physiological effects of a hangover"""
        try:
            # 1. Dehydration - reduced total body water
            # This is a primary effect of alcohol consumption
            self._apply_dehydration(self.severity)
            
            # 2. Acetaldehyde toxicity - a metabolite of alcohol
            # In a real implementation, you would use proper substance infusion
            # For simplicity, we're skipping this in this example
            
            # 3. Electrolyte imbalance
            # Also a result of dehydration and alcohol's diuretic effect
            
            # 4. Inflammatory response
            # Alcohol triggers cytokine release, causing inflammation
            
            logger.info(f"Applied initial hangover effects with severity {self.severity}")
            
        except Exception as e:
            logger.error(f"Error applying initial hangover effects: {e}")
    
    def _apply_dehydration(self, severity):
        """
        Apply dehydration effects to the Pulse Engine
        
        Args:
            pulse_engine: The initialized Pulse Engine instance
            severity: Value from 0.0 to 1.0 indicating dehydration severity
        """
        if not self.pulse_engine or severity < 0.01:
            return False
            
        try:
            # The main way to simulate dehydration is to use hemorrhage
            # which removes fluid from the vascular space
            # Create a hemorrhage action            
            hemorrhage = SEHemorrhage()
            
            # Set hemorrhage rate based on severity
            # For a 70kg person, total blood volume is ~5L
            # We'll simulate low to moderate dehydration (2-5% of body water)
            # which would be approximately 0.5-1.5L in blood volume
            
            # Convert severity (0-1) to a blood loss rate
            # For hangover we want a slower, milder effect compared to actual hemorrhage
            # Mild to moderate rate: 0.1-0.5 mL/s (based on severity)
            # This would be 6-30 mL/minute or 360-1800 mL/hour
            rate_ml_per_s = 0.1 + (severity * 0.4)  # 0.1 to 0.5 mL/s
            
            hemorrhage_rate = SEScalarVolumePerTime()
            hemorrhage_rate.set_value(rate_ml_per_s, VolumePerTimeUnit.mL_Per_s)
            hemorrhage.set_rate(hemorrhage_rate)
            
            # Set the compartment for fluid loss
            # For dehydration, blood loss would come from major veins/arteries
            hemorrhage.set_compartment("Vena Cava")
            
            # Execute the action
            self.pulse_engine.process_action(hemorrhage)
            
            # Log the action
            print(f"Applied dehydration via hemorrhage at {rate_ml_per_s:.2f} mL/s")
            
            return True
        
        except Exception as e:
            print(f"Error applying dehydration: {e}")
            return False
                
    def stop_simulation(self):
        """Stop the current hangover simulation"""
        with self.lock:
            was_active = self.active
            self.active = False
            
            if was_active:
                logger.info("Hangover recovery simulation stopped")
                return True
            return False
    
    def apply_intervention(self, intervention_type, level):
        """
        Apply a specific intervention to aid recovery
        
        Args:
            intervention_type: Type of intervention ('hydration', 'electrolytes', etc.)
            level: Value from 0.0 to 1.0 indicating intervention level
        
        Returns:
            True if intervention was applied, False otherwise
        """
        if not self.active:
            logger.warning("No active hangover simulation to apply intervention to")
            return False
            
        with self.lock:
            if intervention_type not in self.interventions:
                logger.error(f"Unknown intervention type: {intervention_type}")
                return False
                
            # Apply intervention
            level = max(0.0, min(1.0, level))
            self.interventions[intervention_type] = level
            
            # Apply physiological effects immediately
            if intervention_type == 'hydration':
                self._apply_hydration_intervention(level)
            elif intervention_type == 'electrolytes':
                self._apply_electrolyte_intervention(level)
            elif intervention_type == 'nutrients':
                self._apply_nutrient_intervention(level)
            elif intervention_type == 'medication':
                self._apply_medication_intervention(level)
            
            logger.info(f"Applied {intervention_type} intervention at level {level}")
            return True
    
    def _apply_hydration_intervention(self, level):
        """Apply hydration effects to the engine"""

        if not self.engine or level < 0.1:
            return False
            
        try:
            # Create a fluid administration action            
            # Fluid administration - oral or IV
            fluid_admin = SEFluidAdministration()
            
            # Set the fluid type - for hangover, typically water or saline
            fluid_admin.set_fluid_type("Saline")  # Can also be "Water" or "Blood"
            
            # Set the fluid amount - based on level (0.1-1.0)
            # Higher level = more fluid
            # For a hangover, typical rehydration might be 0.5-2L
            volume_ml = 500 + (level * 1500)  # 500-2000 mL
            
            bag_volume = SEScalarVolume()
            bag_volume.set_value(volume_ml, VolumeUnit.mL)
            fluid_admin.set_bag_volume(bag_volume)
            
            # Set administration rate
            # Oral hydration would be slower than IV
            # For oral, maybe 2-10 mL/s (120-600 mL/min)
            rate_ml_per_s = 2 + (level * 8)  # 2-10 mL/s based on level
            
            rate = SEScalarVolumePerTime()
            rate.set_value(rate_ml_per_s, VolumePerTimeUnit.mL_Per_s)
            fluid_admin.set_rate(rate)
            
            # Execute the action
            self.engine.process_action(fluid_admin)
            
            # Log the action
            print(f"Applied hydration ({volume_ml:.0f} mL at {rate_ml_per_s:.1f} mL/s)")
            
            return True
            
        except Exception as e:
            print(f"Error applying hydration: {e}")
            return False
            
        except Exception as e:
            logger.error(f"Error applying hydration intervention: {e}")
    
    def _apply_electrolyte_intervention(self, level):
        """
        Apply electrolyte effects to the Pulse Engine
        
        Args:
            pulse_engine: The initialized Pulse Engine instance
            level: Value from 0.0 to 1.0 indicating intervention level
        """
        if not self.engine or level < 0.1:
            return False
            
        try:
            # Create a compound infusion for sodium and potassium
            # Create sodium compound infusion
            sodium_compound = SESubstanceCompound()
            sodium_compound.set_name("Sodium")
            
            # Set sodium concentration
            na_concentration = SEScalarMassPerVolume()
            # Typical sports drink has ~20-30 mmol/L sodium
            # 1 mmol Na = ~23 mg, so ~460-690 mg/L
            na_concentration_mg_per_L = 500 * level  # 50-500 mg/L based on level
            na_concentration.set_value(na_concentration_mg_per_L, MassPerVolumeUnit.mg_Per_L)
            sodium_compound.set_concentration(na_concentration)
            
            # Create the sodium infusion
            sodium_infusion = SESubstanceInfusion()
            sodium_infusion.set_substance(sodium_compound)
            
            # Set infusion rate
            rate = SEScalarVolumePerTime()
            # Rate similar to oral fluid intake
            rate.set_value(5, VolumePerTimeUnit.mL_Per_s)  # ~300 mL/min
            sodium_infusion.set_rate(rate)
            
            # Process sodium infusion
            self.engine.process_action(sodium_infusion)
            
            # Similar process for potassium
            # (Would add potassium compound and infusion here)
            
            # Log the action
            print(f"Applied electrolyte intervention (Na+ {na_concentration_mg_per_L:.0f} mg/L)")
            
            return True
            
        except Exception as e:
            print(f"Error applying electrolyte intervention: {e}")
            return False
    
    def _apply_nutrient_intervention(self, level):
        """Apply nutrient effects to the engine"""
        if level < 0.1 or not self.engine:
            return
            
        try:
            # In a real implementation, you would:
            # 1. Create a compound infusion action (glucose, amino acids, etc.)
            # 2. Set the concentration and rate
            # 3. Apply it to the engine
            
            # Record the action for tracking purposes
            self.last_actions['nutrients'] = time.time()
            
            logger.info(f"Applied nutrient intervention to engine with level {level}")
            
        except Exception as e:
            logger.error(f"Error applying nutrient intervention: {e}")
    
    def _apply_medication_intervention(self, level):
        """Apply medication effects to the engine"""
        if level < 0.1 or not self.engine:
            return
            
        try:
            # In a real implementation, you would:
            # 1. Create a drug administration action
            # 2. Set the drug, dose, and route
            # 3. Apply it to the engine
            
            # Record the action for tracking purposes
            self.last_actions['medication'] = time.time()
            
            logger.info(f"Applied medication intervention to engine with level {level}")
            
        except Exception as e:
            logger.error(f"Error applying medication intervention: {e}")
    
    def get_recovery_status(self):
        """
        Get the current recovery status
        
        Returns:
            Dictionary with recovery status information
        """
        with self.lock:
            return {
                'active': self.active,
                'severity': self.severity,
                'recovery_progress': self.recovery_progress,
                'interventions': self.interventions.copy(),
                'elapsed_time': time.time() - self.start_time if self.active else 0
            }
    
    def update_recovery_progress(self):
        """
        Update recovery progress based on elapsed time and interventions
        
        Returns:
            Current recovery progress (0.0 to 1.0)
        """
        if not self.active:
            return 0.0
            
        with self.lock:
            current_time = time.time()
            time_delta = current_time - self.last_update_time
            self.last_update_time = current_time
            
            # Calculate recovery rate based on interventions
            recovery_rate = 0.0
            for intervention, level in self.interventions.items():
                recovery_rate += level * self.recovery_multipliers[intervention]
            
            # Scale by severity (higher severity = slower recovery)
            recovery_rate = recovery_rate / (1.0 + self.severity)
            
            # Update progress (time-based)
            # Base rate: fully recover in about 24 hours (86400 seconds) without interventions
            base_rate = 1.0 / 86400.0  # progress per second
            
            # Enhanced rate with interventions
            enhanced_rate = base_rate * (1.0 + recovery_rate * 5.0)  # Up to 6x faster with optimal interventions
            
            # Update progress
            progress_delta = enhanced_rate * time_delta
            self.recovery_progress = min(1.0, self.recovery_progress + progress_delta)
            
            # If fully recovered, deactivate
            if self.recovery_progress >= 0.99:
                self.recovery_progress = 1.0
                self.active = False
                logger.info("Hangover recovery complete")
                
            return self.recovery_progress
    
    def apply_to_engine(self):
        """
        Apply the current hangover state and interventions to the Pulse Engine
        
        Returns:
            True if state was applied, False otherwise
        """
        if self.engine is None or not self.active:
            return False
            
        try:
            # Update recovery progress
            self.update_recovery_progress()
            
            # Calculate current hangover effect (decreases as recovery progresses)
            hangover_effect = self.severity * (1.0 - self.recovery_progress)
            
            # Check if we need to apply any physiological effects
            # Only apply at certain intervals to avoid overloading the engine
            current_time = time.time()
            
            # Apply rest effect based on the rest intervention level
            rest_level = self.interventions.get('rest', 0.0)
            self._apply_rest_effect(rest_level)
            
            # Apply exercise effect based on the exercise intervention level
            exercise_level = self.interventions.get('exercise', 0.0)
            self._apply_exercise_effect(exercise_level)
            
            return True
                
        except Exception as e:
            logger.error(f"Error applying hangover state to engine: {e}")
            
        return False
    
    def _apply_rest_effect(self, level):
        """Apply rest effects to the engine"""
        # Rest lowers metabolic rate and energy demands
        # In a real implementation, you would modify metabolic modifiers
        pass
    
    def _apply_exercise_effect(self, level):
        """Apply exercise effects to the engine"""
        # Exercise increases cardiac output, respiration, and metabolism
        # In a real implementation, you would use the exercise action
        pass