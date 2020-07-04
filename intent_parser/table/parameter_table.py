from intent_parser.intent_parser_exceptions import TableException, DictionaryMaintainerException
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.table.cell_parser as cell_parser
import intent_parser.table.table_utils as table_utils
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
                                intent_parser_constants.PARAMETER_VALIDATE_SAMPLES]
    
    FIELD_WITH_FLOAT_VALUE = [intent_parser_constants.PARAMETER_PLATE_READER_INFO_GAIN]
    
    FIELD_WITH_NESTED_STRUCTURE = [intent_parser_constants.PARAMETER_INDUCTION_INFO_REAGENTS_INDUCER, 
                                   intent_parser_constants.PARAMETER_MEASUREMENT_INFO_FLOW_INFO,
                                   intent_parser_constants.PARAMETER_MEASUREMENT_INFO_PLATE_READER_INFO, 
                                   intent_parser_constants.PARAMETER_REAGENT_INFO_INDUCER_INFO, 
                                   intent_parser_constants.PARAMETER_REAGENT_INFO_KILL_SWITCH,
                                   intent_parser_constants.PARAMETER_RECOVERY_INFO]

    FIELD_WITH_STRING_COMMAS = [intent_parser_constants.PARAMETER_EXP_INFO_MEDIA_WELL_STRINGS]
    FIELD_WITH_SINGLE_STRING = [intent_parser_constants.PARAMETER_PROTOCOL,
                                intent_parser_constants.PARAMETER_STRAIN_PROPERTY,
                                intent_parser_constants.PARAMETER_XPLAN_PATH,
                                intent_parser_constants.PARAMETER_PROTOCOL_ID]

    EXPERIMENT_FIELDS_WITH_SINGLE_VALUE = [intent_parser_constants.PARAMETER_PLATE_SIZE,
                                           intent_parser_constants.PARAMETER_PLATE_NUMBER,
                                           intent_parser_constants.PARAMETER_PROTOCOL,
                                           intent_parser_constants.PARAMETER_STRAIN_PROPERTY,
                                           intent_parser_constants.PARAMETER_XPLAN_PATH,
                                           intent_parser_constants.PARAMETER_PROTOCOL_ID]

    FIELD_WITH_INT_VALUES = [intent_parser_constants.PARAMETER_PLATE_SIZE,
                             intent_parser_constants.PARAMETER_PLATE_NUMBER]

    EXPERIMENT_FIELDS_WITH_LIST = [intent_parser_constants.PARAMETER_CONTAINER_SEARCH_STRING]

    def __init__(self, intent_parser_table, parameter_fields={}):
        self.param_intent = _ParameterIntent()
        self._parameter_fields = parameter_fields
        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table 
        self._table_caption = ''

    def process_table(self):
        self._table_caption = self._intent_parser_table.caption()
        for row_index in range(self._intent_parser_table.data_row_index(), self._intent_parser_table.number_of_rows()):
            self._process_row(row_index)

    def get_experiment(self):
        return self.param_intent.to_experiment()

    def get_structured_request(self):
        return self.param_intent.to_structured_request()

    def set_experiment_ref(self, experiment_ref_url):
        self.param_intent.set_field(intent_parser_constants.PARAMETER_EXPERIMENT_REFERENCE_URL_FOR_XPLAN, experiment_ref_url)

    def _flatten_parameter_values(self, param_field, param_value_list):
        if len(param_value_list) == 0:
            return
        elif param_field in self.EXPERIMENT_FIELDS_WITH_SINGLE_VALUE:
            self.param_intent.set_field(param_field, param_value_list[0])
            return
        elif param_field in self.EXPERIMENT_FIELDS_WITH_LIST:
            self.param_intent.set_field(param_field, param_value_list)
            return
        elif len(param_value_list) == 1:
            self.param_intent.add_default_parameter(param_field, param_value_list[0])
            return
        for i in range(len(param_value_list)):
            param_field_id = param_field + '.' + str(i)
            self.param_intent.add_default_parameter(param_field_id, param_value_list[i])

    def _process_row(self, row_index):
        row = self._intent_parser_table.get_row(row_index)
        cell_param_field = None
        cell_param_value = None
        for cell_index in range(len(row)):
            cell = self._intent_parser_table.get_cell(row_index, cell_index)
            # Cell type based on column header
            header_row_index = self._intent_parser_table.header_row_index()
            header_cell = self._intent_parser_table.get_cell(header_row_index, cell_index)
            cell_type = cell_parser.PARSER.get_header_type(header_cell)
            if intent_parser_constants.HEADER_PARAMETER_TYPE == cell_type:
                cell_param_field = cell
            elif intent_parser_constants.HEADER_PARAMETER_VALUE_TYPE == cell_type:
                cell_param_value = cell
        if cell_param_field is None and cell_param_value:
            self._validation_errors.append('Parameter table cannot assign %s as a parameter value to an empty parameter.' % cell_param_value.get_text())
            return
        if cell_param_field and cell_param_value is None:
            return
        self._parse_parameter_field_value(self._get_parameter_field(cell_param_field), cell_param_value)
                  
    def _parse_parameter_field_value(self, parameter_field, parameter_value):
        computed_value = None
        if parameter_field in self.FIELD_WITH_FLOAT_VALUE:
            self.process_numbered_parameter(parameter_field, parameter_value, float)
        elif parameter_field in self.FIELD_WITH_BOOLEAN_VALUE:
            self.process_boolean_parameter(parameter_field, parameter_value)
        elif parameter_field in self.FIELD_WITH_STRING_COMMAS:
            self._flatten_parameter_values(parameter_field, [parameter_value.get_text()])
        elif parameter_field in self.FIELD_WITH_SINGLE_STRING:
            self.process_name_parameter(parameter_field, parameter_value)
        elif parameter_field in self.FIELD_WITH_INT_VALUES:
            self.process_numbered_parameter(parameter_field, parameter_value, int)
        elif parameter_field in self.FIELD_WITH_NESTED_STRUCTURE:
            json_parameter_value = json.loads(parameter_value.get_text())
            computed_value = [json_parameter_value]
            self._flatten_parameter_values(parameter_field, computed_value)
        else:
            computed_value = table_utils.transform_strateos_string(parameter_value.get_text())
            self._flatten_parameter_values(parameter_field, computed_value)
    
    def _get_parameter_field(self, cell):
        parameters = cell_parser.PARSER.process_names(cell)
        if not parameters:
            message = 'Parameter table has invalid %s value: field cannot be empty.' % (intent_parser_constants.HEADER_PARAMETER_VALUE_TYPE)
            self._validation_errors.append(message)
            return None
        if len(parameters) != 1:
            message = ('Parameter table for %s has more than one %s provided. '
                       'Only the first %s will be used from %s.') % (
                      intent_parser_constants.HEADER_PARAMETER_VALUE_TYPE,
                      intent_parser_constants.HEADER_PARAMETER_VALUE_TYPE,
                      cell.get_text())
            self._validation_warnings.append(message)
        parameter = parameters[0]
        if parameter in self._parameter_fields:
            return self._parameter_fields[parameter]
        return parameter

    def get_validation_errors(self):
        return self._validation_errors

    def process_boolean_parameter(self, parameter_field, parameter_value):
        boolean_value = cell_parser.PARSER.process_boolean_flag(parameter_value)
        if boolean_value is None:
            message = 'Parameter table has invalid %s value: %s should be a boolean value' % (parameter_field, parameter_value.get_text())
            self._validation_errors.append(message)
        else:
            computed_value = [boolean_value]
            self._flatten_parameter_values(parameter_field, computed_value)

    def process_name_parameter(self, parameter_field, parameter_value):
        if cell_parser.PARSER.is_name(parameter_value):
            computed_value = cell_parser.PARSER.process_names(parameter_value)
            self._flatten_parameter_values(parameter_field, computed_value)
        else:
            message = 'Parameter table has invalid %s value: %s should only contain a list names' % (parameter_field, parameter_value.get_text())
            self._validation_errors.append(message)

    def process_numbered_parameter(self, parameter_field, parameter_value, number_convert):
        if cell_parser.PARSER.is_number(parameter_value):
            computed_value = [number_convert(value) for value in cell_parser.PARSER.process_numbers(parameter_value)]
            self._flatten_parameter_values(parameter_field, computed_value)
        else:
            message = 'Parameter table has invalid %s value: %s should only contain numbers' % (parameter_field, parameter_value.get_text())
            self._validation_errors.append(message)

class _ParameterIntent(object):

    def __init__(self):
        self.intent = {
            intent_parser_constants.PARAMETER_XPLAN_REACTOR: 'xplan',
            intent_parser_constants.PARAMETER_PLATE_SIZE: None,
            intent_parser_constants.PARAMETER_PROTOCOL: None,
            intent_parser_constants.PARAMETER_PLATE_NUMBER: None,
            intent_parser_constants.PARAMETER_CONTAINER_SEARCH_STRING: None,
            intent_parser_constants.PARAMETER_STRAIN_PROPERTY: None,
            intent_parser_constants.PARAMETER_XPLAN_PATH: None,
            intent_parser_constants.PARAMETER_SUBMIT: False,
            intent_parser_constants.PARAMETER_PROTOCOL_ID: None,
            intent_parser_constants.PARAMETER_TEST_MODE: True,
            intent_parser_constants.PARAMETER_EXPERIMENT_REFERENCE_URL_FOR_XPLAN: None,
            intent_parser_constants.DEFAULT_PARAMETERS: {}
        }

    def set_field(self, field, value):
        if field not in self.intent:
            raise TableException('Parameter Table cannot identify row of type %s.' % field)

        if self.intent[field] is not None:
            raise TableException('Parameter Table has a conflict for %s. Found %s and %s.' % (field, self.intent[field], value))

        self.intent[field] = value

    def add_default_parameter(self, field, value):
        if field in self.intent[intent_parser_constants.DEFAULT_PARAMETERS]:
            raise TableException('Parameter Table has a conflict for %s. Found %s and %s.'
                                 % (field, self.intent[intent_parser_constants.DEFAULT_PARAMETERS][field], value))

        self.intent[intent_parser_constants.DEFAULT_PARAMETERS][field] = value

    def to_experiment(self):
        for key, value in self.intent.items():
            if value is None:
                raise TableException('Parameter Table is missing a %s row.' % key)

        return self.intent

    def to_structured_request(self):
        return self.intent[intent_parser_constants.DEFAULT_PARAMETERS]

