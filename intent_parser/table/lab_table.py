import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.table.table_utils as table_utils
import logging

class LabTable(object):
    """
    Class for parsing Lab table
    """

    _logger = logging.getLogger('intent_parser')
    DEFAULT_LAB = 'tacc'
    
    def __init__(self, intent_parser_table):
        self._lab_content = {}
        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table
        self._table_caption = ''
        
       
    def process_table(self):
        self._table_caption = self._intent_parser_table.caption()
        for row_index in range(self._intent_parser_table.number_of_rows()):
            self._process_row(row_index)
        
        result = {intent_parser_constants.HEADER_LAB_VALUE : self.DEFAULT_LAB,
                  intent_parser_constants.HEADER_EXPERIMENT_ID_VALUE : 'experiment.%s.TBD' % self.DEFAULT_LAB}
        
        if intent_parser_constants.HEADER_LAB_VALUE in self._lab_content:
            result[intent_parser_constants.HEADER_LAB_VALUE] = self._lab_content['lab']
        
        if intent_parser_constants.HEADER_EXPERIMENT_ID_VALUE in self._lab_content:
            result[intent_parser_constants.HEADER_EXPERIMENT_ID_VALUE] = 'experiment.%s.%s' % (result['lab'].lower(),
                                                                                               self._lab_content[intent_parser_constants.HEADER_EXPERIMENT_ID_VALUE])
        else:
            result[intent_parser_constants.HEADER_EXPERIMENT_ID_VALUE] = 'experiment.%s.%s' % (result['lab'].lower(), 'TBD')
        
        return result
    
    def get_validation_errors(self):
        return self._validation_errors
    
    def get_validation_warnings(self):
        return self._validation_warnings
    
    def _process_row(self, row_index):
        row = self._intent_parser_table.get_row(row_index)
        for cell_index in range(len(row)):
            cell = self._intent_parser_table.get_cell(row_index, cell_index)
            text = cell.get_text()
            if text.lower().startswith(intent_parser_constants.HEADER_LAB_VALUE):
                lab_name = self._process_content(cell.get_text(), intent_parser_constants.HEADER_LAB_VALUE)
                if lab_name:
                    self._lab_content[intent_parser_constants.HEADER_LAB_VALUE] = lab_name
            elif text.lower().startswith(intent_parser_constants.HEADER_EXPERIMENT_ID_VALUE):
                experiment_id = self._process_content(cell.get_text(), intent_parser_constants.HEADER_EXPERIMENT_ID_VALUE)
                if experiment_id:
                    self._lab_content[intent_parser_constants.HEADER_EXPERIMENT_ID_VALUE] = experiment_id
                else:
                    self._lab_content[intent_parser_constants.HEADER_EXPERIMENT_ID_VALUE] = 'TBD'
                    
    def _process_content(self, text, keyword):
        prefix, postfix = table_utils.extract_str_after_prefix(text)
        if prefix.lower() != keyword:
            self._validation_errors.append('Lab table has invalid value: Expected text to begin with %s but got %s' % (keyword, prefix))
            return None
        return postfix
            