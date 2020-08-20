from datetime import datetime
from intent_parser.table.intent_parser_table import IntentParserTable
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.constants.ta4_db_constants as ta4_constants
import intent_parser.table.cell_parser as cell_parser
import logging


class ExperimentStatusTableParser(object):
    """
    Process information from Intent Parser's Controls Table
    """
    _logger = logging.getLogger('intent_parser')

    def __init__(self, intent_parser_table=None, status_mappings={}):
        if not intent_parser_table:
            self._intent_parser_table = IntentParserTable()
        else:
            self._intent_parser_table = intent_parser_table

        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table
        self._table_caption = None

        self.status_mappings = status_mappings
        self.status_xplan_request_submitted = None
        self.status_uploaded = None
        self.status_converted = None
        self.status_mtypes = None
        self.status_comparison_passed = None
        self.status_annotated = None
        self.status_ingested = None
        self.status_obs_load = None

    def get_intent_parser_table(self):
        return self._intent_parser_table

    def get_table_caption(self):
        """
        Retrieves the table caption.
        Returns:
            An integer value. None is returned is the table does not have a table caption.
        """
        return self._table_caption

    def set_table_caption(self, index):
        self._table_caption = index

    def add_status(self, status_type, last_updated, state, path):
        status = self._Status(self.status_mappings, status_type, last_updated, state, path)
        self._set_status(status)

    def num_of_columns(self):
        return 4

    def num_of_rows(self):
        return 10

    def to_dict(self):
        result = {}
        if self.status_xplan_request_submitted:
           result[self.status_xplan_request_submitted.status_type] = self.status_xplan_request_submitted.to_dict()
        if self.status_uploaded:
            result[self.status_uploaded.status_type] = self.status_uploaded.to_dict()
        if self.status_converted:
            result[self.status_converted.status_type] = self.status_converted.to_dict()
        if self.status_mtypes:
            result[self.status_mtypes.status_type] = self.status_mtypes.to_dict()
        if self.status_comparison_passed:
            result[self.status_comparison_passed.status_type] = self.status_comparison_passed.to_dict()
        if self.status_annotated:
            result[self.status_annotated.status_type] = self.status_annotated.to_dict()
        if self.status_ingested:
            result[self.status_ingested.status_type] = self.status_ingested.to_dict()
        if self.status_obs_load:
            result[self.status_obs_load.status_type] = self.status_obs_load.to_dict()

        return result

    def get_statuses(self):
        """
        Retrieve statuses parsed form the table.
        Returns:
            A list of _Status objects.
        """
        if self.status_xplan_request_submitted is None:
            self.status_xplan_request_submitted = self._create_default_status(ta4_constants.XPLAN_REQUEST_SUBMITTED)
        if self.status_uploaded is None:
            self.status_uploaded = self._create_default_status(ta4_constants.UPLOADED)
        if self.status_converted is None:
            self.status_converted = self._create_default_status(ta4_constants.CONVERTED)
        if self.status_mtypes is None:
            self.status_mtypes = self._create_default_status(ta4_constants.MTYPES)
        if self.status_comparison_passed is None:
            self.status_comparison_passed = self._create_default_status(ta4_constants.COMPARISON_PASSED)
        if self.status_annotated is None:
            self.status_annotated = self._create_default_status(ta4_constants.ANNOTATED)
        if self.status_ingested is None:
            self.status_ingested = self._create_default_status(ta4_constants.INGESTED)
        if self.status_obs_load is None:
            self.status_obs_load = self._create_default_status(ta4_constants.OBS_LOAD)

        return [self.status_xplan_request_submitted,
                self.status_uploaded,
                self.status_converted,
                self.status_mtypes,
                self.status_comparison_passed,
                self.status_annotated,
                self.status_ingested,
                self.status_obs_load]

    def _create_default_status(self, tacc_id):
        default_status = self._Status(self.status_mappings, tacc_id, datetime.now(), 'unspecified', 'no data')
        return default_status

    def process_table(self):
        self._table_caption = self._intent_parser_table.caption()
        for row_index in range(self._intent_parser_table.data_row_start_index(), self._intent_parser_table.number_of_rows()):
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

    def _process_row(self, row_index):
        row = self._intent_parser_table.get_row(row_index)
        status = self._Status(status_mappings=self.status_mappings)
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

        self._set_status(status)

    def _set_status(self, status):
        if status.status_type == ta4_constants.XPLAN_REQUEST_SUBMITTED:
            self.status_xplan_request_submitted = status
        elif status.status_type == ta4_constants.UPLOADED:
            self.status_uploaded = status
        elif status.status_type == ta4_constants.CONVERTED:
            self.status_converted = status
        elif status.status_type == ta4_constants.MTYPES:
            self.status_mtypes = status
        elif status.status_type == ta4_constants.COMPARISON_PASSED:
            self.status_comparison_passed = status
        elif status.status_type == ta4_constants.ANNOTATED:
            self.status_annotated = status
        elif status.status_type == ta4_constants.INGESTED:
            self.status_ingested = status
        elif status.status_type == ta4_constants.OBS_LOAD:
            self.status_obs_load = status
        else:
            self._logger.warning('%s is not a experiment status supported in Intent Parser' % status.status_type)

    def _process_status_type(self, cell, status):
        cell_text = cell.get_text().strip()
        type = [tacc_id for tacc_id, common_name in self.status_mappings.items() if cell_text == common_name]
        if len(type) == 0:
            status.status_type = 'Unknown'
        else:
            if len(type) != 1:
                self._logger.warning('More than one status TACC UID are assigned to Common Name %s' % cell_text)
            status.status_type = type[0]

    def _process_last_updated(self, cell, status):
        try:
            status.last_updated = cell_parser.PARSER.process_datetime_format(cell.get_text().strip())
        except ValueError as err:
            message = 'Experiment status table has invalid %s value: %s' % (
                intent_parser_constants.HEADER_PIPELINE_STATUS_TYPE, str(err))
            self._validation_errors.append(message)

    def _process_path(self, cell, status):
        cell_text = cell.get_text().strip()
        if cell_parser.PARSER.is_name(cell_text):
            status_type = [status for status, _ in cell_parser.PARSER.process_names_with_uri(cell_text)]
            if len(status_type) > 1:
                message = 'More than one %s detected from %s. Only the first status will be used.' % (
<<<<<<< HEAD
                           intent_parser_constants.HEADER_PATH_VALUE, cell_text)
                self._logger.warning(message)
=======
                intent_parser_constants.HEADER_PATH_VALUE, cell_text)
                self._validation_warnings.append(message)
>>>>>>> ba244faa0a4b619dd483f7c4a848ac304d9b4a23
            status.path = status_type[0]
        else:
            message = 'Experiment status table has invalid %s value: %s should be a file path.' % (
            intent_parser_constants.HEADER_PATH_VALUE, cell_text)
            self._validation_errors.append(message)

    def _process_state(self, cell, status):
        cell_text = cell.get_text().strip().lower()
        if cell_text == 'succeeded':
            status.state = True
        elif cell_text == 'failed':
            status.state = False
        elif cell_text == 'not complete':
            status.state = False

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        return (self.status_xplan_request_submitted == other.status_xplan_request_submitted
                and self.status_uploaded == other.status_uploaded
                and self.status_converted == other.status_converted
                and self.status_mtypes == other.status_mtypes
                and self.status_comparison_passed == other.status_comparison_passed
                and self.status_annotated == other.status_annotated
                and self.status_ingested == other.status_ingested
                and self.status_obs_load == other.status_obs_load)

    class _Status(object):

        def __init__(self, status_mappings, status_type='', last_updated='', state='', path=''):
            self.status_type = status_type
            self.last_updated = last_updated
            self.state = state
            self.path = path
            self.status_mappings = status_mappings

        def __hash__(self):
            return hash((self.status_type, self.last_updated, self.state, self.path))

        def __eq__(self, other):
            if not isinstance(other, type(self)):
                return False

            return (self.status_type == other.status_type
                    and self.last_updated == other.last_updated
                    and self.state == other.state
                    and self.path == other.path)

        def get_status_type(self):
            if self.status_type in self.status_mappings:
                return self.status_mappings[self.status_type]
            return self.status_type

        def get_last_updated(self):
            return '%s/%s/%s %s:%s:%s' % (self.last_updated.year,
                                          self.last_updated.month,
                                          self.last_updated.day,
                                          self.last_updated.hour,
                                          self.last_updated.minute,
                                          self.last_updated.second)

        def get_state(self):
            if self.state is True:
                return 'Succeeded'
            elif self.state is False:
                return 'Failed'
            elif self.state.lower() is 'file loaded':
                return 'Succeeded'
            return 'Not Complete'

        def get_path(self):
            return self.path

        def to_dict(self):
            return {
                    'last_updated': self.get_last_updated(),
                    'state': self.state,
                    'path': self.path
            }