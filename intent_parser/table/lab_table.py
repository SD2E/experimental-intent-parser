from intent_parser.intent.lab_intent import LabIntent
from intent_parser.table.intent_parser_table import IntentParserTable
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.table.cell_parser as cell_parser
import logging

class LabTable(object):
    """
    Process contents from a lab table.
    """

    _logger = logging.getLogger('intent_parser')

    def __init__(self, intent_parser_table=None, lab_names={}):
        if not intent_parser_table:
            self._intent_parser_table = IntentParserTable()
        else:
            self._intent_parser_table = intent_parser_table
        self.lab_intent = LabIntent()
        self._lab_names = lab_names
        self._validation_errors = []
        self._validation_warnings = []
        self._table_caption = None

    def get_intent(self):
        return self.lab_intent

    def get_structured_request(self):
        return self.lab_intent.to_structured_request()

    def process_table(self):
        self._table_caption = self._intent_parser_table.caption()
        for row_index in range(self._intent_parser_table.number_of_rows()):
            self._process_row(row_index)
        
    def get_validation_errors(self):
        return self._validation_errors
    
    def get_validation_warnings(self):
        return self._validation_warnings
    
    def _process_row(self, row_index):
        row = self._intent_parser_table.get_row(row_index)
        for cell_index in range(len(row)):
            cell = self._intent_parser_table.get_cell(row_index, cell_index)
            if cell_parser.PARSER.has_lab_table_keyword(cell.get_text(), dc_constants.LAB):
                self._process_lab_name(cell)
            elif cell_parser.PARSER.has_lab_table_keyword(cell.get_text(), dc_constants.EXPERIMENT_ID):
                self._process_experiment_id(cell)
            else:
                self._validation_errors.append(
                    'Lab table has invalid value: %s is not supported in this table' % cell.get_text())

    def _process_lab_name(self, cell):
        lab_name = cell_parser.PARSER.process_lab_name(cell.get_text())
        if lab_name:
            canonicalize_lab_names = [lab.lower() for lab in self._lab_names]
            processed_lab_name = lab_name.lower()
            if processed_lab_name in canonicalize_lab_names:
                self.lab_intent.set_lab_id(lab_name)
            else:
                err = '%s does not match one of the following lab names: \n %s' % (cell.get_text(), ' ,'.join((map(str, self._lab_names))))
                message = 'Lab table has invalid %s value: %s' % (ip_constants.HEADER_LAB_VALUE, err)
                self._validation_errors.append(message)
        else:
            err = '%s does not follow the correct format for specifying a lab name.' % (cell.get_text())
            message = 'Lab table has invalid %s value: %s' % (ip_constants.HEADER_LAB_VALUE, err)
            self._validation_errors.append(message)

    def _process_experiment_id(self, cell):
        experiment_id = cell_parser.PARSER.process_lab_table_value(cell.get_text())
        if experiment_id:
            self.lab_intent.set_experiment_id(experiment_id)

