from intent_parser.intent_parser_exceptions import TableException
import intent_parser.utils.intent_parser_utils as intent_parser_utils
import intent_parser.table.table_utils as table_utils
import logging

class LabTable(object):
    """
    Class for parsing Lab table
    """
    EXPERIMENT_ID_PREFIX = 'experiment'
    _logger = logging.getLogger('intent_parser')

    def __init__(self):
        self._lab_content = {}
        self._validation_errors = []
        self._validation_warnings = []
       
    def parse_table(self, table):
        rows = table['tableRows']
        for row in rows:
            self._parse_row(row)
        
        result = {}
        if 'lab' not in self._lab_content:
            result['lab'] = 'tacc'
            self._validation_errors('Lab table is missing a lab name')
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
    
    def _parse_row(self, row):
        cells = row['tableCells']
        for i in range(len(cells)): 
            cell_content = intent_parser_utils.get_paragraph_text(cells[i]['content'][0]['paragraph']).strip()
            if self._is_lab(cell_content.lower()):
                self._parse_lab(cell_content)
            elif self._is_experiment_id(cell_content.lower()):
                self._parse_experiment_id(cell_content)
            
    def _is_lab(self, cell_content):
        return cell_content.startswith('lab')
        
    def _parse_lab(self, cell_content):
        try:
            lab_name = table_utils.extract_name_from_str(cell_content, 'lab:')
            if not lab_name:
                raise TableException('lab name is empty.')
            self._lab_content['lab'] = lab_name
        except (ValueError, TableException) as err:
            self._validation_errors.append('Lab table has invalid %s value: %s' % ('lab name', err.get_message()))
    
    def _is_experiment_id(self, cell_content):
        return cell_content.startswith('experiment_id')
   
    def _parse_experiment_id(self, cell_content):
        try:
            experiment_id = table_utils.extract_name_from_str(cell_content, 'experiment_id:')
            if not experiment_id:
                experiment_id = 'TBD'
            self._lab_content['experiment_id'] = experiment_id
        except (ValueError, TableException) as err:
            self._lab_content['experiment_id'] = 'TBD' 
            self._validation_warnings.append('Lab table has invalid %s value: %s' % ('experiment_id', err.get_message()))
    