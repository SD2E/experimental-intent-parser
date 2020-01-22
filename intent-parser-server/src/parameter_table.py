import constants
import table_utils

class ParameterTable(object):
    '''
    Class handles parameter tables 
    '''
    FIELD_WITH_BOOLEAN_VALUE = [constants.PARAMETER_VALIDATE_SAMPLES]
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
        
        content = []
        num_cols = len(row['tableCells'])
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
    
    def _get_parameter_field(self, cell_txt):
        return self._parameter_fields[cell_txt]
            
        