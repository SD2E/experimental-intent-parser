from enum import Enum 
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.constants.google_doc_api_constants as doc_constants
from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.table.intent_parser_table import IntentParserTable
import intent_parser.table.cell_parser as cell_parser

_MEASUREMENT_TABLE_HEADER = {intent_parser_constants.HEADER_REPLICATE_TYPE,
                             intent_parser_constants.HEADER_STRAINS_TYPE,
                             intent_parser_constants.HEADER_MEASUREMENT_TYPE_TYPE,
                             intent_parser_constants.HEADER_FILE_TYPE_TYPE}

_PARAMETER_TABLE_HEADER = {intent_parser_constants.HEADER_PARAMETER_TYPE,
                           intent_parser_constants.HEADER_PARAMETER_VALUE_TYPE}

_CONTROLS_TABLE_HEADER = {intent_parser_constants.HEADER_CHANNEL_TYPE,
                          intent_parser_constants.HEADER_CONTROL_TYPE_TYPE,
                          intent_parser_constants.HEADER_STRAINS_TYPE,
                          intent_parser_constants.HEADER_CONTENTS_TYPE,
                          intent_parser_constants.HEADER_TIMEPOINT_TYPE}

_EXPERIMENT_STATUS_TABLE = {intent_parser_constants.HEADER_LAST_UPDATED_TYPE,
                            intent_parser_constants.HEADER_PATH_TYPE,
                            intent_parser_constants.HEADER_PIPELINE_STATUS_TYPE,
                            intent_parser_constants.HEADER_STATE_TYPE}

_EXPERIMENT_SPECIFICATION_TABLE = {intent_parser_constants.HEADER_EXPERIMENT_ID_VALUE,
                                   intent_parser_constants.HEADER_EXPERIMENT_STATUS_VALUE}

class TableType(Enum):
    UNKNOWN = 1
    LAB = 2
    MEASUREMENT = 3
    PARAMETER = 4
    CONTROL = 5
    EXPERIMENT_STATUS = 6
    EXPERIMENT_SPECIFICATION = 7

class IntentParserTableFactory(object):
        
    def __init__(self):
        self._google_table_parser = GoogleTableParser()
        
    def from_google_doc(self, table):
        return self._google_table_parser.parse_table(table)
    
    def get_caption_row_index(self, intent_parser_table):
        for row_index in range(intent_parser_table.number_of_rows()):
            cell = intent_parser_table.get_cell(row_index, 0)
            if cell_parser.PARSER.is_table_caption(cell.get_text()):
                return row_index
        return None 
        
    def get_header_row_index(self, intent_parser_table):
        for row_index in range(intent_parser_table.number_of_rows()):
            row = intent_parser_table.get_row(row_index)
            header_values = {cell_parser.PARSER.get_header_type(column) for column in row}
            
            if _CONTROLS_TABLE_HEADER.issubset(header_values) \
                or _MEASUREMENT_TABLE_HEADER.issubset(header_values) \
                or _PARAMETER_TABLE_HEADER.issubset(header_values):
                return row_index
        return None  
    
    def get_table_type(self, intent_parser_table):    
        header_row_index = self.get_header_row_index(intent_parser_table)
        if header_row_index is not None:
            row = intent_parser_table.get_row(header_row_index)
            header_values = {cell_parser.PARSER.get_header_type(column) for column in row}
            
            if _CONTROLS_TABLE_HEADER.issubset(header_values):
                return TableType.CONTROL
            elif _MEASUREMENT_TABLE_HEADER.issubset(header_values):
                return TableType.MEASUREMENT 
            elif _PARAMETER_TABLE_HEADER == header_values:
                return TableType.PARAMETER
            elif _EXPERIMENT_STATUS_TABLE == header_values:
                return TableType.EXPERIMENT_STATUS
            elif _EXPERIMENT_SPECIFICATION_TABLE== header_values:
                return TableType.EXPERIMENT_SPECIFICATION

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
        rows = table[doc_constants.TABLE_ROWS]
        for row in rows:
            ip_row = [cell for cell in self._parse_row(row)]
            intent_parser_table.add_row(ip_row)
        return intent_parser_table

    def _parse_row(self, row):
        columns = row[doc_constants.TABLE_CELLS]
        for cell in columns:
            ip_cell = IntentParserCell()
            start_index = cell[doc_constants.START_INDEX]
            end_index = cell[doc_constants.END_INDEX]
            ip_cell.set_start_index(start_index)
            ip_cell.set_end_index(end_index)
            for content, link, bookmark_id in self._parse_cell(cell):
                ip_cell.add_paragraph(content, link, bookmark_id)
            yield ip_cell
    
    def _parse_cell(self, cell):
        contents = cell[doc_constants.CONTENT]
        for content in contents:
            paragraph = content[doc_constants.PARAGRAPH]
            for element in paragraph[doc_constants.ELEMENTS]:
                url = None
                bookmark_id = None 
                text_run = element[doc_constants.TEXT_RUN]
                if doc_constants.TEXT_STYLE in text_run and doc_constants.LINK in text_run[doc_constants.TEXT_STYLE]:
                    link = text_run[doc_constants.TEXT_STYLE][doc_constants.LINK]
                    if doc_constants.URL in link:
                        url = link[doc_constants.URL]
                    if doc_constants.BOOKMARK_ID in link:
                        bookmark_id = link[doc_constants.BOOKMARK_ID]
                result = text_run[doc_constants.CONTENT].strip()
                yield result, url, bookmark_id