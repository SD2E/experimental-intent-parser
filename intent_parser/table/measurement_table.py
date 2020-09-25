from intent_parser.intent.measurement_intent import Measurement, MeasurementIntent
from intent_parser.intent_parser_exceptions import TableException
import intent_parser.table.cell_parser as cell_parser
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.constants.sbol_dictionary_constants as dictionary_constants
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import logging

class MeasurementTable(object):
    """
    Process information from Intent Parser's Measurement Table
    """
    _logger = logging.getLogger('intent_parser')
    IGNORE_COLUMNS = [intent_parser_constants.HEADER_SAMPLES_TYPE, intent_parser_constants.HEADER_NOTES_TYPE]
    
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
        self.measurement_intent = MeasurementIntent()

    def get_structured_request(self):
        return self.measurement_intent.to_structured_request()
    
    def process_table(self, control_tables={}, bookmarks={}):
        self._table_caption = self._intent_parser_table.caption()
        control_mappings = self._process_control_mapping(control_tables, bookmarks) 
        for row_index in range(self._intent_parser_table.data_row_start_index(), self._intent_parser_table.number_of_rows()):
            measurement = self._process_row(row_index, control_mappings)
            if measurement.to_structured_request():
                self.measurement_intent.add_measurement(measurement)

    def _process_control_mapping(self, control_tables, bookmarks):
        table_caption_index = {}
        if bookmarks:
            table_caption_index = self._map_bookmarks_to_captions(control_tables, bookmarks)
        # if bookmarks produce empty result, process control table's caption
        if not table_caption_index:
            try:
                if control_tables:
                    table_caption_index = self._map_captions_to_control(control_tables)
            except TableException as err:
                self._validation_errors.append('Measurement table has invalid %s value: %s' % (intent_parser_constants.HEADER_CONTROL_VALUE, err))
        return table_caption_index

    def _map_captions_to_control(self, control_tables):
        control_map = {}
        for table_caption, control_data in control_tables.items():
            if table_caption:
                control_map[table_caption] = control_data
        if not control_map:
            raise TableException('No reference to a Control table.')
        return control_map
                
    def _map_bookmarks_to_captions(self, control_tables, bookmarks):
        control_map = {}
        for bookmark in bookmarks:
            table_index = cell_parser.PARSER.process_table_caption_index(bookmark['text'])
            if table_index in control_tables:
                control_map[table_index] = control_tables[table_index]
        return control_map
    
    def _process_row(self, row_index, control_data):
        row = self._intent_parser_table.get_row(row_index)
        measurement = Measurement()
        content = []
        for cell_index in range(len(row)):
            cell = self._intent_parser_table.get_cell(row_index, cell_index)
            # Cell type based on column header
            header_cell = self._intent_parser_table.get_cell(self._intent_parser_table.header_row_index(), cell_index)
            cell_type = cell_parser.PARSER.get_header_type(header_cell.get_text())
            
            if not cell.get_text().strip() or cell_type in self.IGNORE_COLUMNS:
                continue
            
            if intent_parser_constants.HEADER_MEASUREMENT_TYPE_TYPE == cell_type:
                self._process_measurement_type(cell, measurement)
            elif intent_parser_constants.HEADER_FILE_TYPE_TYPE == cell_type:
                self._process_file_type(cell, measurement)
            elif intent_parser_constants.HEADER_REPLICATE_TYPE == cell_type:
                self._process_replicate(cell, measurement)
            elif intent_parser_constants.HEADER_STRAINS_TYPE == cell_type:
                self._process_strains(cell, measurement)
            elif intent_parser_constants.HEADER_ODS_TYPE == cell_type:
                self._process_ods(cell, measurement)
            elif intent_parser_constants.HEADER_TEMPERATURE_TYPE == cell_type:
                self._process_temperature(cell, measurement)
            elif intent_parser_constants.HEADER_TIMEPOINT_TYPE == cell_type:
                self._process_timepoints(cell, measurement)
            elif intent_parser_constants.HEADER_BATCH_TYPE == cell_type:
                self._process_batch(cell, measurement)
            elif intent_parser_constants.HEADER_CONTROL_TYPE == cell_type:
                self._process_control(cell, control_data, measurement)
            else:
                reagents = self._process_reagent_media(cell, header_cell)
                if reagents:
                    content.append(reagents)
        if content:
            measurement.add_field(dc_constants.CONTENTS, content)

        return measurement
    
    def _process_reagent_media(self, cell, header_cell):
        reagents_media = []
        text = cell.get_text()
        name_dict, timepoint_dict = cell_parser.PARSER.process_reagent_header(header_cell.get_text(),
                                                                              header_cell.get_text_with_url(),
                                                                              units=self._timepoint_units,
                                                                              unit_type='timepoints')
        # Determine if cells is numerical or name value 
        if cell_parser.PARSER.is_valued_cell(text):
            try:
                list_value_unit = cell_parser.PARSER.process_values_unit(text, units=self._fluid_units, unit_type='fluid')
                for value_unit_dict in list_value_unit:
                    numerical_dict = {dc_constants.NAME: name_dict,
                                      dc_constants.VALUE: str(float(value_unit_dict['value'])),
                                      dc_constants.UNIT: value_unit_dict['unit']}
                    if timepoint_dict:
                        numerical_dict[dc_constants.TIMEPOINT] = timepoint_dict
                    reagents_media.append(numerical_dict)
            except TableException as err:
                message = err.get_message()
                self._validation_errors.append(message)
        elif cell_parser.PARSER.is_number(text):
            err = '%s is missing a unit' % text
            message = 'Measurement table has invalid reagent/media value: %s' % err
            self._validation_errors.append(message)
            return []
        else:
            for name in cell_parser.PARSER.extract_name_value(text):
                named_dict = {dc_constants.NAME: name_dict, dc_constants.VALUE: name}
                if timepoint_dict:
                    named_dict[dc_constants.TIMEPOINT] = timepoint_dict
                reagents_media.append(named_dict)
        return reagents_media

    def get_validation_errors(self):
        return self._validation_errors

    def get_validation_warnings(self):
        return self._validation_warnings
    
    def _process_batch(self, cell, measurement):
        text = cell.get_text()
        try:
            batch = [int(value) for value in cell_parser.PARSER.process_numbers(text)]
            measurement.add_field(dc_constants.BATCH, batch)
        except TableException as err:
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.HEADER_BATCH_VALUE, err)
            self._validation_errors.append(message)
    
    def _process_control(self, cell, control_tables, measurement):
        result = []
        if not control_tables:
            self._validation_errors.append('Unable to process controls from a Measurement table without Control Tables.')
            return result

        if cell.get_bookmark_ids():
            result = self._process_control_with_bookmarks(cell, control_tables)

        if not result:
            result = self._process_control_with_captions(cell, control_tables)
        measurement.add_field(dc_constants.CONTROLS, result)

    def _process_control_with_bookmarks(self, cell, control_tables):
        controls = []
        for bookmark_id in cell.get_bookmark_ids():
            if bookmark_id in control_tables:
                for control in control_tables[bookmark_id]:
                    controls.append(control)
        return controls
    
    def _process_control_with_captions(self, cell, control_tables):
        controls = []
        for table_caption in cell_parser.PARSER.extract_name_value(cell.get_text()):
            table_index = cell_parser.PARSER.process_table_caption_index(table_caption)
            if table_index in control_tables:
                for control in control_tables[table_index]:
                    controls.append(control)
        return controls       
           
    def _process_file_type(self, cell, measurement):
        file_types = [value for value in cell_parser.PARSER.extract_name_value(cell.get_text())]
        result = []
        for file_type in file_types:
            if file_type not in self._file_type:
                err = '%s does not match one of the following file types: \n %s' % (file_type, ' ,'.join((map(str, self._file_type))))
                message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.HEADER_FILE_TYPE_VALUE, err)
                self._validation_errors.append(message)
            else:
                result.append(file_type)

        if not result:
            err = '%s does not match one of the following file types: \n %s' % (cell.get_text(), ' ,'.join((map(str, self._file_type))))
            message = 'Measurement table has invalid %s value: %s' % (
            intent_parser_constants.HEADER_FILE_TYPE_VALUE, err)
            self._validation_errors.append(message)
        else:
            measurement.add_field(dc_constants.FILE_TYPE, result)

    def _process_measurement_type(self, cell, measurement):
        measurement_type = cell.get_text().strip()
        if measurement_type not in self._measurement_types:
            err = '%s does not match one of the following measurement types: \n %s' % (measurement_type, ' ,'.join((map(str, self._measurement_types))))
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.HEADER_MEASUREMENT_TYPE_VALUE, err)
            self._validation_errors.append(message)
        else:
            measurement.add_field(dc_constants.MEASUREMENT_TYPE, measurement_type)

    def _process_ods(self, cell, measurement):
        try:
            ods = [float(value) for value in cell_parser.PARSER.process_numbers(cell.get_text())]
            measurement.add_field(dc_constants.ODS, ods)
        except TableException as err:
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.HEADER_ODS_VALUE, err)
            self._validation_errors.append(message)

    def _process_replicate(self, cell, measurement):
        text = cell.get_text()
        try:
            list_of_replicates = cell_parser.PARSER.process_numbers(text)
            if len(list_of_replicates) > 1:
                message = ('Measurement table for %s has more than one replicate provided.'
                           'Only the first replicate will be used from %s.') % (intent_parser_constants.HEADER_REPLICATE_VALUE, text)
                self._logger.warning(message)
            measurement.add_field(dc_constants.REPLICATES, int(list_of_replicates[0]))
        except TableException as err:
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.HEADER_REPLICATE_VALUE, err)
            self._validation_errors.append(message)
        
    def _process_strains(self, cell, measurement):
        strains = []
        for input_strain, link in cell_parser.PARSER.process_names_with_uri(cell.get_text(), text_with_uri=cell.get_text_with_url()):
            parsed_strain = input_strain.strip()
            if link is None:
                message = ('Measurement table has invalid %s value: %s is missing a SBH URI.' % (intent_parser_constants.HEADER_STRAINS_VALUE, parsed_strain))
                self._validation_errors.append(message)
                continue

            if link not in self.strain_mapping:
                message = ('Measurement table has invalid %s value: '
                           '%s is an invalid link not supported in the SBOL Dictionary Strains tab.' % (intent_parser_constants.HEADER_STRAINS_VALUE, link))
                self._validation_errors.append(message)
                continue

            strain = self.strain_mapping[link]
            if not strain.has_lab_name(parsed_strain):
                lab_name = dictionary_constants.MAPPED_LAB_UID[strain.get_lab_id()]
                message = 'Measurement table has invalid %s value: %s is not listed under %s in the SBOL Dictionary.' % (intent_parser_constants.HEADER_STRAINS_VALUE,
                                                                                                                         parsed_strain,
                                                                                                                         lab_name)
                self._validation_errors.append(message)
                continue

            strain_obj = {dc_constants.SBH_URI: link,
                          dc_constants.LABEL: strain.get_common_name(),
                          dc_constants.LAB_ID: 'name.%s.%s' % (strain.get_lab_id().lower(), parsed_strain)}
            strains.append(strain_obj)

        if strains:
            measurement.add_field(dc_constants.STRAINS, strains)

    def _process_temperature(self, cell, measurement):
        text = cell.get_text()
        try:
            result = []
            for value_unit in cell_parser.PARSER.process_values_unit(text,
                                                                     units=self._temperature_units,
                                                                     unit_type='temperature'):
                temperature = {dc_constants.VALUE: float(value_unit['value']),
                               dc_constants.UNIT: value_unit['unit']}
                result.append(temperature)
            measurement.add_field(dc_constants.TEMPERATURES, result)
        except TableException as err:
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.HEADER_TEMPERATURE_VALUE, err.get_message())
            self._validation_errors.append(message)

    def _process_timepoints(self, cell, measurement):
        text = cell.get_text()
        try:
            result = []
            for value_unit in cell_parser.PARSER.process_values_unit(text, units=self._timepoint_units, unit_type='timepoints'):
                timepoint = {dc_constants.VALUE: float(value_unit['value']),
                             dc_constants.UNIT: value_unit['unit']}
                result.append(timepoint)
            measurement.add_field(dc_constants.TIMEPOINTS, result)
        except TableException as err:
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.HEADER_TIMEPOINT_VALUE, err.get_message())
            self._validation_errors.append(message)

