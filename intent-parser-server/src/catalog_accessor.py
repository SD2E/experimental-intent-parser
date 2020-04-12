import json
import urllib.request

class CatalogAccessor(object):
    '''
    An accessor to get information from sd2e's catalog.
    '''
    _CHALLENGE_PROBLEM_URL = 'https://schema.catalog.sd2e.org/schemas/challenge_problem_id.json'
    _FILE_TYPES_URL = 'https://schema.catalog.sd2e.org/schemas/filetype_label.json'
    _FLUID_UNITS_URL = 'https://schema.catalog.sd2e.org/schemas/fluid_unit.json'
    _MEASUREMENT_TYPES_URL = 'https://schema.catalog.sd2e.org/schemas/measurement_type.json'
    _TEMPERATURE_UNITS_URL = 'https://schema.catalog.sd2e.org/schemas/temperature_unit.json'
    _TIME_UNITS_URL = 'https://schema.catalog.sd2e.org/schemas/time_unit.json'
    _VOLUME_UNITS_URL = 'https://schema.catalog.sd2e.org/schemas/volume_unit.json'
    _LAB_IDS_URL = 'https://schema.catalog.sd2e.org/schemas/lab.json'
    
    def __init__(self):
        self.challenge_problem_ids = None
        self.file_types = None
        self.fluid_units = None
        self.lab_ids = None
        self.measurement_types = None
        self.temperature_units = None
        self.time_units = None
        self.volume_units = None
    
    def get_challenge_problem_ids(self):
        if self.challenge_problem_ids is None:
            data = self._fetch_from_catalog(self._CHALLENGE_PROBLEM_URL)
            self.challenge_problem_ids = []
            for d in data['enum']:
                self.challenge_problem_ids.append(d)
                
        return self.challenge_problem_ids
    
    def get_file_types(self):
        if self.file_types is None:
            data = self._fetch_from_catalog(self._FILE_TYPES_URL)
            self.file_types = []
            for d in data['enum']:
                self.file_types.append(d)
                
        return self.file_types 
    
    def get_fluid_units(self):
        if self.fluid_units is None:
            data = self._fetch_from_catalog(self._FLUID_UNITS_URL)
            self.fluid_units = []
            for d in data['enum']:
                self.fluid_units.append(d)
                
        return self.fluid_units
    
    def get_lab_ids(self):
        if self.lab_ids is None:
            data = self._fetch_from_catalog(self._LAB_IDS_URL)
            self.lab_ids = []
            for d in data['enum']:
                self.lab_ids.append(d)
            self.lab_ids.sort()
             
        return self.lab_ids
    
    def get_measurement_types(self):
        if self.measurement_types is None:
            data = self._fetch_from_catalog(self._MEASUREMENT_TYPES_URL)
            self.measurement_types = []
            for d in data['enum']:
                self.measurement_types.append(d)
                
        return self.measurement_types
    
    def get_temperature_units(self):
        if self.temperature_units is None:
            data = self._fetch_from_catalog(self._TEMPERATURE_UNITS_URL)
            self.temperature_units = []
            for d in data['enum']:
                self.temperature_units.append(d)
                
        return self.temperature_units
        
    
    def get_time_units(self):
        if self.time_units is None:
            data = self._fetch_from_catalog(self._TIME_UNITS_URL)
            self.time_units = []
            for d in data['enum']:
                self.time_units.append(d)
                
        return self.time_units
    
    def get_volume_units(self):
        if self.volume_units is None:
            data = self._fetch_from_catalog(self._VOLUME_UNITS_URL)
            self.volume_units = []
            for d in data['enum']:
                self.volume_units.append(d)
                
        return self.volume_units
     
    def _fetch_from_catalog(self, url):
        response = urllib.request.urlopen(url,timeout=60)
        return json.loads(response.read().decode('utf-8'))

        