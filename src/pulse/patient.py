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
        self.pc = None
        self._load_config(pulse, data_req_mgr, start_type)

    def _load_config(self, pulse: PulseEngine, data_req_mgr: SEDataRequestManager, start_type: eStartType):
        if start_type is eStartType.State: # The engine is ready instantaneously
            if not pulse.serialize_from_file("./data/states/StandardMale@0s.json", data_req_mgr):
                logging.error("Unable to load initial state file")
                return
        elif start_type is eStartType.Stabilize_PatientFile or \
        start_type is eStartType.Stabilize_PatientObject:
            self.pc = SEPatientConfiguration()
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
