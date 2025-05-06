from enum import Enum
import logging
from pulse.engine.PulseEngine import PulseEngine
from pulse.cdm.engine import SEDataRequestManager
from pulse.cdm.patient import SEPatientConfiguration
from pulse.cdm.io.patient import serialize_patient_from_file
from pulse.cdm.scalars import TimeUnit, LengthUnit, MassUnit, FrequencyUnit, PressureUnit, TemperatureUnit

class eStartType(Enum):
    State = 0
    Stabilize_PatientFile = 1
    Stabilize_PatientObject = 2

class PatientConfiguration:
    def __init__(self, pulse: PulseEngine, data_req_mgr: SEDataRequestManager, start_type: eStartType):
        self.start_type = start_type
        self.pc = SEPatientConfiguration()
        self._load_config(pulse, data_req_mgr, start_type)

    def _load_config(self, pulse: PulseEngine, data_req_mgr: SEDataRequestManager, start_type: eStartType):
        if start_type is eStartType.State: # The engine is ready instantaneously
            if not pulse.serialize_from_file("./data/states/StandardMale@0s.json", data_req_mgr):
                logging.error("Unable to load initial state file")
                return
        elif start_type is eStartType.Stabilize_PatientFile or \
        start_type is eStartType.Stabilize_PatientObject:
            if start_type is eStartType.Stabilize_PatientFile:
                self.pc.set_patient_file("./data/patients/Soldier.json")
            elif start_type is eStartType.Stabilize_PatientObject:
                p = self.pc.get_patient()
                # You only need to set sex and all other properties will be computed
                # per https://pulse.kitware.com/_patient_methodology.html
                serialize_patient_from_file("./data/patients/Soldier.json", p)
                # Now let's modify a few properties
                p.set_name("Wenye")
                p.get_age().set_value(22,TimeUnit.yr)
                p.get_height().set_value(72, LengthUnit.inch)
                p.get_weight().set_value(180, MassUnit.lb)
                p.get_heart_rate_baseline().set_value(72, FrequencyUnit.Per_min)
                p.get_systolic_arterial_pressure_baseline().set_value(117, PressureUnit.mmHg)
                p.get_diastolic_arterial_pressure_baseline().set_value(72, PressureUnit.mmHg)
                p.get_respiration_rate_baseline().set_value(12, FrequencyUnit.Per_min)

    def has_patient_file(self):
        """Check if a patient file has been set"""
        return self.pc is not None and self.pc.has_patient_file()

    def has_patient(self):
        """Check if a patient has been set"""
        return self.pc is not None and self.pc.has_patient()

    def has_conditions(self):
        """Check if any conditions have been set"""
        return self.pc is not None and self.pc.has_conditions()

    def get_patient(self):
        """Get the patient object"""
        return self.pc.get_patient() if self.pc is not None else None

    def get_patient_configuration(self):
        """Get the underlying SEPatientConfiguration object"""
        return self.pc

    def get_data_root_dir(self):
        """Get the data root directory path"""
        return "./data"

    def set_data_root_dir(self, path):
        """Set the data root directory path"""
        if self.pc is not None:
            self.pc.set_data_root_dir(path)
