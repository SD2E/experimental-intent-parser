from intent_parser_exceptions import TableException, DictionaryMaintainerException
import constants
import json
import logging
import table_utils

class ParameterTable(object):
    '''
    Class handles parameter tables 
    '''
    
    _logger = logging.getLogger('intent_parser_server')
    
    FIELD_WITH_BOOLEAN_VALUE = [constants.PARAMETER_MEASUREMENT_INFO_36_HR_READ, 
                                constants.PARAMETER_RUN_INFO_READ_EACH_RECOVER,
                                constants.PARAMETER_RUN_INFO_READ_EACH_INDUCTION,
                                constants.PARAMETER_RUN_INFO_SAVE_FOR_RNASEQ, 
                                constants.PARAMETER_RUN_INFO_SKIP_FIRST_FLOW, 
                                constants.PARAMETER_RUN_INFO_ONLY_ENDPOINT_FLOW, 
                                constants.PARAMETER_VALIDATE_SAMPLES]
    
    FIELD_WITH_FLOAT_VALUE = [constants.PARAMETER_PLATE_READER_INFO_GAIN]
    
    FIELD_WITH_NESTED_STRUCTURE = [constants.PARAMETER_INDUCTION_INFO_REAGENTS_INDUCER, 
                                   constants.PARAMETER_MEASUREMENT_INFO_FLOW_INFO,
                                   constants.PARAMETER_MEASUREMENT_INFO_PLATE_READER_INFO, 
                                   constants.PARAMETER_REAGENT_INFO_INDUCER_INFO, 
                                   constants.PARAMETER_REAGENT_INFO_KILL_SWITCH,
                                   constants.PARAMETER_RECOVERY_INFO]
    
    FIELD_WITH_LIST_OF_STRING = [constants.PARAMETER_EXP_INFO_MEDIA_WELL_STRINGS]
     
    def __init__(self, parameter_fields={}):
        self._parameter_fields = parameter_fields
        self._validation_errors = []
    
    def parse_table(self, table):
        parameter_data = {}
        rows = table['tableRows']
        for row in rows[1:]:
            try:
                param_field, param_value_list = self._parse_row(rows[0], row)
                if len(param_value_list) == 0:
                    continue
                elif len(param_value_list) == 1:
                    parameter_data[param_field] = param_value_list[0]
                else:
                    for i in range(len(param_value_list)):
                        param_field_id = param_field + '.' + str(i)
                        parameter_data[param_field_id] =  param_value_list[i]
            except ValueError as value_err:
                message = str(value_err)
                self._logger.info('WARNING ' + message)
                self._validation_errors.append(message)       
            except TableException as table_err:
                message = ' '.join(['In Parameter Table: ', table_err.get_expression(), table_err.get_message()])
                self._logger.info('WARNING ' + message)
                self._validation_errors.append(message) 
        return parameter_data
    
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
                raise TableException(parameter_value, 'should be a boolean value')
        elif parameter_field in self.FIELD_WITH_LIST_OF_STRING:
            # Return the original form for parameters that contain a list of string 
            return parameter_field, [parameter_value] 
        elif parameter_field in self.FIELD_WITH_NESTED_STRUCTURE:
            json_parameter_value = json.loads(parameter_value)
            return parameter_field, [json_parameter_value] 
        
        return parameter_field, table_utils.transform_strateos_string(parameter_value)
    
    def _parse_row(self, header_row, row):
        num_cols = len(row['tableCells'])
        param_field = ''
        param_value = '' 
        for col_index in range(0, num_cols): 
            paragraph_element = header_row['tableCells'][col_index]['content'][0]['paragraph']
            header = table_utils.get_paragraph_text(paragraph_element).strip()
            cell_txt = ' '.join([table_utils.get_paragraph_text(content['paragraph']).strip() for content in row['tableCells'][col_index]['content']])
            
            if header == constants.COL_HEADER_PARAMETER:
                param_field = self._get_parameter_field(cell_txt)
            elif header == constants.COL_HEADER_PARAMETER_VALUE:
                param_value = cell_txt
            else:
                raise TableException(cell_txt, 'was not recognized as a cell value under ' + constants.COL_HEADER_PARAMETER + ' or ' + constants.COL_HEADER_PARAMETER_VALUE)
        
        if not param_field:
            raise TableException('Parameter field', 'should not be empty') 
        
        if not param_value:
            return param_field, []
        
        return self._parse_parameter_field_value(param_field, param_value)        
            
    def _get_parameter_field(self, cell_txt):
        if not self._parameter_fields:
            raise DictionaryMaintainerException('Strateos mapping', 'is empty')
        if not cell_txt in self._parameter_fields:
            raise TableException(cell_txt, 'does not map to a Strateos UID')
        return self._parameter_fields[cell_txt]
    
    def get_validation_errors(self):
        return self._validation_errors      
        