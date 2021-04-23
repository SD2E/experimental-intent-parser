from intent_parser.intent.parameter_intent import ParameterIntent
from intent_parser.intent_parser_exceptions import TableException
from json import JSONDecodeError
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.table.cell_parser as cell_parser
import json
import logging

class ParameterTable(object):
    """
    Process information from Intent Parser's Parameter Table
    """

    _logger = logging.getLogger('intent_parser')

    FIELD_WITH_BOOLEAN_VALUE = [intent_parser_constants.PARAMETER_MEASUREMENT_INFO_36_HR_READ,
                                intent_parser_constants.PARAMETER_RUN_INFO_READ_EACH_RECOVER,
                                intent_parser_constants.PARAMETER_RUN_INFO_READ_EACH_INDUCTION,
                                intent_parser_constants.PARAMETER_RUN_INFO_SAVE_FOR_RNASEQ,
                                intent_parser_constants.PARAMETER_RUN_INFO_SKIP_FIRST_FLOW,
                                intent_parser_constants.PARAMETER_RUN_INFO_ONLY_ENDPOINT_FLOW,
                                intent_parser_constants.PARAMETER_VALIDATE_SAMPLES,
                                intent_parser_constants.PARAMETER_RUN_INFO_INCUBATE_IN_READER,
                                intent_parser_constants.PARAMETER_RXN_INFO_RXN_GROUP_INFO_MG_GLU2]

    FIELD_WITH_FLOAT_VALUE = [intent_parser_constants.PARAMETER_PLATE_READER_INFO_GAIN]

    FIELD_WITH_NESTED_STRUCTURE = [intent_parser_constants.PARAMETER_INDUCTION_INFO_REAGENTS,
                                   intent_parser_constants.PARAMETER_INDUCTION_INFO_REAGENTS_INDUCER,
                                   intent_parser_constants.PARAMETER_INDUCTION_INFO_SAMPLING_INFO,
                                   intent_parser_constants.PARAMETER_MEASUREMENT_INFO_FLOW_INFO,
                                   intent_parser_constants.PARAMETER_MEASUREMENT_INFO_PLATE_READER_INFO,
                                   intent_parser_constants.PARAMETER_REAGENT_INFO_INDUCER_INFO,
                                   intent_parser_constants.PARAMETER_REAGENT_INFO_KILL_SWITCH,
                                   intent_parser_constants.PARAMETER_RECOVERY_INFO,
                                   intent_parser_constants.PARAMETER_INDUCERS,
                                   intent_parser_constants.PARAMETER_READER_INFO_LIST_OF_GAINS]

    FIELD_WITH_STRING_COMMAS = [intent_parser_constants.PARAMETER_EXP_INFO_MEDIA_WELL_STRINGS]

    def __init__(self, intent_parser_table, parameter_fields={}, run_as_opil=False):
        self.run_as_opil = run_as_opil

        self._parameter_intent = ParameterIntent()
        self._parameter_fields = parameter_fields
        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table
        self._table_caption = None

    def get_parameter_intent(self):
        return self._parameter_intent

    def get_experiment(self):
        experiment_result = self._parameter_intent.to_experiment_structured_request()
        for key in experiment_result.keys():
            if not experiment_result[key]:
                self._validation_warnings.append('Parameter Table is missing a value for %s.' % key)
        return experiment_result

    def get_structured_request(self):
        return self._parameter_intent.to_structure_request()

    def get_validation_errors(self):
        return self._validation_errors

    def get_validation_warnings(self):
        return self._validation_warnings

    def process_table(self):
        self._table_caption = self._intent_parser_table.caption()
        for row_index in range(self._intent_parser_table.data_row_start_index(),
                               self._intent_parser_table.number_of_rows()):
            self._process_row(row_index)

    def set_experiment_reference_url(self, experiment_ref_url):
        self._parameter_intent.set_experiment_reference_url_for_xplan(experiment_ref_url)

    def _process_row(self, row_index):
        row = self._intent_parser_table.get_row(row_index)
        cell_param_field = None
        cell_param_value = None
        for cell_index in range(len(row)):
            cell = self._intent_parser_table.get_cell(row_index, cell_index)
            # Cell type based on column header
            header_row_index = self._intent_parser_table.header_row_index()
            header_cell = self._intent_parser_table.get_cell(header_row_index, cell_index)
            cell_type = cell_parser.PARSER.get_header_type(header_cell.get_text())

            if intent_parser_constants.HEADER_PARAMETER_TYPE == cell_type:
                cell_param_field = cell
            elif intent_parser_constants.HEADER_PARAMETER_VALUE_TYPE == cell_type:
                cell_param_value = cell

        if ((cell_param_field is None) or (not cell_param_field.get_text().strip())):
            if cell_param_value:
                self._validation_errors.append(
                    'Parameter table cannot assign %s as a parameter value to an empty parameter.' % cell_param_value.get_text())
            return

        if cell_param_field:
            if (cell_param_value is None) or (not cell_param_value.get_text().strip()):
                self._validation_warnings.append(
                    'Skipping %s because no parameter value was assigned.' % cell_param_field.get_text())
                return

        self._parse_parameter(cell_param_field.get_text().strip(),
                              cell_param_value.get_text().strip())

    def _flatten_parameter_values(self, param_field, param_value_list):
        if len(param_value_list) == 0:
            return
        elif len(param_value_list) == 1:
            self._parameter_intent.add_parameter(param_field, param_value_list[0])
            return
        for i in range(len(param_value_list)):
            param_field_id = param_field + '.' + str(i)
            self._parameter_intent.add_parameter(param_field_id, param_value_list[i])

    def _parse_parameter(self, parameter_field: str, parameter_value: str):
        if parameter_field == intent_parser_constants.PROTOCOL_FIELD_XPLAN_BASE_DIRECTORY:
            self._parameter_intent.set_base_dir(parameter_value)
        elif parameter_field == intent_parser_constants.PROTOCOL_FIELD_XPLAN_REACTOR:
            self._parameter_intent.set_xplan_reactor(parameter_value)
        elif parameter_field == intent_parser_constants.PROTOCOL_FIELD_PLATE_SIZE:
            plate_size = [int(value) for value in cell_parser.PARSER.process_numbers(parameter_value)]
            self._parameter_intent.set_plate_size(plate_size[0])
        elif parameter_field == intent_parser_constants.PARAMETER_PROTOCOL_NAME:
            if parameter_value == 'growth_curve':
                self._parameter_intent.set_protocol_name(intent_parser_constants.GROWTH_CURVE_PROTOCOL)
            else:
                self._parameter_intent.set_protocol_name(parameter_value)
        elif parameter_field == intent_parser_constants.PROTOCOL_FIELD_PLATE_NUMBER:
            plate_number = [int(value) for value in cell_parser.PARSER.process_numbers(parameter_value)]
            self._parameter_intent.set_plate_number(plate_number[0])
        elif parameter_field == intent_parser_constants.PROTOCOL_FIELD_CONTAINER_SEARCH_STRING:
            container_search_string = cell_parser.PARSER.extract_name_value(parameter_value)
            self._parameter_intent.set_container_search_strain(container_search_string)
        elif parameter_field == intent_parser_constants.PROTOCOL_FIELD_STRAIN_PROPERTY:
            self._parameter_intent.set_strain_property(parameter_value)
        elif parameter_field == intent_parser_constants.PROTOCOL_FIELD_XPLAN_PATH:
            self._parameter_intent.set_xplan_path(parameter_value)
        elif parameter_field == intent_parser_constants.PROTOCOL_FIELD_SUBMIT:
            boolean_value = cell_parser.PARSER.process_boolean_flag(parameter_value)
            self._parameter_intent.set_submit(boolean_value[0])
        elif parameter_field == intent_parser_constants.PROTOCOL_FIELD_PROTOCOL_ID:
            self._parameter_intent.set_protocol_id(parameter_value)
        elif parameter_field == intent_parser_constants.PROTOCOL_FIELD_TEST_MODE:
            boolean_value = cell_parser.PARSER.process_boolean_flag(parameter_value)
            self._parameter_intent.set_test_mode(boolean_value[0])
        elif parameter_field == intent_parser_constants.PROTOCOL_FIELD_EXPERIMENT_REFERENCE_URL_FOR_XPLAN:
            self._parameter_intent.set_experiment_reference_url_for_xplan(parameter_value)
        else:
            # must be protocol parameters
            self._parse_default_parameter(parameter_field, parameter_value)

    def _parse_default_parameter(self, parameter_field, parameter_value):
        if self.run_as_opil:
            parameter_id = parameter_field
            if parameter_field in self._parameter_fields:
                parameter_id = self._parameter_fields[parameter_id]

            if parameter_id == intent_parser_constants.PARAMETER_READER_INFO_LIST_OF_GAINS:
                json_parameter_value = json.loads(parameter_value)
                self._parameter_intent.add_parameter('plate_reader_info.list_of_gains.gain_1',
                                                     json_parameter_value['gain_1'])
                self._parameter_intent.add_parameter('plate_reader_info.list_of_gains.gain_2',
                                                     json_parameter_value['gain_2'])
                self._parameter_intent.add_parameter('plate_reader_info.list_of_gains.gain_3',
                                                     json_parameter_value['gain_3'])
            else:
                self._parameter_intent.add_parameter(parameter_id, parameter_value)
        else:
            parameter_id = parameter_field
            if parameter_field in self._parameter_fields:
                parameter_id = self._parameter_fields[parameter_id]
                self._parse_protocol_parameter(parameter_id, parameter_value)
            else:
                message = 'Parameter table has invalid Parameter Value: %s is not a supported parameter field.' % parameter_id
                self._validation_errors.append(message)

    def _parse_protocol_parameter(self, parameter_field, parameter_value):
        if parameter_field in self.FIELD_WITH_FLOAT_VALUE and parameter_value:
            self._process_numbered_parameter(parameter_field, parameter_value, float)
        elif parameter_field in self.FIELD_WITH_BOOLEAN_VALUE and parameter_value:
            self._process_boolean_parameter(parameter_field, parameter_value)
        elif parameter_field in self.FIELD_WITH_STRING_COMMAS:
            self._flatten_parameter_values(parameter_field, [parameter_value])
        elif parameter_field in self.FIELD_WITH_NESTED_STRUCTURE:
            try:
                if parameter_value:
                    json_parameter_value = json.loads(parameter_value)
                    computed_value = [json_parameter_value]
                    self._flatten_parameter_values(parameter_field, computed_value)
            except JSONDecodeError:
                errors = 'Parameter table has invalid Parameter Value: %s is an invalid json format.' % (parameter_value)
                self._validation_errors.append(errors)
        else:
            if parameter_value:
                computed_value = cell_parser.PARSER.transform_strateos_string(parameter_value)
                self._flatten_parameter_values(parameter_field, computed_value)

    def _process_boolean_parameter(self, parameter_field, parameter_value):
        try:
            boolean_value = cell_parser.PARSER.process_boolean_flag(parameter_value)
            if len(boolean_value) == 1:
                self._flatten_parameter_values(parameter_field, boolean_value)
            else:
                message = 'Found more than one boolean value in %s. Only the first boolean value encountered is used.' % (parameter_field)
                self._validation_warnings.append(message)
                self._flatten_parameter_values(parameter_field, [boolean_value[0]])

        except TableException as err:
            message = 'Parameter table has invalid %s value: %s' % (parameter_field, err)
            self._validation_errors.append(message)

    def _process_name_parameter(self, parameter_field, parameter_value):
        computed_value = [value for value, _ in cell_parser.PARSER.process_names_with_uri(parameter_value)]
        self._flatten_parameter_values(parameter_field, computed_value)

    def _process_numbered_parameter(self, parameter_field, parameter_value, number_convert):
        try:
            computed_value = [number_convert(value) for value in cell_parser.PARSER.process_numbers(parameter_value)]
            self._flatten_parameter_values(parameter_field, computed_value)
        except TableException as err:
            message = 'Parameter table has invalid %s value: %s' % (parameter_field, err)
            self._validation_errors.append(message)

