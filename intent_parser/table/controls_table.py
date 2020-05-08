from intent_parser.intent_parser_exceptions import TableException
from intent_parser.table.intent_parser_cell import IntentParserCell 
from intent_parser.table.intent_parser_table import IntentParserTable
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.table.table_utils as table_utils
import intent_parser.utils.intent_parser_utils as intent_parser_utils
import logging

class ControlsTable(object):
    """
    Process information from Intent Parser's Controls Table
    """
    _logger = logging.getLogger('intent_parser')
    
    TABLE_HEADER_ROW_INDEX = 0

    def __init__(self, table, control_types={}, timepoint_units={}):
        self._control_types = control_types
        self._timepoint_units = timepoint_units
        self._validation_errors = []
        self._validation_warnings = []
        self._table = IntentParserTable(table)
       
    def process_table(self):
        controls = []
        for row_index in enumerate(self._table.number_of_rows(), start=1):
            row = self._table.get_row_by_index(row_index)
            control_data = self._process_row(row)
            self.controls.append(control_data)
        return controls
                    
    def _process_row(self, row):
        control_data = {}
        control_type_index = self._get_header_index(intent_parser_constants.COL_HEADER_CONTROL_TYPE) 
        control_strains_index = self._get_header_index(intent_parser_constants.COL_HEADER_CONTROL_STRAINS) 
        channel_index = self._get_header_index(intent_parser_constants.COL_HEADER_CHANNEL) 
        
        num_of_cells = self._table.number_of_cells(row)
        for cell_index in enumerate(num_of_cells):
            cell = self._table.get_cell_from_row(row, cell_index)
            cell_parser = IntentParserCell(cell)
            cell_txt = cell_parser.get_contents()
            if cell_index == control_type_index:
                control_data['type'] = self._process_control_type(cell_txt)
            elif cell_index == control_strains_index:
                control_data['strains'] = self._process_control_strains(cell_txt)
            elif cell_index == channel_index:
                control_data['channels'] = self._process_channels(cell_txt)
        return control_data
    
    def _process_channels(self, cell_txt):
        try:
            if table_utils.is_valued_cells(cell_txt):
                raise TableException('Identified %s as a numerical value when expecting alpha-numeric values.')
        except TableException as err:
            message = 'Controls table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_CHANNEL, err.get_message())  
            self._validation_errors.append(message)
        
        list_of_channels = [value for value in table_utils.extract_name_value(cell_txt)]
        if len(list_of_channels) > 1:
            message = 'Controls table for %s has more than one channel provided. Only the first channel will be used from %s.' % (intent_parser_constants.COL_HEADER_CHANNEL, cell_txt)
            self._validation_warnings.append(message)
            
        return list_of_channels[0]
        
    def _process_control_strains(self, cell_txt):
        try:
            if table_utils.is_valued_cells(cell_txt):
                raise TableException('Identified %s as a numerical value when expecting alpha-numeric values.')
        except TableException as err:
            message = 'Controls table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_CONTROL_STRAINS, err.get_message())  
            self._validation_errors.append(message)
        return [value for value in table_utils.extract_name_value(cell_txt)]
                
    def _process_control_type(self, cell_txt):
        try: 
            if cell_txt not in self._control_types:
                raise TableException('%s does not match one of the following control types: \n %s' % (cell_txt, ' ,'.join((map(str, self._control_types)))))
        except TableException as err:
            message = 'Controls table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_CONTROL_TYPE, err.get_message())
            self._validation_errors.append(message)
        return cell_txt
    
    def parse_table(self, table):
        controls = []
        rows = table['tableRows']
        for row in rows[1:]:
            controls_data = self._parse_row(rows[0], row)
            if controls_data:
                controls.append(controls_data)
        return controls  
    
    def _parse_row(self, header_row, row):
        control_data = {}
        num_cols = len(row['tableCells'])
        for i in range(0, num_cols): 
            paragraph_element = header_row['tableCells'][i]['content'][0]['paragraph']
            header = intent_parser_utils.get_paragraph_text(paragraph_element).strip()
            cell_txt = ' '.join([intent_parser_utils.get_paragraph_text(content['paragraph']).strip() for content in row['tableCells'][i]['content']])
            if not cell_txt:
                continue
            elif header == intent_parser_constants.COL_HEADER_CONTROL_TYPE:
                try:  
                    control_data['type'] = self._get_control_type(cell_txt.strip())
                except TableException as err:
                    message = 'Controls table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_CONTROL_TYPE, err.get_message())
                    self._validation_errors.append(message)
            elif header == intent_parser_constants.COL_HEADER_CONTROL_STRAINS:
                try:
                    if table_utils.is_valued_cells(cell_txt):
                        raise TableException('Identified %s as a numerical value when expecting alpha-numeric values.')
                    control_data['strains'] = [value for value in table_utils.extract_name_value(cell_txt)]
                except TableException as err:
                    message = 'Controls table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_CONTROL_STRAINS, err.get_message())  
                    self._validation_errors.append(message)
            elif header == intent_parser_constants.COL_HEADER_CHANNEL:
                try:
                    if table_utils.is_valued_cells(cell_txt):
                        raise TableException('Identified %s as a numerical value when expecting alpha-numeric values.')
                    list_of_channels = [value for value in table_utils.extract_name_value(cell_txt)]
                    if len(list_of_channels) > 1:
                        message = 'Controls table for %s has more than one channel provided. Only the first channel will be used from %s.' % (intent_parser_constants.COL_HEADER_CHANNEL, cell_txt)
                        self._validation_warnings.append(message)
                    control_data['channel'] = list_of_channels[0]
                except TableException as err:
                    message = 'Controls table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_CHANNEL, err.get_message())  
                    self._validation_errors.append(message)
            elif header == intent_parser_constants.COL_HEADER_CONTROL_TIMEPOINT:
                try:
                    control_data['timepoint'] = table_utils.parse_and_append_value_unit(cell_txt, 'timepoints', self._timepoint_units)
                except TableException as err:
                    message = 'Controls table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_CONTROL_TIMEPOINT, err.get_message())  
                    self._validation_errors.append(message)
            elif header == intent_parser_constants.COL_HEADER_CONTENT:
                pass
        return control_data
    
    def get_validation_errors(self):
        return self._validation_errors

    def get_validation_warnings(self):
        return self._validation_warning
    
    def _get_header_index(self, header_name):
        header_row = self._table.get_row_by_index(self.TABLE_HEADER_ROW_INDEX)
        num_of_cells = self._table.number_of_cells(header_row)
        for cell_index in enumerate(num_of_cells):
            cell = self._table.get_cell_from_row(header_row, cell_index)
            cell_parser = IntentParserCell(cell)
            cell_content = cell_parser.get_contents()
            if cell_content == header_name:
                return cell_index
    
    def _get_control_type(self, text):
        result = None 
        for type in self._control_types:
            if type == text:
                result = type
                break
        if result is None:
            raise TableException('%s does not match one of the following control types: \n %s' % (text, ' ,'.join((map(str, self._control_types)))))
        return result
    

        