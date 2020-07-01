import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.constants.sd2_datacatalog_constants as dictionary_constants
import intent_parser.table.cell_parser as cell_parser
import intent_parser.table.table_utils as table_utils
import logging

class LabTable(object):
    """
    Class for parsing Lab table
    """

    _logger = logging.getLogger('intent_parser')
    DEFAULT_LAB = 'tacc'
    
    def __init__(self, intent_parser_table):
        self._lab_content = {dictionary_constants.LAB: self.DEFAULT_LAB,
                             dictionary_constants.EXPERIMENT_ID: 'TBD'}
        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table
        self._table_caption = ''

    def process_table(self):
        self._table_caption = self._intent_parser_table.caption()
        for row_index in range(self._intent_parser_table.number_of_rows()):
            self._process_row(row_index)
        
        return {dictionary_constants.LAB: self._lab_content[dictionary_constants.LAB],
                dictionary_constants.EXPERIMENT_ID: 'experiment.%s.%s' % (self._lab_content[dictionary_constants.LAB].lower(),
                                                                          self._lab_content[dictionary_constants.EXPERIMENT_ID])}
    
    def get_validation_errors(self):
        return self._validation_errors
    
    def get_validation_warnings(self):
        return self._validation_warnings
    
    def _process_row(self, row_index):
        row = self._intent_parser_table.get_row(row_index)
        for cell_index in range(len(row)):
            cell = self._intent_parser_table.get_cell(row_index, cell_index)
            if cell_parser.PARSER.is_lab_table(cell):
                self._lab_content[dictionary_constants.LAB] = cell_parser.PARSER.process_lab_name(cell)
            elif cell_parser.PARSER.has_lab_table_keyword(cell, dictionary_constants.EXPERIMENT_ID):
                self._lab_content[dictionary_constants.EXPERIMENT_ID] = cell_parser.PARSER.process_lab_table_value(cell)
            else:
                self._validation_errors.append(
                    'Lab table has invalid value: %s is not supported in this table' % cell.get_text())
