import os
import sys
import time
import json
import logging
from threading import Lock

# Import our previously defined components
from wearable.processor import WearableDataProcessor
from pulse.simulation import PulseSimulationController
from avatar.state_manager import AvatarStateManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WearableTwinSystem")

class OutputChannel:
    """Base class for avatar state output channels"""
    
    def update_avatar_state(self, state_record):
        """
        Update with new avatar state
        Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement update_avatar_state")