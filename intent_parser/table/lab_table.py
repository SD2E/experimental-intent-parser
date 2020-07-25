import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.table.cell_parser as cell_parser
import logging

class LabTable(object):
    """
    Class for parsing Lab table
    """

    _logger = logging.getLogger('intent_parser')

    def __init__(self, intent_parser_table):
        self._lab_content = {dc_constants.LAB: ip_constants.TACC_SERVER,
                             dc_constants.EXPERIMENT_ID: 'TBD'}
        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table
        self._table_caption = None

    def process_table(self):
        self._table_caption = self._intent_parser_table.caption()
        for row_index in range(self._intent_parser_table.number_of_rows()):
            self._process_row(row_index)
        
        return {dc_constants.LAB: self._lab_content[dc_constants.LAB],
                dc_constants.EXPERIMENT_ID: 'experiment.%s.%s' % (self._lab_content[dc_constants.LAB].lower(),
                                                                  self._lab_content[dc_constants.EXPERIMENT_ID])}
    
    def get_validation_errors(self):
        return self._validation_errors
    
    def get_validation_warnings(self):
        return self._validation_warnings
    
    def _process_row(self, row_index):
        row = self._intent_parser_table.get_row(row_index)
        for cell_index in range(len(row)):
            cell = self._intent_parser_table.get_cell(row_index, cell_index)
            if cell_parser.PARSER.is_lab_table(cell.get_text()):
                self._lab_content[dc_constants.LAB] = cell_parser.PARSER.process_lab_name(cell.get_text())
            elif cell_parser.PARSER.has_lab_table_keyword(cell.get_text(), dc_constants.EXPERIMENT_ID):
                self._lab_content[dc_constants.EXPERIMENT_ID] = cell_parser.PARSER.process_lab_table_value(cell.get_text())
            else:
                self._validation_errors.append(
                    'Lab table has invalid value: %s is not supported in this table' % cell.get_text())
