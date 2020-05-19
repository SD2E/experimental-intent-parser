from intent_parser.intent_parser_exceptions import TableException
from intent_parser.table.intent_parser_table import IntentParserTable
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

    def __init__(self, intent_parser_table, control_types={}, fluid_units={}, timepoint_units={}):
        self._control_types = control_types
        self._fluid_units = fluid_units
        self._timepoint_units = timepoint_units
        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table 
        self._table_caption = ''
    
    def get_table_caption(self):
        return self._table_caption
    
    def process_table(self):
        controls = []
        
        self._process_table_caption(self._table.get_row(self.TABLE_CAPTION_ROW_INDEX))
        for row_index in range(2, self._table.number_of_rows()):
            row = self._table.get_row_by_index(row_index)
            control_data = self._process_row(row)
            controls.append(control_data)
        return controls 
    
    def _process_table_caption(self, row):
        cell = self._table.get_row(row, 0)
        for cell_txt, _ in table_utils.parse_cell(cell):
            table_name = table_utils.extract_table_caption(cell_txt.lower())
            self._table_caption = table_name
                    
    def _process_row(self, row):
        control_type_index = self._get_header_index(intent_parser_constants.COL_HEADER_CONTROL_TYPE) 
        control_strains_index = self._get_header_index(intent_parser_constants.COL_HEADER_CONTROL_STRAINS) 
        channel_index = self._get_header_index(intent_parser_constants.COL_HEADER_CONTROL_CHANNEL) 
        contents_index = self._get_header_index(intent_parser_constants.COL_HEADER_CONTROL_CONTENT) 
        timepoint_index = self._get_header_index(intent_parser_constants.COL_HEADER_CONTROL_TIMEPOINT) 
        
        control_data = {}
        content_data = {}
        for cell_index in range(len(row)):
            cell = self._table.get_cell(row, cell_index)
            if cell_index == control_type_index:
                control_type = self._process_control_type(cell)
                if control_type:
                    control_data['type'] = control_type
            elif cell_index == control_strains_index:
                strains = self._process_control_strains(cell)    
                if strains:
                    control_data['strains'] = strains
            elif cell_index == channel_index:
                channel = self._process_channels(cell)
                if channel:
                    control_data['channels'] = channel
            elif cell_index == contents_index:
                content_data = self._process_contents(cell)
            elif cell_index == timepoint_index:
                timepoint = self._process_timepoint(cell)
                if timepoint:
                    content_data['timepoints'] = timepoint
        
        control_data['contents'] = [content_data]
        return control_data
    
    def _process_channels(self, cell):
        cell_content = ''.join([cell_txt for cell_txt, _ in table_utils.parse_cell(cell)])
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
        for cell_txt, url in table_utils.parse_cell(cell):
            canonicalize_cell = cell_txt.strip() 
            for name, value, unit in table_utils.parse_and_append_named_value_unit(canonicalize_cell, 'fluid', self._fluid_units):
                content_name = {'label' : name, 'sbh_uri' : url} 
                content = {'name' : content_name, 
                       'value' : float(value), 
                       'unit' : unit}
            list_of_contents.append(content)
        return list_of_contents
        
    def _process_control_strains(self, cell):
        cell_content = ''.join([cell_txt for cell_txt, _ in table_utils.parse_cell(cell)])
        if table_utils.is_valued_cells(cell_content):
            message = ('Controls table has invalid %s value: %s' 
                       'Identified %s as a numerical value when '
                       'expecting alpha-numeric values.') % (intent_parser_constants.COL_HEADER_CONTROL_STRAINS, cell_content)
            self._validation_errors.append(message)
            return []
        return [value for value in table_utils.extract_name_value(cell_content)]
                
    def _process_control_type(self, cell):
        control_type = ''.join([cell_txt for cell_txt, _ in table_utils.parse_cell(cell)]).strip()
        if control_type not in self._control_types:
            err = '%s does not match one of the following control types: \n %s' % (control_type, ' ,'.join((map(str, self._control_types))))
            message = 'Controls table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_CONTROL_TYPE, err)
            self._validation_errors.append(message)
            return []
        return control_type

    def _process_timepoint(self, cell):
        cell_content = ''.join([cell_txt for cell_txt, _ in table_utils.parse_cell(cell)])
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
    
    def _get_header_index(self, header_name):
        header_row = self._table.get_row(self.TABLE_HEADER_ROW_INDEX)
        for cell_index in range(len(header_row)):
            cell = self._table.get_cell(header_row, cell_index)
            cell_content = ''.join([cell_txt for cell_txt, _ in table_utils.parse_cell(cell)]).strip()
            if cell_content == header_name:
                return cell_index
    
        