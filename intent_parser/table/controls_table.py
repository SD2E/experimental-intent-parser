from intent_parser.intent_parser_exceptions import TableException
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.table.table_utils as table_utils
import logging

class ControlsTable(object):
    """
    Process information from Intent Parser's Controls Table
    """
    _logger = logging.getLogger('intent_parser')
    
    TABLE_CAPTION_ROW_INDEX = 0
    TABLE_HEADER_ROW_INDEX = 1
    TABLE_DATA_ROW_INDEX = 2

    def __init__(self, intent_parser_table, control_types={}, fluid_units={}, timepoint_units={}):
        self._control_types = control_types
        self._fluid_units = fluid_units
        self._timepoint_units = timepoint_units
        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table 
        self._table_caption = ''
        self._header_indices = {}
    
    def get_table_caption(self):
        return self._table_caption
    
    def process_table(self):
        controls = []
        self._process_table_caption()
        for row_index in range(self.TABLE_DATA_ROW_INDEX, self._intent_parser_table.number_of_rows()):
            control_data = self._process_row(row_index)
            controls.append(control_data)
        return controls 
    
    def _process_table_caption(self):
        cell = self._intent_parser_table.get_cell(self.TABLE_CAPTION_ROW_INDEX, 0)
        table_name, _ = table_utils.extract_str_after_prefix(cell.get_text())
        self._table_caption = table_name
         
    def _process_row(self, row_index):
        row = self._intent_parser_table.get_row(row_index)
        control_data = {}
        for cell_index in range(len(row)):
            cell = self._intent_parser_table.get_cell(row_index, cell_index)
            # Cell type based on column header
            header_cell = self._intent_parser_table.get_cell(self.TABLE_HEADER_ROW_INDEX, cell_index)
            cell_type = header_cell.get_text()
            
            if intent_parser_constants.COL_HEADER_CONTROL_TYPE == cell_type:
                control_type = self._process_control_type(cell)
                if control_type:
                    control_data['type'] = control_type
            elif intent_parser_constants.COL_HEADER_CONTROL_STRAINS == cell_type:
                strains = self._process_control_strains(cell)    
                if strains:
                    control_data['strains'] = strains
            elif intent_parser_constants.COL_HEADER_CONTROL_CHANNEL == cell_type:
                channel = self._process_channels(cell)
                if channel:
                    control_data['channels'] = channel
            elif intent_parser_constants.COL_HEADER_CONTROL_CONTENT == cell_type:
                contents = self._process_contents(cell)
                if contents:
                    control_data['contents'] = contents
            elif intent_parser_constants.COL_HEADER_CONTROL_TIMEPOINT == cell_type:
                timepoint = self._process_timepoint(cell)
                if timepoint:
                    control_data['timepoints'] = timepoint
        
        return control_data 
    
    def _process_channels(self, cell):
        cell_content = cell.get_text()
        if table_utils.is_valued_cells(cell_content):
            message = ('Controls table has invalid %s value: '
                       'Identified %s as a numerical value when ' 
                       'expecting alpha-numeric values.') % (intent_parser_constants.COL_HEADER_CONTROL_CHANNEL, cell_content)
            self._validation_errors.append(message)
            return []
        list_of_channels = [value for value in table_utils.extract_name_value(cell_content)]
        if len(list_of_channels) > 1:
            message = ('Controls table for %s has more than one channel provided. '
                       'Only the first channel will be used from %s.') % (intent_parser_constants.COL_HEADER_CONTROL_CHANNEL, cell_content)
            self._logger.warning(message)
        return list_of_channels[0]
    
    def _process_contents(self, cell):
        list_of_contents = []
        text_with_urls = cell.get_text_with_url()
        for name, value, unit in table_utils.parse_and_append_named_value_unit(cell.get_text(), 'fluid', self._fluid_units):
            url = 'NO PROGRAM DICTIONARY ENTRY'
            if name in text_with_urls:
                url = text_with_urls[name]
            content_name = {'label' : name, 'sbh_uri' : url} 
            content = {'name' : content_name, 
                       'value' : float(value), 
                       'unit' : unit}
            list_of_contents.append(content)
        return list_of_contents
        
    def _process_control_strains(self, cell):
        cell_content = cell.get_text()
        if table_utils.is_valued_cells(cell_content):
            message = ('Controls table has invalid %s value: %s' 
                       'Identified %s as a numerical value when '
                       'expecting alpha-numeric values.') % (intent_parser_constants.COL_HEADER_CONTROL_STRAINS, cell_content)
            self._validation_errors.append(message)
            return []
        return [value for value in table_utils.extract_name_value(cell_content)]
                
    def _process_control_type(self, cell):
        control_type = cell.get_text()
        if control_type not in self._control_types:
            err = '%s does not match one of the following control types: \n %s' % (control_type, ' ,'.join((map(str, self._control_types))))
            message = 'Controls table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_CONTROL_TYPE, err)
            self._validation_errors.append(message)
            return []
        return control_type

    def _process_timepoint(self, cell):
        cell_content = cell.get_text()
        timepoint = []
        try:
            timepoint = table_utils.parse_and_append_value_unit(cell_content, 'timepoints', self._timepoint_units)
        except TableException as err:
            message = 'Controls table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_CONTROL_TYPE, err.get_message())
            self._validation_errors.append(message)
        return timepoint
        
    def get_validation_errors(self):
        return self._validation_errors

    def get_validation_warnings(self):
        return self._validation_warnings 
        