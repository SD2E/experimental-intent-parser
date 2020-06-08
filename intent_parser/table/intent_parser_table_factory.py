from enum import Enum 
from intent_parser.constants import intent_parser_constants
from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.table.intent_parser_table import IntentParserTable
import intent_parser.table.cell_parser as cell_parser

_MEASUREMENT_TABLE_HEADER = {intent_parser_constants.COL_HEADER_REPLICATE,
                             intent_parser_constants.COL_HEADER_STRAIN,
                             intent_parser_constants.COL_HEADER_MEASUREMENT_TYPE,
                             intent_parser_constants.COL_HEADER_FILE_TYPE}

_PARAMETER_TABLE_HEADER = {intent_parser_constants.COL_HEADER_PARAMETER,
                           intent_parser_constants.COL_HEADER_PARAMETER_VALUE}

_CONTROLS_TABLE_HEADER = {intent_parser_constants.COL_HEADER_CONTROL_CHANNEL,
                          intent_parser_constants.COL_HEADER_CONTROL_TYPE,
                          intent_parser_constants.COL_HEADER_CONTROL_STRAINS,
                          intent_parser_constants.COL_HEADER_CONTROL_CONTENT,
                          intent_parser_constants.COL_HEADER_CONTROL_TIMEPOINT}

class TableType(Enum):
    CONTROL = 1 
    LAB = 2
    MEASUREMENT = 3
    PARAMETER = 4
    UNKNOWN = 5
    
class IntentParserTableFactory(object):
        
    def __init__(self):
        self._google_table_parser = GoogleTableParser()
        
    def from_google_doc(self, table):
        return self._google_table_parser.parse_table(table)
    
    def get_caption_row_index(self, intent_parser_table):
        for row_index in range(intent_parser_table.number_of_rows()):
            cell = intent_parser_table.get_cell(row_index, 0)
            if cell_parser.PARSER.is_table_caption(cell):
                return row_index
        return None 
        
    def get_header_row_index(self, intent_parser_table):
        for row_index in range(intent_parser_table.number_of_rows()):
            row = intent_parser_table.get_row(row_index)
            header_values = {column.get_text() for column in row}
            if _CONTROLS_TABLE_HEADER.issubset(header_values) \
                or _MEASUREMENT_TABLE_HEADER.issubset(header_values) \
                or _PARAMETER_TABLE_HEADER.issubset(header_values):
                return row_index
        return None  
    
    def get_table_type(self, intent_parser_table):    
        header_row_index = self.get_header_row_index(intent_parser_table)
        if header_row_index:
            header_row = intent_parser_table.get_row(header_row_index)
            header_values = {column.get_text() for column in header_row}
            if _CONTROLS_TABLE_HEADER.issubset(header_values):
                return TableType.CONTROL
            elif _MEASUREMENT_TABLE_HEADER.issubset(header_values):
                return TableType.MEASUREMENT 
            elif _PARAMETER_TABLE_HEADER.issubset(header_values):
                return TableType.PARAMETER
        
        if self._lab_table(intent_parser_table):
            return TableType.LAB
        return TableType.UNKNOWN
    
    def _lab_table(self, intent_parser_table):
        num_rows = intent_parser_table.number_of_rows()
        if num_rows < 0 or num_rows > 2:
            return False 
        for row_index in range(num_rows):
            row = intent_parser_table.get_row(row_index)
            if len(row) != 1:
                return False 
            for column in row:
                text = column.get_text().lower()
                if text.startswith('lab'):
                    return True 
        return False 

        
        
class TableParser(object):
    def parse_table(self, table):
        pass

class GoogleTableParser(TableParser):
    
    def __init__(self):
        pass
    
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
            for content, link, bookmark_id in self._parse_cell(cell):
                ip_cell.add_paragraph(content, link, bookmark_id)
            yield ip_cell 
    
    def _parse_cell(self, cell):
        contents = cell['content']
        for content in contents:
            paragraph = content['paragraph'] 
            for element in paragraph['elements']:
                url = None
                bookmark_id = None 
                text_run = element['textRun']
                if 'textStyle' in text_run and 'link' in text_run['textStyle']:
                    link = text_run['textStyle']['link']
                    if 'url' in link:
                        url = link['url']
                    if 'bookmarkId' in link:
                        bookmark_id = link['bookmarkId']
                result = text_run['content'].strip()
                yield result, url, bookmark_id 