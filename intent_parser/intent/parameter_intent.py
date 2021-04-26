from intent_parser.utils.id_provider import IdProvider
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.constants.intent_parser_constants as ip_constants

class ParameterIntent(object):

    def __init__(self, submit_experiment: bool = True, xplan_reactor: str = 'xplan', test_mode: bool = False):
        self._base_dir = None
        self._xplan_reactor = xplan_reactor
        self._plate_size = None
        self._protocol_name = None
        self._plate_number = None
        self._container_search_strings = dc_constants.GENERATE
        self._strain_property = None
        self._xplan_path = None
        self._submit = submit_experiment
        self._protocol_id = None
        self._test_mode = test_mode
        self._experiment_reference_url_for_xplan = None
        self._default_parameters = {}
        self._id_provider = IdProvider()

    def add_parameter(self, field, value):
        self._default_parameters[field] = value

    def get_container_search_string(self):
        return self._container_search_strings

    def get_default_parameters(self) -> dict:
        return self._default_parameters

    def get_experiment_ref_url(self):
        return self._experiment_reference_url_for_xplan

    def get_plate_number(self):
        return self._plate_number

    def get_plate_size(self):
        return self._plate_size

    def get_protocol_id(self):
        return self._protocol_id

    def get_protocol_name(self):
        return self._protocol_name

    def get_strain_property(self):
        return self._strain_property

    def get_submit_flag(self):
        return self._submit

    def get_test_mode(self):
        return self._test_mode

    def get_xplan_base_dir(self):
        return self._base_dir

    def get_xplan_path(self):
        return self._xplan_path

    def get_xplan_reactor(self):
        return self._xplan_reactor

    def set_base_dir(self, value: str):
        self._base_dir = value

    def set_container_search_strain(self, value: list):
        self._container_search_strings = value

    def set_experiment_reference_url_for_xplan(self, value: str):
        self._experiment_reference_url_for_xplan = value

    def set_plate_number(self, value: int):
        self._plate_number = value

    def set_plate_size(self, value: int):
        self._plate_size = value

    def set_protocol_id(self, value: str):
        self._protocol_id = value

    def set_protocol_name(self, value: str):
        self._protocol_name = value

    def set_strain_property(self, value: str):
        self._strain_property = value

    def set_submit(self, value: bool):
        self._submit = value

    def set_test_mode(self, value: bool):
        self._test_mode = value

    def set_xplan_path(self, value: str):
        self._xplan_path = value

    def set_xplan_reactor(self, value: str):
        self._xplan_reactor = value

    def size_of_default_parameters(self):
        return len(self._default_parameters)

    def to_structure_request(self):
        return self._default_parameters

    def to_experiment_structured_request(self) -> dict:
        return {
            ip_constants.PARAMETER_BASE_DIR: self._base_dir,
            ip_constants.PARAMETER_XPLAN_REACTOR: self._xplan_reactor,
            ip_constants.PARAMETER_PLATE_SIZE: self._plate_size,
            ip_constants.PARAMETER_PROTOCOL_NAME: self._protocol_name,
            ip_constants.PARAMETER_PLATE_NUMBER: self._plate_number,
            ip_constants.PARAMETER_CONTAINER_SEARCH_STRING: self._container_search_strings,
            ip_constants.PARAMETER_STRAIN_PROPERTY: self._strain_property,
            ip_constants.PARAMETER_XPLAN_PATH: self._xplan_path,
            ip_constants.PARAMETER_SUBMIT: self._submit,
            ip_constants.PARAMETER_PROTOCOL_ID: self._protocol_id,
            ip_constants.PARAMETER_TEST_MODE: self._test_mode,
            ip_constants.PARAMETER_EXPERIMENT_REFERENCE_URL_FOR_XPLAN: self._experiment_reference_url_for_xplan,
            ip_constants.DEFAULT_PARAMETERS: self._default_parameters
        }
