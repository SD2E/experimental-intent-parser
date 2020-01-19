import table_utils

class ParameterTable(object):
    '''
    Class handles parameter tables 
    '''

    def __init__(self, params):
        '''
        Constructor
        '''
    
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
        for i in range(0, num_cols): 
            paragraph_element = header_row['tableCells'][i]['content'][0]['paragraph']
            header = table_utils.get_paragraph_text(paragraph_element).strip()
            cellTxt = ' '.join([table_utils.get_paragraph_text(content['paragraph']).strip() for content in row['tableCells'][i]['content']])
            if not cellTxt:
                continue
            
        return parameter_data 