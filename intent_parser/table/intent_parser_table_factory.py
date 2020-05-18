from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.table.intent_parser_table import IntentParserTable
from intent_parser.constants import intent_parser_constants

_MEASUREMENT_TABLE_HEADER = {intent_parser_constants.COL_HEADER_REPLICATE,
                             intent_parser_constants.COL_HEADER_STRAIN,
                             intent_parser_constants.COL_HEADER_MEASUREMENT_TYPE,
                             intent_parser_constants.COL_HEADER_FILE_TYPE}

class IntentParserTableFactory(object):
        
    
    
    def __init__(self):
        self._google_table_parser = GoogleTableParser()
    
    def from_google_doc(self, table):
        intent_parser_table = self._google_table_parser.parse_table(table)
        pass
             
    def get_table_type(self, intent_parser_table):    
        header_row = self._get_header_row(intent_parser_table)
        
        header_values = {column.get_content() for column in header_row}
        
        if _MEASUREMENT_TABLE_HEADER.issubset(header_values):
            return None # enum
            
        
        
    
    def _get_header_row(self, intent_parser_table):
        pass
        
        
class TableParser(object):
    def parse_table(self, table):
        pass

class GoogleTableParser(TableParser):
    
    def __init__(self):
        pass
    
    # Override
    def parse_table(self, table):
        intent_parser_table = IntentParserTable()
        rows = table['tableRows']
        for row in rows:
            ip_row = [cell for cell in self._parse_row(row)]
            intent_parser_table.add_row(ip_row)
        return intent_parser_table

    def _parse_row(self, row):
        columns = row['tableCells']
        for cell in columns:
            ip_cell = IntentParserCell()
            for content, link in self._parse_cell(cell):
                ip_cell.add_paragraph(content, link)
            yield ip_cell 
    
    def _parse_cell(self, cell):
        content = cell['content']
        for paragraph in content['paragraph']:
            url = None
            if 'url' in paragraph['link']:
                url = paragraph['link']['url']
            list_of_contents = []
            for element in paragraph['elements']: 
                for text_run in element['textRun']:
                    result = text_run['content']
                    list_of_contents.append(result)
            flatten_content = ''.join(list_of_contents)
            yield flatten_content, url