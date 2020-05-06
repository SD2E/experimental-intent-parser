from intent_parser.intent_parser_exceptions import TableException
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.table.table_utils as table_utils
import intent_parser.utils.intent_parser_utils as intent_parser_utils
import logging

class ControlsTable(object):
    """
    Process information from Intent Parser's Controls Table
    """
    _logger = logging.getLogger('intent_parser')

    def __init__(self, control_types={}, timepoint_units={}):
        self._control_types = control_types
        self._timepoint_units = timepoint_units
        self._validation_errors = []
        self._validation_warnings = []
    
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
    
    def _get_control_type(self, text):
        result = None 
        for type in self._control_types:
            if type == text:
                result = type
                break
        if result is None:
            raise TableException('%s does not match one of the following control types: \n %s' % (text, ' ,'.join((map(str, self._control_types)))))
        return result
    