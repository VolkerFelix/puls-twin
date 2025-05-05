from .base import OutputChannel

class ConsoleOutputChannel(OutputChannel):
    """Outputs avatar state to console for debugging/demo"""
    
    def update_avatar_state(self, state_record):
        """Print avatar state to console"""
        state = state_record['primary_state']
        description = state_record['state_description']
        
        # Create a formatted output
        print("\n" + "="*50)
        print(f"AVATAR STATE: {description}")
        print("="*50)
        
        # Print key physiological values
        print("\nKEY PHYSIOLOGICAL VALUES:")
        values = state_record['physiological_values']
        print(f"  Heart Rate: {values.get('heart_rate', 'N/A')} bpm")
        print(f"  Blood Pressure: {values.get('systolic_pressure', 'N/A')}/{values.get('diastolic_pressure', 'N/A')} mmHg")
        print(f"  Cardiac Output: {values.get('cardiac_output', 'N/A')} L/min")
        print(f"  Oxygen Saturation: {values.get('oxygen_saturation', 'N/A')}%")
        print(f"  HRV: {values.get('hrv', 'N/A')} ms")
        print(f"  Respiratory Rate: {values.get('respiratory_rate', 'N/A')} breaths/min")
        
        # Print all active states
        print("\nACTIVE STATES:")
        for state_name, is_active in state_record['all_states'].items():
            if is_active:
                print(f"  • {state_name}")
        print()