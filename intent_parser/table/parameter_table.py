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
    
    FIELD_WITH_LIST_OF_STRING = [intent_parser_constants.PARAMETER_EXP_INFO_MEDIA_WELL_STRINGS]
     
    def __init__(self, intent_parser_table, parameter_fields={}):
        self._parameter_fields = parameter_fields
        self._validation_errors = []
        self._intent_parser_table = intent_parser_table 
        self._table_caption = ''
    
    def process_table(self):
        parameter_data = {}
        self._table_caption = self._intent_parser_table.caption()
        for row_index in range(self._intent_parser_table.data_row_index(), self._intent_parser_table.number_of_rows()):
            try:
                param_field,param_value_list = self._process_row(row_index)
                if len(param_value_list) == 0:
                    continue
                elif len(param_value_list) == 1:
                    parameter_data[param_field] = param_value_list[0]
                else:
                    for i in range(len(param_value_list)):
                        param_field_id = param_field + '.' + str(i)
                        parameter_data[param_field_id] = param_value_list[i]
            except ValueError as value_err:
                message = str(value_err)
                self._validation_errors.append(message)       
            except TableException as table_err:
                message = table_err.get_message()
                self._validation_errors.append(message)
            except DictionaryMaintainerException as dictionary_err:
                self._validation_errors.append(dictionary_err.get_message())
        return parameter_data
    
    def _process_row(self, row_index):
        row = self._intent_parser_table.get_row(row_index)
        param_field = ''
        param_value = '' 
        for cell_index in range(len(row)):
            cell = self._intent_parser_table.get_cell(row_index, cell_index)
            # Cell type based on column header
            header_row_index = self._intent_parser_table.header_row_index()
            header_cell = self._intent_parser_table.get_cell(header_row_index, cell_index)
            cell_type = cell_parser.PARSER.get_header_type(header_cell)
            if intent_parser_constants.HEADER_PARAMETER_TYPE == cell_type:
                param_field = self._get_parameter_field(cell.get_text().strip())
            elif intent_parser_constants.HEADER_PARAMETER_VALUE_TYPE == cell_type:
                param_value = cell.get_text()
        if not param_field:
            raise TableException('Parameter field should not be empty')
        if not param_value:
            return param_field, []
        return self._parse_parameter_field_value(param_field, param_value)  
                  
    def _parse_parameter_field_value(self, parameter_field, parameter_value):
        if parameter_field in self.FIELD_WITH_FLOAT_VALUE: 
            values = table_utils.extract_number_value(parameter_value)
            return parameter_field, [float(float_val) for float_val in values]
        elif parameter_field in self.FIELD_WITH_BOOLEAN_VALUE:
            parameter_value = parameter_value.lower()
            if parameter_value == 'false':
                return parameter_field, [False]
            elif parameter_value == 'true':
                return parameter_field, [True]
            else:
                raise TableException('Parameter table has invalid %s value: %s should be a boolean value' % (parameter_field, parameter_value))
        elif parameter_field in self.FIELD_WITH_LIST_OF_STRING:
            return parameter_field, [parameter_value] 
        elif parameter_field in self.FIELD_WITH_NESTED_STRUCTURE:
            json_parameter_value = json.loads(parameter_value)
            return parameter_field, [json_parameter_value] 
        
        return parameter_field, table_utils.transform_strateos_string(parameter_value)
    
    def _get_parameter_field(self, cell_txt):
        if not self._parameter_fields:
            raise DictionaryMaintainerException('There are no parameters that could map to a Strateos protocol')
        if cell_txt not in self._parameter_fields:
            raise TableException('%s does not map to a Strateos UID' % cell_txt)
        return self._parameter_fields[cell_txt]

    def get_validation_errors(self):
        return self._validation_errors
