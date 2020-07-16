import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.table.cell_parser as cell_parser

class ExperimentSpecificationTable(object):

    def __init__(self, intent_parser_table, lab_names):
        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table
        self._table_caption = None
        self._experiment_id_to_status = {}

    def get_mappings_for_experiment_id_and_status_table(self, ref_status_table_index):
        return self._experiment_id_to_status

    def get_table_caption(self):
        return self._table_caption

    def process_table(self):
        self._table_caption = self._intent_parser_table.caption()
        for row_index in range(self._intent_parser_table.data_row_index(), self._intent_parser_table.number_of_rows()):
            self._process_row(row_index)

    def _process_row(self, row_index):
        experiment_id = None
        experiment_status = None
        row = self._intent_parser_table.get_row(row_index)
        for cell_index in range(len(row)):
            cell = self._intent_parser_table.get_cell(row_index, cell_index)
            # Cell type based on column header
            header_row_index = self._intent_parser_table.header_row_index()
            header_cell = self._intent_parser_table.get_cell(header_row_index, cell_index)
            cell_type = cell_parser.PARSER.get_header_type(header_cell)
            if not cell.get_text():
                continue
            if intent_parser_constants.HEADER_EXPERIMENT_ID_VALUE == cell_type:
                experiment_id = self._process_experiment_id(cell)
            elif intent_parser_constants.HEADER_EXPERIMENT_STATUS_VALUE == cell_type:
                experiment_status = self._process_experiment_status(cell)

        if experiment_id is None:
            self._validation_errors.append('Experiment Status Table has invalid %s value: Unable to parse information from cell' % intent_parser_constants.HEADER_EXPERIMENT_ID_VALUE)
        if experiment_status is None:
            self._validation_errors.append('Experiment Status Table has invalid %s value: Unable to parse information from cell' % intent_parser_constants.HEADER_EXPERIMENT_STATUS_VALUE)
        self._experiment_id_to_status[experiment_id] = experiment_status

    def _process_experiment_id(self, cell):
        lab_names = []

        if cell_parser.is_experiment_id(cell, lab_names):
            return cell.get_text()
        else:
            message = 'Experiment Status Table has invalid %s value: %s must follow experiment.lab_name.experiment_id' \
                      % (intent_parser_constants.HEADER_EXPERIMENT_ID_VALUE, cell.get_text())
            self._validation_errors.append(message)
            return None

    def _process_experiment_status(self, cell):
        if cell_parser.PARSER.is_table_caption(cell.get_text()):
            table_index = cell_parser.PARSER.process_table_caption_index(cell.get_text())
            return table_index
        else:
            message = 'Experiment Status Table has invalid %s value: %s does not reference a Table' \
                      % (intent_parser_constants.HEADER_EXPERIMENT_STATUS_VALUE, cell.get_text())
            self._validation_errors.append(message)
            return None
