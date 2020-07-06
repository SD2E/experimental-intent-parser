from intent_parser.intent_parser_exceptions import TableException
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.table.cell_parser as cell_parser
import logging

class ExperimentStatusTable(object):
    """
    Process information from Intent Parser's Controls Table
    """
    _logger = logging.getLogger('intent_parser')

    def __init__(self, intent_parser_table=None):
        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table
        self._table_caption = ''
        self._statuses = {}

    def get_table_caption(self):
        return self._table_caption

    def add_status(self, status_type, last_updated, state, path):
        status = self._Status(status_type, last_updated, state, path)
        self._statuses.append(status)

    def get_statuses(self):
        return self._statuses

    def process_table(self):
        self._table_caption = self._intent_parser_table.caption()
        for row_index in range(self._intent_parser_table.data_row_index(), self._intent_parser_table.number_of_rows()):
            self._process_row(row_index)

    def _process_row(self, row_index):
        row = self._intent_parser_table.get_row(row_index)
        control_data = {}

        status = self._Status()
        for cell_index in range(len(row)):
            cell = self._intent_parser_table.get_cell(row_index, cell_index)
            # Cell type based on column header
            header_row_index = self._intent_parser_table.header_row_index()
            header_cell = self._intent_parser_table.get_cell(header_row_index, cell_index)
            cell_type = cell_parser.PARSER.get_header_type(header_cell)
            if not cell.get_text():
                continue
            if intent_parser_constants.HEADER_PIPELINE_STATUS_TYPE == cell_type:
                self._process_status_type(cell, status)
            elif intent_parser_constants.HEADER_LAST_UPDATED_TYPE == cell_type:
                self._process_last_updated(cell, status)
            elif intent_parser_constants.HEADER_PATH_TYPE == cell_type:
                self._process_path(cell, status)
            elif intent_parser_constants.HEADER_STATE == cell_type:
                self._process_state(cell, status)
        self._statuses.append(status)

    def _process_status_type(self, cell, status):
        if cell_parser.PARSER.is_name(cell):
            status_type = cell_parser.PARSER.process_names(cell)
            if len(status_type) != 1:
                message = 'More than one %s detected from %s. Only the first status will be used.' % (intent_parser_constants.HEADER_PIPELINE_STATUS_VALUE, cell.get_text())
                self._validation_warnings.append(message)
            status.status_type = status_type[0]
        else:
            message = 'Experiment status table has invalid %s value: %s should be a name' % (intent_parser_constants.HEADER_PIPELINE_STATUS_TYPE, cell.get_text())
            self._validation_errors.append(message)

    def _process_last_updated(self, cell, status):
        if cell_parser.PARSER.is_datetime_format(cell):
            pass # TODO
        else:
            message = 'Experiment status table has invalid %s value: %s should follow a datetime format.' % (
            intent_parser_constants.HEADER_PIPELINE_STATUS_TYPE, cell.get_text())
            self._validation_errors.append(message)

    def _process_path(self, cell, status):
        if cell_parser.PARSER.is_name(cell):
            status_type = cell_parser.PARSER.process_names(cell)
            if len(status_type) != 1:
                message = 'More than one %s detected from %s. Only the first status will be used.' % (intent_parser_constants.HEADER_PATH_VALUE, cell.get_text())
                self._validation_warnings.append(message)
            status.status_type = status_type[0]
        else:
            message = 'Experiment status table has invalid %s value: %s should be a name' % (intent_parser_constants.HEADER_PATH_VALUE, cell.get_text())
            self._validation_errors.append(message)

    def _process_state(self, cell, status):
        boolean_value = cell_parser.PARSER.process_boolean_flag(cell)
        if boolean_value is None:
            non_boolean_state = cell_parser.PARSER.process_names(cell)
            status.state = non_boolean_state[0]
        else:
            status.state = boolean_value

    class _Status(object):

        def __init__(self, status_type='', last_updated='', state='', path=''):
            self.status_type = status_type
            self.last_updated = last_updated
            self.state = state
            self.path = path

