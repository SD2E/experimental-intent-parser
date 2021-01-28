from intent_parser.intent.measurement_intent import ContentIntent, MeasurementIntent
from intent_parser.intent.measure_property_intent import MediaIntent, NamedBooleanValue, NamedIntegerValue, NamedLink, NamedStringValue, ReagentIntent, TemperatureIntent, TimepointIntent
from intent_parser.intent_parser_exceptions import TableException
import intent_parser.table.cell_parser as cell_parser
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.constants.sbol_dictionary_constants as dictionary_constants
import logging

class MeasurementTable(object):
    """
    Process information from Intent Parser's Measurement Table
    """
    _logger = logging.getLogger('intent_parser')
    IGNORE_COLUMNS = [ip_constants.HEADER_SAMPLES_TYPE,
                      ip_constants.HEADER_NOTES_TYPE]
    
    def __init__(self,
                 intent_parser_table,
                 temperature_units={},
                 timepoint_units={},
                 fluid_units={},
                 measurement_types={},
                 file_type={},
                 strain_mapping={}):
        self._temperature_units = temperature_units
        self._timepoint_units = timepoint_units
        self._fluid_units = fluid_units
        self._measurement_types = measurement_types
        self._file_type = file_type
        self.strain_mapping = strain_mapping

        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table 
        self._table_caption = None
        self._measurement_intents = []

    def get_intents(self):
        return self._measurement_intents

    def get_structured_request(self):
        return [measurement.to_structure_request() for measurement in self._measurement_intents]
    
    def process_table(self, control_data={}, bookmarks={}):
        self._table_caption = self._intent_parser_table.caption()
        control_mappings = self._process_control_mapping(control_data, bookmarks)
        for row_index in range(self._intent_parser_table.data_row_start_index(), self._intent_parser_table.number_of_rows()):
            measurement = self._process_row(row_index, control_mappings)
            if not measurement.is_empty():
                self._measurement_intents.append(measurement)

    def _process_control_mapping(self, control_data, bookmarks):
        control_mapping = {}
        if bookmarks:
            control_mapping = self._map_control_with_bookmarks(control_data, bookmarks)

        # if bookmarks produce empty result, process control table's caption
        if not control_mapping:
            try:
                if control_data:
                    control_mapping = self._map_control_with_captions(control_data)
            except TableException as err:
                self._validation_errors.append('Measurement table has invalid %s value: %s' % (ip_constants.HEADER_CONTROL_VALUE, err))
        return control_mapping

    def _map_control_with_captions(self, control_tables):
        control_map = {}
        for table_caption, control_data in control_tables.items():
            if table_caption:
                control_map[table_caption] = control_data
        if not control_map:
            raise TableException('No reference to a Control table.')
        return control_map
                
    def _map_control_with_bookmarks(self, control_tables, bookmarks):
        control_map = {}
        for bookmark in bookmarks:
            table_index = cell_parser.PARSER.process_table_caption_index(bookmark['text'])
            if table_index in control_tables:
                control_map[table_index] = control_tables[table_index]
        return control_map
    
    def _process_row(self, row_index, control_data):
        row = self._intent_parser_table.get_row(row_index)
        measurement = MeasurementIntent()
        content_intent = ContentIntent()

        row_offset = row_index # Used for reporting row value to users
        for cell_index in range(len(row)):
            cell = self._intent_parser_table.get_cell(row_index, cell_index)

            # Cell type based on column header
            header_cell = self._intent_parser_table.get_cell(self._intent_parser_table.header_row_index(), cell_index)
            cell_type = cell_parser.PARSER.get_header_type(header_cell.get_text())

            column_offset = cell_index # Used for reporting column value to users
            if not cell.get_text().strip() or cell_type in self.IGNORE_COLUMNS:
                continue

            if ip_constants.HEADER_MEASUREMENT_TYPE_TYPE == cell_type:
                self._process_measurement_type(cell, measurement, row_offset, column_offset)
            elif ip_constants.HEADER_FILE_TYPE_TYPE == cell_type:
                self._process_file_type(cell, measurement, row_offset, column_offset)
            elif ip_constants.HEADER_REPLICATE_TYPE == cell_type:
                self._process_replicate(cell, measurement, row_offset, column_offset)
            elif ip_constants.HEADER_STRAINS_TYPE == cell_type:
                self._process_strains(cell, measurement, row_offset, column_offset)
            elif ip_constants.HEADER_ODS_TYPE == cell_type:
                self._process_ods(cell, measurement, row_offset, column_offset)
            elif ip_constants.HEADER_TEMPERATURE_TYPE == cell_type:
                self._process_temperature(cell, measurement, row_offset, column_offset)
            elif ip_constants.HEADER_TIMEPOINT_TYPE == cell_type:
                self._process_timepoints(cell, measurement, row_offset, column_offset)
            elif ip_constants.HEADER_BATCH_TYPE == cell_type:
                self._process_batch(cell, measurement, row_offset, column_offset)
            elif ip_constants.HEADER_CONTROL_TYPE == cell_type:
                self._process_control(cell, control_data, measurement)
            elif ip_constants.HEADER_NUM_NEG_CONTROL_TYPE == cell_type:
                num_neg_controls = self._process_num_neg_controls(cell, row_offset, column_offset)
                if num_neg_controls:
                    content_intent.set_numbers_of_negative_controls(num_neg_controls)
            elif ip_constants.HEADER_RNA_INHIBITOR_REACTION_TYPE == cell_type:
                rna_inhibitor_reactions = self._process_rna_inhibitor_reaction(cell, row_offset, column_offset)
                if rna_inhibitor_reactions:
                    content_intent.set_rna_inhibitor_reaction_flags(rna_inhibitor_reactions)
            elif ip_constants.HEADER_DNA_REACTION_CONCENTRATION_TYPE == cell_type:
                dna_reaction_concentrations = self._process_dna_reaction_concentration(cell, row_offset, column_offset)
                if dna_reaction_concentrations:
                    content_intent.set_dna_reaction_concentrations(dna_reaction_concentrations)
            elif ip_constants.HEADER_TEMPLATE_DNA_TYPE == cell_type:
                dna_templates = self._process_template_dna(cell, row_offset, column_offset)
                if dna_templates:
                    content_intent.set_template_dna_values(dna_templates)
            elif ip_constants.HEADER_COLUMN_ID_TYPE == cell_type:
                column_ids = self._process_col_id(cell, row_offset, column_offset)
                if column_ids:
                    content_intent.set_column_ids(column_ids)
            elif ip_constants.HEADER_ROW_ID_TYPE == cell_type:
                row_ids = self._process_row_id(cell, row_offset, column_offset)
                if row_ids:
                    content_intent.set_row_ids(row_ids)
            elif ip_constants.HEADER_MEASUREMENT_LAB_ID_TYPE == cell_type:
                lab_ids = self._process_lab_id(cell, row_offset, column_offset)
                if lab_ids:
                    content_intent.set_lab_ids(lab_ids)
            else:
                reagents_and_medias = self._process_reagent_or_media(cell, header_cell, row_offset, column_offset)
                for reagent_or_media in reagents_and_medias:
                    if isinstance(reagent_or_media, ReagentIntent):
                        content_intent.add_reagent(reagent_or_media)
                    elif isinstance(reagent_or_media, MediaIntent):
                        content_intent.add_media(reagent_or_media)

        if not content_intent.is_empty():
            measurement.add_content(content_intent)
        return measurement

    def _process_lab_id(self, cell, row_index, column_index):
        lab_ids = []
        try:
            for value in cell_parser.PARSER.extract_name_value(cell.get_text()):
                name = NamedLink('lab_id')
                lab_id = NamedStringValue(name, value)
                lab_ids.append(lab_id)
        except TableException as err:
            message = ('Measurement table at row %d column %d has invalid %s value: %s') % (row_index,
                                                                                            column_index,
                                                                                            ip_constants.HEADER_LAB_ID_VALUE,
                                                                                            err.get_message())
            self._validation_errors.append(message)
        return lab_ids

    def _process_row_id(self, cell, row_index, column_index):
        row_ids = []
        try:
            for value in cell_parser.PARSER.process_numbers(cell.get_text()):
                name = NamedLink('row_id')
                row_id = NamedIntegerValue(name, int(value))
                row_ids.append(row_id)
        except TableException as err:
            message = 'Measurement table at row %d column %d has invalid %s value: %s' % (row_index,
                                                                                          column_index,
                                                                                          ip_constants.HEADER_ROW_ID_VALUE,
                                                                                          err)
            self._validation_errors.append(message)

        return row_ids

    def _process_col_id(self, cell, row_index, column_index):
        column_ids = []
        try:
            for value in cell_parser.PARSER.process_numbers(cell.get_text()):
                name = NamedLink('column_id')
                col_id = NamedIntegerValue(name, int(value))
                column_ids.append(col_id)
        except TableException as err:
            message = 'Measurement table at row %d column %d has invalid %s value: %s' % (row_index,
                                                                                          column_index,
                                                                                          ip_constants.HEADER_COLUMN_ID_VALUE,
                                                                                          err)
            self._validation_errors.append(message)

        return column_ids
    
    def _process_reagent_or_media(self, cell, header_cell, row_index, column_index):
        result = []
        text = cell.get_text()
        try:
            named_link, timepoint = cell_parser.PARSER.process_reagent_or_media_header(header_cell.get_text(),
                                                                                       header_cell.get_text_with_url(),
                                                                                       units=self._timepoint_units,
                                                                                       unit_type='timepoints')
        except TableException as err:
            message = err.get_message()
            self._validation_errors.append(message)
            return []

        if cell_parser.PARSER.is_valued_cell(text):
            # content is of type reagent if cell contais value with units
            try:
                measured_units = cell_parser.PARSER.process_values_unit(text,
                                                                        units=self._fluid_units,
                                                                        unit_type='fluid')
                for measured_unit in measured_units:
                    reagent = ReagentIntent(named_link, float(measured_unit.get_value()), measured_unit.get_unit())
                    if timepoint is not None:
                        reagent.set_timepoint(timepoint)

                    result.append(reagent)
            except TableException as err:
                message = err.get_message()
                self._validation_errors.append(message)
        elif cell_parser.PARSER.is_number(text):
            err = '%s is missing a unit' % text
            message = ('Measurement table at row %d column %d has invalid reagent/media value: %s' % (row_index,
                                                                                                      column_index,
                                                                                                      err))
            self._validation_errors.append(message)
        else:
            # content must be of type media if cell contains list of string
            for name, media_link in cell_parser.PARSER.process_names_with_uri(cell.get_text(), text_with_uri=cell.get_text_with_url()):
                media_value = NamedLink(name, link=media_link)
                media = MediaIntent(named_link, media_value)
                if timepoint is not None:
                    media.set_timepoint(timepoint)
                result.append(media)

        return result

    def get_validation_errors(self):
        return self._validation_errors

    def get_validation_warnings(self):
        return self._validation_warnings
    
    def _process_batch(self, cell, measurement, row_index, column_index):
        text = cell.get_text()
        try:
            for value in cell_parser.PARSER.process_numbers(text):
                measurement.add_batch(int(value))
        except TableException as err:
            message = 'Measurement table at row %d column %d has invalid %s value: %s' % (row_index,
                                                                                          column_index,
                                                                                          ip_constants.HEADER_BATCH_VALUE,
                                                                                          err)
            self._validation_errors.append(message)
    
    def _process_control(self, cell, control_data, measurement):
        if not control_data:
            self._validation_errors.append('Unable to process controls from a Measurement table without Control Tables.')

        control_intents = []
        if cell.get_bookmark_ids():
            control_intents = self._process_control_with_bookmarks(cell, control_data)

        # if processing control by bookmark_id did not work, process by table index value
        if len(control_intents) == 0:
            control_intents = self._process_control_with_captions(cell, control_data)

        for control_intent in control_intents:
            measurement.add_control(control_intent)


    def _process_control_with_bookmarks(self, cell, control_tables):
        controls = []
        for bookmark_id in cell.get_bookmark_ids():
            if bookmark_id in control_tables:
                for control in control_tables[bookmark_id]:
                    controls.append(control)
        return controls
    
    def _process_control_with_captions(self, cell, control_tables):
        control_intents = []
        for table_caption in cell_parser.PARSER.extract_name_value(cell.get_text()):
            table_index = cell_parser.PARSER.process_table_caption_index(table_caption)
            if table_index in control_tables:
                for control in control_tables[table_index]:
                    control_intents.append(control)
        return control_intents
           
    def _process_dna_reaction_concentration(self, cell, row_index, column_index):
        dna_reaction_concentrations = []
        try:
            for value in cell_parser.PARSER.process_numbers(cell.get_text()):
                name = NamedLink(ip_constants.HEADER_DNA_REACTION_CONCENTRATION_VALUE)
                dna_reaction_concentration = NamedIntegerValue(name, int(value))
                dna_reaction_concentrations.append(dna_reaction_concentration)
        except TableException as err:
            message = 'Measurement table at row %d column %d has invalid %s value: %s' % (row_index,
                                                                                          column_index,
                                                                                          ip_constants.HEADER_DNA_REACTION_CONCENTRATION_VALUE,
                                                                                          err)
            self._validation_errors.append(message)

        return dna_reaction_concentrations

    def _process_template_dna(self, cell, row_index, column_index):
        dna_templates = []
        try:
            for value in cell_parser.PARSER.extract_name_value(cell.get_text()):
                name = NamedLink(ip_constants.HEADER_TEMPLATE_DNA_VALUE)
                dna_template = NamedStringValue(name, value)
                dna_templates.append(dna_template)
        except TableException as err:
            message = 'Measurement table at row %d column %d has invalid %s value: %s' % (row_index,
                                                                                          column_index,
                                                                                          ip_constants.HEADER_TEMPLATE_DNA_VALUE,
                                                                                          err)
            self._validation_errors.append(message)
        return dna_templates

    def _process_file_type(self, cell, measurement, row_index, column_index):
        file_types = [value for value in cell_parser.PARSER.extract_name_value(cell.get_text())]
        for file_type in file_types:
            if file_type not in self._file_type:
                err = '%s does not match one of the following file types: \n %s' % (file_type, ' ,'.join((map(str, self._file_type))))
                message = 'Measurement table at row %d column %d has invalid %s value: %s' % (row_index,
                                                                                              column_index,
                                                                                              ip_constants.HEADER_FILE_TYPE_VALUE,
                                                                                              err)
                self._validation_errors.append(message)
            else:
                measurement.add_file_type(file_type)

    def _process_measurement_type(self, cell, measurement, row_index, column_index):
        measurement_type = cell.get_text().strip()
        if measurement_type not in self._measurement_types:
            err = '%s does not match one of the following measurement types: \n %s' % (measurement_type, ' ,'.join((map(str, self._measurement_types))))
            message = 'Measurement table at row %d column %d has invalid %s value: %s' % (row_index,
                                                                                          column_index,
                                                                                          ip_constants.HEADER_MEASUREMENT_TYPE_VALUE,
                                                                                          err)
            self._validation_errors.append(message)
        else:
            measurement.set_measurement_type(measurement_type)

    def _process_num_neg_controls(self, cell, row_index, column_index):
        num_neg_controls = []
        try:
            for value in cell_parser.PARSER.process_numbers(cell.get_text()):
                name = NamedLink(ip_constants.HEADER_NUMBER_OF_NEGATIVE_CONTROLS_VALUE)
                num_neg_control = NamedIntegerValue(name, int(value))
                num_neg_controls.append(num_neg_control)
        except TableException as err:
            message = 'Measurement table at row %d column %d has invalid %s value: %s' % (row_index,
                                                                                          column_index,
                                                                                          ip_constants.HEADER_NUMBER_OF_NEGATIVE_CONTROLS_VALUE,
                                                                                          err)
            self._validation_errors.append(message)

        return num_neg_controls

    def _process_ods(self, cell, measurement, row_index, column_index):
        try:
            for value in cell_parser.PARSER.process_numbers(cell.get_text()):
                measurement.add_optical_density(float(value))
        except TableException as err:
            message = 'Measurement table at row %d column %d has invalid %s value: %s' % (ip_constants.HEADER_ODS_VALUE,
                                                                                          row_index,
                                                                                          column_index,
                                                                                          err)
            self._validation_errors.append(message)

    def _process_replicate(self, cell, measurement, row_index, column_index):
        try:
            if not cell.get_text().strip():
                self._validation_warnings.append('Measurement table at row %d column %d does not have '
                                                 'any replicates provided.' % (row_index, column_index))
                return

            list_of_replicates = cell_parser.PARSER.process_numbers(cell.get_text())
            for replicate in list_of_replicates:
                measurement.add_replicate(int(replicate))
        except TableException as err:
            message = 'Measurement table at row %d column %d has invalid %s value: %s' % (row_index,
                                                                                          column_index,
                                                                                          ip_constants.HEADER_REPLICATE_VALUE,
                                                                                          err)
            self._validation_errors.append(message)

    def _process_rna_inhibitor_reaction(self, cell, row_index, column_index):
        rna_inhibitor_reactions = []
        try:
            for boolean_value in cell_parser.PARSER.process_boolean_flag(cell.get_text()):
                name = NamedLink(ip_constants.HEADER_USE_RNA_INHIBITOR_IN_REACTION_VALUE)
                rna_inhibitor_reaction = NamedBooleanValue(name, boolean_value)
                rna_inhibitor_reactions.append(rna_inhibitor_reaction)
        except TableException as err:
            message = 'Measurement table at row %d column %d has invalid %s value: %s' % (row_index,
                                                                                          column_index,
                                                                                          ip_constants.HEADER_USE_RNA_INHIBITOR_IN_REACTION_VALUE,
                                                                                          err)
            self._validation_errors.append(message)

        return rna_inhibitor_reactions

    def _process_strains(self, cell, measurement, row_index, column_index):
        for input_strain, link in cell_parser.PARSER.process_names_with_uri(cell.get_text(), text_with_uri=cell.get_text_with_url()):
            parsed_strain = input_strain.strip()
            if link is None:
                message = ('Measurement table at row %d column %d has invalid %s value: %s is missing a SBH URI.' % (row_index,
                                                                                                                     column_index,
                                                                                                                     ip_constants.HEADER_STRAINS_VALUE,
                                                                                                                     parsed_strain))
                self._validation_errors.append(message)
                continue

            if link not in self.strain_mapping:
                message = ('Measurement table at row %d column %d has invalid %s value: '
                           '%s is an invalid link not supported in the SBOL Dictionary Strains tab.' % (row_index,
                                                                                                        column_index,
                                                                                                        ip_constants.HEADER_STRAINS_VALUE,
                                                                                                        link))
                self._validation_errors.append(message)
                continue

            strain_intent = self.strain_mapping[link]
            if not strain_intent.has_lab_strain_name(parsed_strain):
                lab_name = dictionary_constants.MAPPED_LAB_UID[strain_intent.get_lab_id()]
                message = ('Measurement table at row %d column %d has invalid %s value: '
                           '%s is not listed under %s in the SBOL Dictionary.' % (row_index,
                                                                                  column_index,
                                                                                  ip_constants.HEADER_STRAINS_VALUE,
                                                                                  parsed_strain,
                                                                                  lab_name))
                self._validation_errors.append(message)
                continue

            strain_intent.set_selected_strain(parsed_strain)
            measurement.add_strain(strain_intent)

    def _process_temperature(self, cell, measurement, row_index, column_index):
        try:
            text = cell.get_text()
            for measured_unit in cell_parser.PARSER.process_values_unit(text,
                                                                        units=self._temperature_units,
                                                                        unit_type='temperature'):
                temperature = TemperatureIntent(float(measured_unit.get_value()), measured_unit.get_unit())
                measurement.add_temperature(temperature)
        except TableException as err:
            message = 'Measurement table at row %d column %d has invalid %s value: %s' % (row_index,
                                                                                          column_index,
                                                                                          ip_constants.HEADER_TEMPERATURE_VALUE,
                                                                                          err.get_message())
            self._validation_errors.append(message)

    def _process_timepoints(self, cell, measurement, row_index, column_index):
        text = cell.get_text()
        try:
            for measured_unit in cell_parser.PARSER.process_values_unit(text, units=self._timepoint_units, unit_type='timepoints'):
                timepoint = TimepointIntent(float(measured_unit.get_value()), measured_unit.get_unit())
                measurement.add_timepoint(timepoint)
        except TableException as err:
            message = 'Measurement table at row %d column %d has invalid %s value: %s' % (row_index,
                                                                                          column_index,
                                                                                          ip_constants.HEADER_TIMEPOINT_VALUE,
                                                                                          err.get_message())
            self._validation_errors.append(message)

