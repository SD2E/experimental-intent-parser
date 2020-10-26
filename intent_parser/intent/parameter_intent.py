import intent_parser.protocols.opil_parameter_utils as parameter_utils
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.constants.intent_parser_constants as ip_constants

class ExperimentIntent(object):

    def __init__(self, submit_experiment: bool = False, xplan_reactor: str = 'xplan', test_mode: bool = True):
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

    def add_parameter(self, field, value):
        self._default_parameters[field] = value

    def get_default_parameters(self):
        return self._default_parameters

    def get_protocol_name(self):
        return self._protocol_name

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

    def to_opil_for_experiment(self):
        parameters_fields = []
        parameter_values = []
        base_dir_field, base_dir_value = self._create_opil_base_dir()
        parameters_fields.extend(base_dir_field)
        parameter_values.extend(base_dir_value)

        xplan_reactor_field, xplan_reactor_value = self._create_opil_xplan_reactor()
        parameters_fields.extend(xplan_reactor_field)
        parameter_values.extend(xplan_reactor_value)

        plate_size_field, plate_size_value = self._create_opil_plate_size()
        parameters_fields.extend(plate_size_field)
        parameter_values.extend(plate_size_value)

        protocol_name_field, protocol_name_value = self._create_opil_protocol_name()
        parameters_fields.extend(protocol_name_field)
        parameter_values.extend(protocol_name_value)

        plate_number_field, plate_number_value = self._create_opil_plate_number()
        parameters_fields.extend(plate_number_field)
        parameter_values.extend(plate_number_value)

        container_fields, container_values = self._create_opil_container_search_string()
        parameters_fields.extend(container_fields)
        parameter_values.extend(container_values)

        strain_property_field, strain_property_value = self._create_opil_strain_property()
        parameters_fields.extend(strain_property_field)
        parameter_values.extend(strain_property_value)

        xplan_path_field, xplan_path_value = self._create_xplan_path()
        parameters_fields.extend(xplan_path_field)
        parameter_values.extend(xplan_path_value)

        submit_field, submit_value = self._create_opil_submit()
        parameters_fields.extend(submit_field)
        parameter_values.extend(submit_value)

        protocol_id_field, protocol_id_value = self._create_opil_protocol_id()
        parameters_fields.extend(protocol_id_field)
        parameter_values.extend(protocol_id_value)

        test_mode_field, test_mode_value = self._create_opil_test_mode()
        parameters_fields.extend(test_mode_field)
        parameter_values.extend(test_mode_value)

        experiment_ref_url_for_xplan_field, experiment_ref_url_for_xplan_value = self._create_opil_experiment_url_for_xplan()
        parameters_fields.extend(experiment_ref_url_for_xplan_field)
        parameter_values.extend(experiment_ref_url_for_xplan_value)

        return parameters_fields, parameter_values

    def _create_opil_base_dir(self):
        if not self._base_dir:
            return [], []
        parameter_field = parameter_utils.create_opil_string_parameter_field('%s_field_id' % ip_constants.PARAMETER_BASE_DIR,
                                                                             ip_constants.PARAMETER_BASE_DIR)
        parameter_value = parameter_utils.create_opil_string_parameter_value('%s_value_id' % ip_constants.PARAMETER_BASE_DIR,
                                                                             self._base_dir)
        parameter_field.default_value = [parameter_value]
        return [parameter_field], [parameter_value]

    def _create_opil_container_search_string(self):
        parameter_fields = []
        parameter_values = []

        if self._container_search_strings == dc_constants.GENERATE:
            parameter_field = parameter_utils.create_opil_enumerated_parameter_field('%s_field_id' % ip_constants.PARAMETER_CONTAINER_SEARCH_STRING,
                                                                                     ip_constants.PARAMETER_CONTAINER_SEARCH_STRING)
            parameter_value = parameter_utils.create_opil_enumerated_parameter_value('%s_value_id' % (ip_constants.PARAMETER_CONTAINER_SEARCH_STRING),
                                                                                     dc_constants.GENERATE)
            parameter_field.default_value = [parameter_value]
            parameter_fields.append(parameter_field)
            parameter_values.append(parameter_value)
        else:
            for value_index in range(len(self._container_search_strings)):
                parameter_field = parameter_utils.create_opil_string_parameter_field('%s_%d_field_id' % (ip_constants.PARAMETER_CONTAINER_SEARCH_STRING, value_index),
                                                                                         ip_constants.PARAMETER_CONTAINER_SEARCH_STRING)
                parameter_value = parameter_utils.create_opil_string_parameter_value('%s_%d_value_id' % (ip_constants.PARAMETER_CONTAINER_SEARCH_STRING, value_index),
                                                                                         self._container_search_strings[value_index])
                parameter_field.default_value = [parameter_value]
                parameter_fields.append(parameter_field)
                parameter_values.append(parameter_value)

        return parameter_fields, parameter_values

    def _create_opil_experiment_url_for_xplan(self):
        if not self._experiment_reference_url_for_xplan:
            return [], []

        parameter_field = parameter_utils.create_opil_string_parameter_field('%s_field_id' % ip_constants.PARAMETER_EXPERIMENT_REFERENCE_URL_FOR_XPLAN,
                                                                             ip_constants.PARAMETER_EXPERIMENT_REFERENCE_URL_FOR_XPLAN)
        parameter_value = parameter_utils.create_opil_string_parameter_value('%s_value_id' % ip_constants.PARAMETER_EXPERIMENT_REFERENCE_URL_FOR_XPLAN,
                                                                             self._experiment_reference_url_for_xplan)
        parameter_field.default_value = [parameter_value]
        return [parameter_field], [parameter_value]


    def _create_opil_plate_number(self):
        if not self._plate_number:
            return [], []

        parameter_field = parameter_utils.create_opil_integer_parameter_field('%s_field_id' % ip_constants.PARAMETER_PLATE_NUMBER,
                                                                              ip_constants.PARAMETER_PLATE_NUMBER)
        parameter_value = parameter_utils.create_opil_integer_parameter_value('%s_value_id' % ip_constants.PARAMETER_PLATE_NUMBER,
                                                                              self._plate_number)
        parameter_field.default_value = [parameter_value]
        return [parameter_field], [parameter_value]

    def _create_opil_plate_size(self):
        if not self._plate_size:
            return [], []
        parameter_field = parameter_utils.create_opil_integer_parameter_field('%s_field_id' % ip_constants.PARAMETER_PLATE_SIZE,
                                                                              ip_constants.PARAMETER_PLATE_SIZE)
        parameter_value = parameter_utils.create_opil_integer_parameter_value('%s_value_id' % ip_constants.PARAMETER_PLATE_SIZE,
                                                                              self._plate_size)
        parameter_field.default_value = [parameter_value]
        return [parameter_field], [parameter_value]

    def _create_opil_protocol_id(self):
        if not self._protocol_id:
            return [], []
        parameter_field = parameter_utils.create_opil_string_parameter_field('%s_field_id' % ip_constants.PARAMETER_PROTOCOL_ID,
                                                                             ip_constants.PARAMETER_PROTOCOL_ID)
        parameter_value = parameter_utils.create_opil_string_parameter_value('%s_value_id' % ip_constants.PARAMETER_PROTOCOL_ID,
                                                                             self._protocol_id)
        parameter_field.default_value = [parameter_value]
        return [parameter_field], [parameter_value]

    def _create_opil_protocol_name(self):
        if not self._protocol_name:
            return [], []
        parameter_field = parameter_utils.create_opil_string_parameter_field('%s_field_id' % ip_constants.PARAMETER_PROTOCOL_NAME,
                                                                             ip_constants.PARAMETER_PROTOCOL_NAME)
        parameter_value = parameter_utils.create_opil_string_parameter_value('%s_value_id' % ip_constants.PARAMETER_PROTOCOL_NAME,
                                                                             self._protocol_name)
        parameter_field.default_value = [parameter_value]
        return [parameter_field], [parameter_value]

    def _create_opil_strain_property(self):
        if not self._strain_property:
            return [], []
        parameter_field = parameter_utils.create_opil_string_parameter_field('%s_field_id' % ip_constants.PARAMETER_STRAIN_PROPERTY,
                                                                             ip_constants.PARAMETER_STRAIN_PROPERTY)
        parameter_value = parameter_utils.create_opil_string_parameter_value('%s_value_id' % ip_constants.PARAMETER_STRAIN_PROPERTY,
                                                                             self._strain_property)
        return [parameter_field], [parameter_value]

    def _create_opil_submit(self):
        parameter_field = parameter_utils.create_opil_boolean_parameter_field('%s_field_id' % ip_constants.PARAMETER_SUBMIT,
                                                                              ip_constants.PARAMETER_SUBMIT)
        parameter_value = parameter_utils.create_opil_boolean_parameter_value('%s_value_id' % ip_constants.PARAMETER_SUBMIT,
                                                                              self._submit)
        parameter_field.default_value = [parameter_value]
        return [parameter_field], [parameter_value]

    def _create_opil_test_mode(self):
        parameter_field = parameter_utils.create_opil_boolean_parameter_field('%s_field_id' % ip_constants.PARAMETER_TEST_MODE,
                                                                              ip_constants.PARAMETER_TEST_MODE)
        parameter_value = parameter_utils.create_opil_boolean_parameter_value('%s_value_id' % ip_constants.PARAMETER_TEST_MODE, self._test_mode)
        parameter_field.default_value = [parameter_value]
        return [parameter_field], [parameter_value]

    def _create_xplan_path(self):
        if not self._xplan_path:
            return [], []

        parameter_field = parameter_utils.create_opil_string_parameter_field('%s_field_id' % ip_constants.PARAMETER_XPLAN_PATH,
                                                                             ip_constants.PARAMETER_XPLAN_PATH)
        parameter_value = parameter_utils.create_opil_string_parameter_value('%s_value_id' % ip_constants.PARAMETER_XPLAN_PATH,
                                                                             self._xplan_path)
        parameter_field.default_value = [parameter_value]
        return [parameter_field], [parameter_value]

    def _create_opil_xplan_reactor(self):
        parameter_field = parameter_utils.create_opil_string_parameter_field('%s_field_id' % ip_constants.PARAMETER_XPLAN_REACTOR,
                                                                             ip_constants.PARAMETER_XPLAN_REACTOR)
        parameter_value = parameter_utils.create_opil_string_parameter_value('%s_value_id' % ip_constants.PARAMETER_XPLAN_REACTOR,
                                                                             self._xplan_reactor)
        parameter_field.default_value = [parameter_value]
        return [parameter_field], [parameter_value]

