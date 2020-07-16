from intent_parser.intent_parser_exceptions import IntentParserException
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.table.cell_parser as cell_parser
import logging


class ExperimentStatusTableParser(object):
    """
    Process information from Intent Parser's Controls Table
    """
    _logger = logging.getLogger('intent_parser')

    def __init__(self, intent_parser_table=None):
        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table
        self._table_caption = None
        self._statuses = set()

    def get_table_caption(self):
        """
        Retrieves the table caption.
        Returns:
            An integer value. None is returned is the table does not have a table caption.
        """
        return self._table_caption

    def add_status(self, status_type, last_updated, state, path):
        status = self._Status(status_type, last_updated, state, path)
        self._statuses.add(status)

    def get_statuses(self):
        """
        Retrieves a set of statuses parsed from the table.
        Returns:
            A set of _Status objects. Information available to access from a _Status object are:
            _Status.status_type: A string for representing the type of job performed on an experiment.
            _Status.last_updated: A datetime object for indicating when the type of job was last performed.
            _Status.state: A boolean for representing whether the job has been processed.
            _Status.path: A String to reference the location where the output data for the executed job was generated.
        """
        return self._statuses

    def process_table(self):
        self._table_caption = self._intent_parser_table.caption()
        for row_index in range(self._intent_parser_table.data_row_index(), self._intent_parser_table.number_of_rows()):
            self._process_row(row_index)

    def compare_statuses(self, set_of_status):
        """Check if this status table is equivalent to a list of _Status object
        Args:
            set_of_status: A set of _Status objects
        Returns:
            A boolean value. True if the list is equivalent to this table set of statuses. Otherwise, False is returned.
        """
        if len(set_of_status) != len(self._statuses):
            return False
        return self._statuses.isdisjoint(set_of_status)

    def diff_status(self, set_of_status):
        """
        Retrieve a set of Status() objects not contained in this table
        Args:
            set_of_status: A set of _Status objects
        Returns:
            A set of _Status objects from set_of_status not contained within this table.
        """
        return self._statuses.difference(set_of_status)


    def _process_row(self, row_index):
        row = self._intent_parser_table.get_row(row_index)
        status = self._Status()
        for cell_index in range(len(row)):
            cell = self._intent_parser_table.get_cell(row_index, cell_index)
            # Cell type based on column header
            header_row_index = self._intent_parser_table.header_row_index()
            header_cell = self._intent_parser_table.get_cell(header_row_index, cell_index)
            cell_type = cell_parser.PARSER.get_header_type(header_cell.get_text())
            if not cell.get_text():
                continue
            if intent_parser_constants.HEADER_PIPELINE_STATUS_TYPE == cell_type:
                self._process_status_type(cell, status)
            elif intent_parser_constants.HEADER_LAST_UPDATED_TYPE == cell_type:
                self._process_last_updated(cell, status)
            elif intent_parser_constants.HEADER_PATH_TYPE == cell_type:
                self._process_path(cell, status)
            elif intent_parser_constants.HEADER_STATE_TYPE == cell_type:
                self._process_state(cell, status)
        self._statuses.add(status)

    def _process_status_type(self, cell, status):
        cell_text = cell.get_text()
        if cell_parser.PARSER.is_name(cell_text):
            status_type = cell_parser.PARSER.process_names(cell_text)
            if len(status_type) != 1:
                message = 'More than one %s detected from %s. Only the first status will be used.' % (
                intent_parser_constants.HEADER_PIPELINE_STATUS_VALUE, cell.get_text())
                self._validation_warnings.append(message)
            status.status_type = status_type[0]
        else:
            message = 'Experiment status table has invalid %s value: %s should be a name' % (
            intent_parser_constants.HEADER_PIPELINE_STATUS_TYPE, cell.get_text())
            self._validation_errors.append(message)

    def _process_last_updated(self, cell, status):
        try:
            status.last_updated = cell_parser.PARSER.process_datetime_format(cell.get_text())
        except ValueError as err:
            message = 'Experiment status table has invalid %s value: %s' % (
                intent_parser_constants.HEADER_PIPELINE_STATUS_TYPE, str(err))
            self._validation_errors.append(message)

    def _process_path(self, cell, status):
        cell_text = cell.get_text()
        if cell_parser.PARSER.is_name(cell_text):
            status_type = cell_parser.PARSER.process_names(cell_text)
            if len(status_type) != 1:
                message = 'More than one %s detected from %s. Only the first status will be used.' % (
                intent_parser_constants.HEADER_PATH_VALUE, cell_text)
                self._validation_warnings.append(message)
            status.path = status_type[0]
        else:
            message = 'Experiment status table has invalid %s value: %s should be a name' % (
            intent_parser_constants.HEADER_PATH_VALUE, cell_text)
            self._validation_errors.append(message)

    def _process_state(self, cell, status):
        cell_text = cell.get_text()
        boolean_value = cell_parser.PARSER.process_boolean_flag(cell_text)
        if boolean_value is None:
            non_boolean_state = cell_parser.PARSER.process_names(cell_text)
            status.state = non_boolean_state[0]
        else:
            status.state = boolean_value

    class _Status(object):

        def __init__(self, status_type='', last_updated='', state='', path=''):
            self.status_type = status_type
            self.last_updated = last_updated
            self.state = state
            self.path = path

        def __hash__(self):
            return hash((self.status_type, self.last_updated, self.state, self.path))

        def __eq__(self, other):
            if not isinstance(other, type(self)):
                raise IntentParserException('%s is not the same type as %s' % (type(other), type(self)))

            return (self.status_type == other.status_type
                    and self.last_updated == other.last_updated
                    and self.state == other.state
                    and self.path == other.path)
