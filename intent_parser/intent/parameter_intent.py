from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.utils.id_provider import IdProvider
import intent_parser.utils.opil_parameter_utils as parameter_utils
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

    def get_default_parameters(self) -> dict:
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
        if self._base_dir is None:
            raise IntentParserException('%s is missing a value' % ip_constants.PARAMETER_BASE_DIR)

        base_dir_field, base_dir_value = self._create_opil_base_dir()
        parameters_fields.append(base_dir_field)
        parameter_values.append(base_dir_value)

        xplan_reactor_field, xplan_reactor_value = self._create_opil_xplan_reactor()
        parameters_fields.append(xplan_reactor_field)
        parameter_values.append(xplan_reactor_value)

        if self._plate_size is None:
            raise IntentParserException('%s is missing a value' % ip_constants.PARAMETER_PLATE_SIZE)

        plate_size_field, plate_size_value = self._create_opil_plate_size()
        parameters_fields.append(plate_size_field)
        parameter_values.append(plate_size_value)

        if self._protocol_name is None:
            raise IntentParserException('%s is missing a value' % ip_constants.PARAMETER_PROTOCOL_NAME)

        protocol_name_field, protocol_name_value = self._create_opil_protocol_name()
        parameters_fields.append(protocol_name_field)
        parameter_values.append(protocol_name_value)

        if self._plate_number is None:
            raise IntentParserException('%s is missing a value' % ip_constants.PARAMETER_PLATE_NUMBER)

        plate_number_field, plate_number_value = self._create_opil_plate_number()
        parameters_fields.append(plate_number_field)
        parameter_values.append(plate_number_value)

        container_fields, container_values = self._create_opil_container_search_string()
        parameters_fields.extend(container_fields)
        parameter_values.extend(container_values)

        if self._strain_property is None:
            raise IntentParserException('%s is missing a value' % ip_constants.PARAMETER_STRAIN_PROPERTY)

        strain_property_field, strain_property_value = self._create_opil_strain_property()
        parameters_fields.append(strain_property_field)
        parameter_values.append(strain_property_value)

        if self._xplan_path is None:
            raise IntentParserException('%s is missing a value' % ip_constants.PARAMETER_XPLAN_PATH)

        xplan_path_field, xplan_path_value = self._create_xplan_path()
        parameters_fields.append(xplan_path_field)
        parameter_values.append(xplan_path_value)

        submit_field, submit_value = self._create_opil_submit()
        parameters_fields.append(submit_field)
        parameter_values.append(submit_value)

        if self._protocol_id is None:
            raise IntentParserException('%s is missing a value' % ip_constants.PARAMETER_PROTOCOL_ID)

        protocol_id_field, protocol_id_value = self._create_opil_protocol_id()
        parameters_fields.append(protocol_id_field)
        parameter_values.append(protocol_id_value)

        test_mode_field, test_mode_value = self._create_opil_test_mode()
        parameters_fields.append(test_mode_field)
        parameter_values.append(test_mode_value)

        if self._experiment_reference_url_for_xplan is None:
            raise IntentParserException('%s is missing a value' % ip_constants.PARAMETER_EXPERIMENT_REFERENCE_URL_FOR_XPLAN)

        experiment_ref_url_for_xplan_field, experiment_ref_url_for_xplan_value = self._create_opil_experiment_url_for_xplan()
        parameters_fields.append(experiment_ref_url_for_xplan_field)
        parameter_values.append(experiment_ref_url_for_xplan_value)

        return parameters_fields, parameter_values

    def _create_opil_base_dir(self):
        parameter_field = parameter_utils.create_opil_string_parameter_field(self._id_provider.get_unique_sd2_id(),
                                                                             ip_constants.PARAMETER_BASE_DIR)
        parameter_value = parameter_utils.create_opil_string_parameter_value(self._id_provider.get_unique_sd2_id(),
                                                                             self._base_dir)
        parameter_value.value_of = parameter_field
        # todo: when to assign parameter field default_value?
        parameter_field.default_value = parameter_value
        return parameter_field, parameter_value

    def _create_opil_container_search_string(self):
        parameter_fields = []
        parameter_values = []

        if self._container_search_strings == dc_constants.GENERATE:
            parameter_field = parameter_utils.create_opil_enumerated_parameter_field(self._id_provider.get_unique_sd2_id(),
                                                                                     ip_constants.PARAMETER_CONTAINER_SEARCH_STRING)
            parameter_value = parameter_utils.create_opil_enumerated_parameter_value(self._id_provider.get_unique_sd2_id(),
                                                                                     dc_constants.GENERATE)
            parameter_value.value_of = parameter_field
            # todo: when to assign parameter field default_value?
            parameter_field.default_value = parameter_value
            parameter_fields.append(parameter_field)
            parameter_values.append(parameter_value)
        else:
            for value_index in range(len(self._container_search_strings)):
                parameter_field = parameter_utils.create_opil_string_parameter_field(self._id_provider.get_unique_sd2_id(),
                                                                                     ip_constants.PARAMETER_CONTAINER_SEARCH_STRING)
                parameter_value = parameter_utils.create_opil_string_parameter_value(self._id_provider.get_unique_sd2_id(),
                                                                                     self._container_search_strings[value_index])
                parameter_value.value_of = parameter_field
                # todo: when to assign parameter field default_value?
                parameter_field.default_value = parameter_value
                parameter_fields.append(parameter_field)
                parameter_values.append(parameter_value)

        return parameter_fields, parameter_values

    def _create_opil_experiment_url_for_xplan(self):
        parameter_field = parameter_utils.create_opil_string_parameter_field(self._id_provider.get_unique_sd2_id(),
                                                                             ip_constants.PARAMETER_EXPERIMENT_REFERENCE_URL_FOR_XPLAN)
        parameter_value = parameter_utils.create_opil_string_parameter_value(self._id_provider.get_unique_sd2_id(),
                                                                             self._experiment_reference_url_for_xplan)
        parameter_value.value_of = parameter_field
        # todo: when to assign parameter field default_value?
        parameter_field.default_value = parameter_value
        return parameter_field, parameter_value


    def _create_opil_plate_number(self):
        parameter_field = parameter_utils.create_opil_integer_parameter_field(self._id_provider.get_unique_sd2_id(),
                                                                              ip_constants.PARAMETER_PLATE_NUMBER)
        parameter_value = parameter_utils.create_opil_integer_parameter_value(self._id_provider.get_unique_sd2_id(),
                                                                              self._plate_number)
        parameter_value.value_of = parameter_field
        # todo: when to assign parameter field default_value?
        parameter_field.default_value = parameter_value
        return parameter_field, parameter_value

    def _create_opil_plate_size(self):
        parameter_field = parameter_utils.create_opil_integer_parameter_field(self._id_provider.get_unique_sd2_id(),
                                                                              ip_constants.PARAMETER_PLATE_SIZE)
        parameter_value = parameter_utils.create_opil_integer_parameter_value(self._id_provider.get_unique_sd2_id(),
                                                                              self._plate_size)
        parameter_value.value_of = parameter_field
        # todo: when to assign parameter field default_value?
        parameter_field.default_value = parameter_value
        return parameter_field, parameter_value

    def _create_opil_protocol_id(self):
        parameter_field = parameter_utils.create_opil_string_parameter_field(self._id_provider.get_unique_sd2_id(),
                                                                             ip_constants.PARAMETER_PROTOCOL_ID)
        parameter_value = parameter_utils.create_opil_string_parameter_value(self._id_provider.get_unique_sd2_id(),
                                                                             self._protocol_id)
        parameter_value.value_of = parameter_field
        # todo: when to assign parameter field default_value?
        parameter_field.default_value = parameter_value
        return parameter_field, parameter_value

    def _create_opil_protocol_name(self):
        parameter_field = parameter_utils.create_opil_string_parameter_field(self._id_provider.get_unique_sd2_id(),
                                                                             ip_constants.PARAMETER_PROTOCOL_NAME)
        parameter_value = parameter_utils.create_opil_string_parameter_value(self._id_provider.get_unique_sd2_id(),
                                                                             self._protocol_name)
        parameter_value.value_of = parameter_field
        # todo: when to assign parameter field default_value?
        parameter_field.default_value = parameter_value
        return parameter_field, parameter_value

    def _create_opil_strain_property(self):
        parameter_field = parameter_utils.create_opil_string_parameter_field(self._id_provider.get_unique_sd2_id(),
                                                                             ip_constants.PARAMETER_STRAIN_PROPERTY)
        parameter_value = parameter_utils.create_opil_string_parameter_value(self._id_provider.get_unique_sd2_id(),
                                                                             self._strain_property)
        parameter_value.value_of = parameter_field
        # todo: when to assign parameter field default_value?
        parameter_field.default_value = parameter_value
        return parameter_field, parameter_value

    def _create_opil_submit(self):
        parameter_field = parameter_utils.create_opil_boolean_parameter_field(self._id_provider.get_unique_sd2_id(),
                                                                              ip_constants.PARAMETER_SUBMIT)
        parameter_value = parameter_utils.create_opil_boolean_parameter_value(self._id_provider.get_unique_sd2_id(),
                                                                              self._submit)
        parameter_value.value_of = parameter_field
        # todo: when to assign parameter field default_value?
        parameter_field.default_value = parameter_value
        return parameter_field, parameter_value

    def _create_opil_test_mode(self):
        parameter_field = parameter_utils.create_opil_boolean_parameter_field(self._id_provider.get_unique_sd2_id(),
                                                                              ip_constants.PARAMETER_TEST_MODE)
        parameter_value = parameter_utils.create_opil_boolean_parameter_value(self._id_provider.get_unique_sd2_id(),
                                                                              self._test_mode)
        parameter_value.value_of = parameter_field
        # todo: when to assign parameter field default_value?
        parameter_field.default_value = parameter_value
        return parameter_field, parameter_value

    def _create_xplan_path(self):
        parameter_field = parameter_utils.create_opil_string_parameter_field(self._id_provider.get_unique_sd2_id(),
                                                                             ip_constants.PARAMETER_XPLAN_PATH)
        parameter_value = parameter_utils.create_opil_string_parameter_value(self._id_provider.get_unique_sd2_id(),
                                                                             self._xplan_path)
        parameter_value.value_of = parameter_field
        # todo: when to assign parameter field default_value?
        parameter_field.default_value = parameter_value
        return parameter_field, parameter_value

    def _create_opil_xplan_reactor(self):
        parameter_field = parameter_utils.create_opil_string_parameter_field(self._id_provider.get_unique_sd2_id(),
                                                                             ip_constants.PARAMETER_XPLAN_REACTOR)
        parameter_value = parameter_utils.create_opil_string_parameter_value(self._id_provider.get_unique_sd2_id(),
                                                                             self._xplan_reactor)
        parameter_value.value_of = parameter_field
        # todo: when to assign parameter field default_value?
        parameter_field.default_value = parameter_value
        return parameter_field, parameter_value

