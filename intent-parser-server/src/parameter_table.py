from intent_parser_exceptions import TableException
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
    
    def parse_table(self, table):
        parameter_data = {}
        rows = table['tableRows']
        for row in rows[1:]:
            param_field, param_value = self._parse_row(rows[0], row)
            # TODO: Support nested result from parameter_value.  
            if not param_field:
                continue
            
            if param_field in self.FIELD_WITH_FLOAT_VALUE:  
                parameter_data[param_field] = float(param_value[0])
            elif param_field in self.FIELD_WITH_BOOLEAN_VALUE:
                if param_value[0] == 'false':
                    parameter_data[param_field] = False
                elif param_value[0] == 'true':
                    parameter_data[param_field] = True 
            else:
                parameter_data[param_field] = param_value[0]
                    
        return parameter_data
    
    def _parse_row(self, header_row, row):
        num_cols = len(row['tableCells'])
        try:
            param_field = ''
            param_value = ['unspecified']
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
                
            return param_field, param_value 
        except TableException as err:
            self._logger.info('WARNING in Parameter Table: ' + err.get_message() + ' for ' + err.get_expression())
            
    def _get_parameter_field(self, cell_txt):
        if not cell_txt in self._parameter_fields:
            raise TableException(cell_txt, 'Strateos does not support parameter field')
        return self._parameter_fields[cell_txt]
            
        