from intent_parser.intent_parser_exceptions import TableException
from intent_parser.table.intent_parser_cell import IntentParserCell 
from intent_parser.table.intent_parser_table import IntentParserTable
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.table.table_utils as table_utils
import logging

class ControlsTable(object):
    """
    Process information from Intent Parser's Controls Table
    """
    _logger = logging.getLogger('intent_parser')
    
    TABLE_HEADER_ROW_INDEX = 0

    def __init__(self, table, control_types={}, fluid_units={}, timepoint_units={}):
        self._control_types = control_types
        self._fluid_units = fluid_units
        self._timepoint_units = timepoint_units
        self._validation_errors = []
        self._validation_warnings = []
        self._table = IntentParserTable(table)
       
    def process_table(self):
        controls = []
        for row_index in enumerate(self._table.number_of_rows(), start=1):
            row = self._table.get_row_by_index(row_index)
            control_data = self._process_row(row)
            controls.append(control_data)
        return controls
                    
    def _process_row(self, row):
        control_type_index = self._get_header_index(intent_parser_constants.COL_HEADER_CONTROL_TYPE) 
        control_strains_index = self._get_header_index(intent_parser_constants.COL_HEADER_CONTROL_STRAINS) 
        channel_index = self._get_header_index(intent_parser_constants.COL_HEADER_CONTROL_CHANNEL) 
        contents_index = self._get_header_index(intent_parser_constants.COL_HEADER_CONTROL_CONTENT) 
        timepoint_index = self._get_header_index(intent_parser_constants.COL_HEADER_CONTROL_TIMEPOINT) 
        
        control_data = {}
        content_data = {}
        num_of_cells = self._table.number_of_cells(row)
        for cell_index in enumerate(num_of_cells):
            cell = self._table.get_cell_from_row(row, cell_index)
            cell_parser = IntentParserCell(cell)
            cell_txt = cell_parser.get_contents()
            if cell_index == control_type_index:
                control_type = self._process_control_type(cell_txt)
                if control_type:
                    control_data['type'] = control_type
            elif cell_index == control_strains_index:
                strains = self._process_control_strains(cell_txt)    
                if strains:
                    control_data['strains'] = strains
            elif cell_index == channel_index:
                channel = self._process_channels(cell_txt)
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
    
    def _process_channels(self, cell_txt):
        if table_utils.is_valued_cells(cell_txt):
            message = ('Controls table has invalid %s value: '
                       'Identified %s as a numerical value when ' 
                       'expecting alpha-numeric values.') % (intent_parser_constants.COL_HEADER_CONTROL_CHANNEL, cell_txt)
            self._validation_errors.append(message)
            return []
        list_of_channels = [value for value in table_utils.extract_name_value(cell_txt)]
        if len(list_of_channels) > 1:
            message = ('Controls table for %s has more than one channel provided. '
                       'Only the first channel will be used from %s.') % (intent_parser_constants.COL_HEADER_CONTROL_CHANNEL, cell_txt)
            self._validation_warnings.append(message)
        return list_of_channels[0]
    
    def _process_contents(self, cell):
        cell_parser = IntentParserCell(cell)
        cell_txt = cell_parser.get_contents()
        str_with_links = cell_parser.get_links_to_words()
        name, value, unit = table_utils.parse_and_append_named_value_unit(cell_txt, 'fluid', self._fluid_units)
        
        url = 'NO PROGRAM DICTIONARY ENTRY'
        if name in str_with_links:
            url = str_with_links[name]
        
        content_name = {'label' : name, 'sbh_uri' : url} 
        return {'name' : content_name, 'value' : float(value), 'unit' : unit}
        
    def _process_control_strains(self, cell_txt):
        if table_utils.is_valued_cells(cell_txt):
            message = ('Controls table has invalid %s value: %s' 
                       'Identified %s as a numerical value when '
                       'expecting alpha-numeric values.') % (intent_parser_constants.COL_HEADER_CONTROL_STRAINS, cell_txt)
            self._validation_errors.append(message)
            return []
        return [value for value in table_utils.extract_name_value(cell_txt)]
                
    def _process_control_type(self, cell_txt):
        if cell_txt not in self._control_types:
            err = '%s does not match one of the following control types: \n %s' % (cell_txt, ' ,'.join((map(str, self._control_types))))
            message = 'Controls table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_CONTROL_TYPE, err)
            self._validation_errors.append(message)
            return None
        
        return cell_txt

    def _process_timepoint(self, cell_txt):
        timepoint = None
        try:
            timepoint = table_utils.parse_and_append_value_unit(cell_txt, 'timepoints', self._timepoint_units)
        except TableException as err:
            message = 'Controls table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_CONTROL_TYPE, err.get_message())
            self._validation_errors.append(message)
        return timepoint
        
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
    
        