from intent_parser.constants import sd2_datacatalog_constants as dc_constants, intent_parser_constants as ip_constants

class LabIntent(object):

    def __init__(self):
        self._lab_id = ip_constants.TACC_SERVER
        self._experiment_id = 'TBD'

    def get_experiment_id(self):
        return self._experiment_id

    def get_lab_name(self) -> str:
        return self._lab_id

    def set_experiment_id(self, experiment_id: str):
        self._experiment_id = experiment_id

    def set_lab_id(self, lab_name):
        self._lab_id = lab_name

    def to_structured_request(self):
        return {dc_constants.LAB: self._lab_id,
                dc_constants.EXPERIMENT_ID: 'experiment.%s.%s' % (self._lab_id.lower(),
                                                                  self._experiment_id)}