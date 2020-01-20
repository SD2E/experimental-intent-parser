import constants
import table_utils

class ParameterTable(object):
    '''
    Class handles parameter tables 
    '''

    def __init__(self, parameter_fields={}):
        self._parameter_fields = parameter_fields
    
    def parse_table(self, table):
        parameter = []
        rows = table['tableRows']
        for row in rows[1:]:
            parameter.append(self._parse_row(rows[0], row))
        return parameter
    
    def _parse_row(self, header_row, row):
        parameter_data = {}
        content = []
        num_cols = len(row['tableCells'])
        param_field = ''
        param_value = 'unspecified'
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
                
        if param_field:
            # TODO: Support nested result from parameter_value.  
            parameter_data[param_field] = param_value[0]
            
        return parameter_data 
    
    def _get_parameter_field(self, cell_txt):
        return self._parameter_fields[cell_txt]
            
        