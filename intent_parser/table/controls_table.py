from intent_parser.intent.control_intent import ControlIntent
from intent_parser.intent.measurement_intent import TimepointIntent
from intent_parser.intent_parser_exceptions import TableException
import intent_parser.constants.sbol_dictionary_constants as dictionary_constants
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.table.cell_parser as cell_parser
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import logging

class ControlsTable(object):
    """
    Process information from Intent Parser's Controls Table
    """
    _logger = logging.getLogger('intent_parser')
    
    def __init__(self, intent_parser_table, control_types={}, fluid_units={}, timepoint_units={}, strain_mapping={}):
        self._control_types = control_types
        self._fluid_units = fluid_units
        self._strain_mapping = strain_mapping
        self._timepoint_units = timepoint_units
        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table 
        self._table_caption = ''
        self._control_intents = []

    def get_table_caption(self):
        return self._table_caption

    def get_intents(self):
        return self._control_intents

    def get_structure_request(self):
        return [control.to_structure_request() for control in self._control_intents]

    def get_validation_errors(self):
        return self._validation_errors

    def get_validation_warnings(self):
        return self._validation_warnings

    def process_table(self):
        self._table_caption = self._intent_parser_table.caption()
        for row_index in range(self._intent_parser_table.data_row_start_index(), self._intent_parser_table.number_of_rows()):
            self._process_row(row_index)

    def _process_row(self, row_index):
        row = self._intent_parser_table.get_row(row_index)
        control = ControlIntent()
        row_offset = row_index # Used for reporting row value to users

        for cell_index in range(len(row)):
            cell = self._intent_parser_table.get_cell(row_index, cell_index)
            # Cell type based on column header
            header_row_index = self._intent_parser_table.header_row_index()
            header_cell = self._intent_parser_table.get_cell(header_row_index, cell_index)
            cell_type = cell_parser.PARSER.get_header_type(header_cell.get_text())
            column_offset = cell_index # Used for reporting column value to users

            if not cell.get_text().strip():
                continue

            if intent_parser_constants.HEADER_CONTROL_TYPE_TYPE == cell_type:
                self._process_control_type(cell, control, row_offset, column_offset)
            elif intent_parser_constants.HEADER_STRAINS_TYPE == cell_type:
                self._process_control_strains(cell, control, row_offset, column_offset)
            elif intent_parser_constants.HEADER_CHANNEL_TYPE == cell_type:
                self._process_channels(cell, control, row_offset, column_offset)
            elif intent_parser_constants.HEADER_CONTENTS_TYPE == cell_type:
                self._process_contents(cell, control, row_offset, column_offset)
            elif intent_parser_constants.HEADER_TIMEPOINT_TYPE == cell_type:
                self._process_timepoint(cell, control, row_offset, column_offset)

        if not control.is_empty():
            self._control_intents.append(control)

    def _process_channels(self, cell, control, row_index, column_index):
        cell_content = cell.get_text()
        try:
            list_of_channels = cell_parser.PARSER.extract_name_value(cell_content)
            if len(list_of_channels) > 1:
                message = ('Controls table at row %d column %d has more than one %s provided. '
                           'Only the first channel will be used from %s.') % (row_index,
                                                                              column_index,
                                                                              intent_parser_constants.HEADER_CHANNEL_VALUE,
                                                                              cell_content)
                self._logger.warning(message)

            control.set_channel(list_of_channels[0])
        except TableException as err:
            message = ('Controls table for row %d column % has invalid %s value: %s') % (row_index,
                                                                                         column_index,
                                                                                         intent_parser_constants.HEADER_CHANNEL_VALUE,
                                                                                         err.get_message())
            self._validation_errors.append(message)
    
    def _process_contents(self, cell, control, row_index, column_index):
        try:
            contents = cell_parser.PARSER.parse_content_item(cell.get_text(),
                                                             cell.get_text_with_url(),
                                                             fluid_units=self._fluid_units,
                                                             timepoint_units=self._timepoint_units)
            for content in contents:
                control.add_content(content)
        except TableException as err:
            message = 'Controls table at row %d column %d has invalid %s value: %s' % (row_index,
                                                                                       column_index,
                                                                                       intent_parser_constants.HEADER_CONTENTS_VALUE,
                                                                                       err.get_message())
            self._validation_errors.append(message)

    def _process_control_strains(self, cell, control, row_index, column_index):
        for input_strain, link in cell_parser.PARSER.process_names_with_uri(cell.get_text(), text_with_uri=cell.get_text_with_url()):
            parsed_strain = input_strain.strip()
            if link is None:
                message = ('Controls table at row %d column %d has invalid %s value: %s is missing a SBH URI.' % (row_index,
                                                                                                                  column_index,
                                                                                                                  intent_parser_constants.HEADER_STRAINS_VALUE,
                                                                                                                  parsed_strain))
                self._validation_errors.append(message)
                continue

            if link not in self._strain_mapping:
                message = ('Controls table at row %d column %d has invalid %s value: '
                           '%s is an invalid link not supported in the SBOL Dictionary Strains tab.' % (row_index,
                                                                                                        column_index,
                                                                                                        intent_parser_constants.HEADER_STRAINS_VALUE,
                                                                                                        link))
                self._validation_errors.append(message)
                continue

            strain_intent = self._strain_mapping[link]
            if not strain_intent.has_lab_strain_name(parsed_strain):
                lab_name = dictionary_constants.MAPPED_LAB_UID[strain_intent.get_lab_id()]
                message = ('Controls table at row %d column %d has invalid %s value: '
                           '%s is not listed under %s in the SBOL Dictionary.' % (row_index,
                                                                                  column_index,
                                                                                  intent_parser_constants.HEADER_STRAINS_VALUE,
                                                                                  parsed_strain,
                                                                                  lab_name))
                self._validation_errors.append(message)
                continue

            strain_intent.set_selected_strain(parsed_strain)
            control.add_strain(strain_intent)

    def _process_control_type(self, cell, control, row_index, column_index):
        control_type = cell.get_text().strip()
        if control_type not in self._control_types:
            err = '%s does not match one of the following control types: \n %s' % (control_type, ' ,'.join((map(str, self._control_types))))
            message = 'Controls table at row %d column %d has invalid %s value: %s' % (row_index,
                                                                                       column_index,
                                                                                       intent_parser_constants.HEADER_CONTROL_TYPE_VALUE,
                                                                                       err)
            self._validation_errors.append(message)
        else:
            control.set_control_type(control_type)

    def _process_timepoint(self, cell, control, row_index, column_index):
        try:
            result = []
            for measured_unit in cell_parser.PARSER.process_values_unit(cell.get_text(),
                                                                     units=self._timepoint_units,
                                                                     unit_type='timepoints'):
                timepoint = TimepointIntent(float(measured_unit.get_value()), measured_unit.get_unit())
                control.add_timepoint(timepoint)
        except TableException as err:
            message = 'Controls table at row %d column % has invalid %s value: %s' % (row_index,
                                                                                      column_index,
                                                                                      intent_parser_constants.HEADER_CONTROL_TYPE_VALUE,
                                                                                      err.get_message())
            self._validation_errors.append(message)


