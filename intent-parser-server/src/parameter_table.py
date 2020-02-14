from intent_parser_exceptions import TableException, DictionaryMaintainerException
import constants
import logging
import table_utils

class ParameterTable(object):
    '''
    Class handles parameter tables 
    '''
    
    _logger = logging.getLogger('intent_parser_server')
    
    FIELD_WITH_BOOLEAN_VALUE = [constants.PARAMETER_VALIDATE_SAMPLES, 
                                constants.PARAMETER_RUN_INFO_READ_EACH_RECOVER,
                                constants.PARAMETER_RUN_INFO_READ_EACH_INDUCTION,
                                constants.PARAMETER_RUN_INFO_SAVE_FOR_RNASEQ, 
                                constants.PARAMETER_RUN_INFO_SKIP_FIRST_FLOW, 
                                constants.PARAMETER_RUN_INFO_ONLY_ENDPOINT_FLOW]
    FIELD_WITH_FLOAT_VALUE = [constants.PARAMETER_PLATE_READER_INFO_GAIN]
    
    def __init__(self, parameter_fields={}):
        self._parameter_fields = parameter_fields
        self._validation_errors = []
    
    def parse_table(self, table):
        parameter_data = {}
        rows = table['tableRows']
        for row in rows[1:]:
            param_field, param_value = self._parse_row(rows[0], row)
            if not param_field or len(param_value) == 0:
                continue
            try:
                if len(param_value) == 1:
                    key, value = self._parse_parameter_field_value(param_field, param_field, param_value[0])
                    parameter_data[key] = value
                else:
                    for index in range(len(param_value)):
                        param_field_id = '.'.join([param_field, str(index)])
                        key, value = self._parse_parameter_field_value(param_field, param_field_id, param_value[index])
                        parameter_data[key] = value
            except ValueError as value_err:
                message = str(value_err)
                self._logger.info('WARNING ' + message)
                self._validation_errors.append(message)       
            except TableException as table_err:
                message = ' '.join([table_err.get_expression(), table_err.get_message()]) 
                self._logger.info('WARNING ' + message)
                self._validation_errors.append(message) 
        return parameter_data
    
    def _parse_parameter_field_value(self, parameter_field, parameter_field_id, parameter_value):
        if parameter_field in self.FIELD_WITH_FLOAT_VALUE: 
            return parameter_field_id, float(parameter_value)
        elif parameter_field in self.FIELD_WITH_BOOLEAN_VALUE:
            parameter_value = parameter_value.lower()
            if parameter_value == 'false':
                return parameter_field_id, False
            elif parameter_value == 'true':
                return parameter_field_id, True
            else:
                raise TableException(parameter_value, 'is not a boolean value')
        
        return parameter_field_id, parameter_value
        
    def _parse_row(self, header_row, row):
        num_cols = len(row['tableCells'])
        try:
            param_field = ''
            param_value = []
            for col_index in range(0, num_cols): 
                paragraph_element = header_row['tableCells'][col_index]['content'][0]['paragraph']
                header = table_utils.get_paragraph_text(paragraph_element).strip()
                cell_txt = ' '.join([table_utils.get_paragraph_text(content['paragraph']).strip() for content in row['tableCells'][col_index]['content']])
                if not cell_txt:
                    continue
                elif header == constants.COL_HEADER_PARAMETER:
                    param_field = self._get_parameter_field(cell_txt)
                elif header == constants.COL_HEADER_PARAMETER_VALUE:
                    param_value = table_utils.transform_number_name_cell(cell_txt)
            
            if not param_field:
                raise TableException('Parameter field', 'is empty') 
            return param_field, param_value 
        except TableException as err:
            message = ' '.join(['In Parameter Table: ', err.get_expression(), err.get_message()]) 
            self._logger.info('WARNING ' + message)
            self._validation_errors.append(message)
            
    def _get_parameter_field(self, cell_txt):
        if not self._parameter_fields:
            raise DictionaryMaintainerException('Strateos mapping', 'is empty')
        if not cell_txt in self._parameter_fields:
            raise TableException(cell_txt, 'does not map to a Strateos UID')
        return self._parameter_fields[cell_txt]
    
    def get_validation_errors(self):
        return self._validation_errors      
        