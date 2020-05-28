import intent_parser.utils.intent_parser_utils as intent_parser_utils
import intent_parser.table.table_utils as table_utils
import logging

class LabTable(object):
    """
    Class for parsing Lab table
    """
    EXPERIMENT_ID_PREFIX = 'experiment'
    _logger = logging.getLogger('intent_parser')

    def __init__(self, intent_parser_table):
        self._lab_content = {}
        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table
       
    def process_table(self, table):
        for row_index in range(table.number_of_rows()):
            self._process_row(table[row_index])
        
        result = {}
        if 'lab' not in self._lab_content:
            result['lab'] = 'tacc'
        else:
            result['lab'] = self._lab_content['lab']
        
        if 'experiment_id' not in self._lab_content:
            result['experiment_id'] = 'experiment.%s.TBD' % result['lab'].lower()
        else:
            result['experiment_id'] = 'experiment.%s.%s' % (result['lab'].lower(), self._lab_content['experiment_id'])
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
            if self._is_lab(text.lower()):
                self._parse_lab(text)
            elif self._is_experiment_id(text.lower()):
                self._parse_experiment_id(text)
            
    def _is_lab(self, cell_content):
        return cell_content.startswith('lab')
        
    def _parse_lab(self, cell_content):
        prefix, postfix = table_utils.extract_str_after_prefix(cell_content)
        if prefix.lower() != 'lab':
            self._validation_errors.append('Lab table has invalid value: Expecting the starting phrase to begin with lab but got %s' % prefix)
            return
        
        if not postfix:
            self._lab_content['lab'] = 'tacc'
        else:
            self._lab_content['lab'] = postfix

    def _is_experiment_id(self, cell_content):
        return cell_content.startswith('experiment_id')
   
    def _parse_experiment_id(self, cell_content):
        prefix, postfix = table_utils.extract_str_after_prefix(cell_content)
        if prefix.lower() != 'experiment_id':
            self._validation_errors.append('Lab table has invalid value: Expecting the starting phrase to begin with experiment_id but got %s' % prefix)
            return 
        if not postfix:
            self._lab_content['experiment_id'] = 'TBD'
        else:
            self._lab_content['experiment_id'] = postfix
