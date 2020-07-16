from intent_parser.intent_parser_exceptions import TableException
import intent_parser.table.cell_parser as cell_parser
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import logging

class MeasurementTable(object):
    """
    Process information from Intent Parser's Measurement Table
    """
    _logger = logging.getLogger('intent_parser')
    IGNORE_COLUMNS = [intent_parser_constants.HEADER_SAMPLES_TYPE, intent_parser_constants.HEADER_NOTES_TYPE]
    
    def __init__(self, intent_parser_table, temperature_units={}, timepoint_units={}, fluid_units={}, measurement_types={}, file_type={}):
        self._temperature_units = temperature_units
        self._timepoint_units = timepoint_units
        self._fluid_units = fluid_units
        self._measurement_types = measurement_types
        self._file_type = file_type
        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table 
        self._table_caption = None
    
    def process_table(self, control_tables={}, bookmarks={}):
        measurements = []
        self._table_caption = self._intent_parser_table.caption()
        control_mappings = self._process_control_mapping(control_tables, bookmarks) 
        for row_index in range(self._intent_parser_table.data_row_index(), self._intent_parser_table.number_of_rows()):
            measurement_data = self._process_row(row_index, control_mappings)
            if measurement_data:
                measurements.append(measurement_data)
        return measurements   
    
    def _process_control_mapping(self, control_tables, bookmarks):
        if bookmarks:
            return self._map_bookmarks_to_captions(control_tables, bookmarks)
        return self._map_captions_to_control(control_tables)

    def _map_captions_to_control(self, control_tables):
        control_map = {}
        for table_caption, control_data in control_tables.items():
            if table_caption:
                control_map[table_caption] = control_data
        return control_map
                
    def _map_bookmarks_to_captions(self, control_tables, bookmarks):
        control_map = {}
        for bookmark in bookmarks:
            if bookmark['text'] in control_tables:
                control_map[bookmark['id']] = control_tables[bookmark['text']]
        return control_map
    
    def _process_row(self, row_index, control_data):
        row = self._intent_parser_table.get_row(row_index)
        measurement = {}
        content = []
        for cell_index in range(len(row)):
            cell = self._intent_parser_table.get_cell(row_index, cell_index)
            # Cell type based on column header
            header_cell = self._intent_parser_table.get_cell(self._intent_parser_table.header_row_index(), cell_index)
            cell_type = cell_parser.PARSER.get_header_type(header_cell.get_text())
            
            if not cell.get_text() or cell_type in self.IGNORE_COLUMNS:
                continue
            
            elif intent_parser_constants.HEADER_MEASUREMENT_TYPE_TYPE == cell_type:
                measurement_type = self._process_measurement_type(cell)
                if measurement_type:
                    measurement['measurement_type'] = measurement_type
            elif intent_parser_constants.HEADER_FILE_TYPE_TYPE == cell_type:
                file_type = self._process_file_type(cell) 
                if file_type:
                    measurement['file_type'] = file_type  
            elif intent_parser_constants.HEADER_REPLICATE_TYPE == cell_type:
                replicates = self._process_replicate(cell)
                if replicates:
                    measurement['replicates'] = replicates
            elif intent_parser_constants.HEADER_STRAINS_TYPE == cell_type:
                strains = self._process_strains(cell)
                if strains:
                    measurement['strains'] = strains
            elif intent_parser_constants.HEADER_ODS_TYPE == cell_type:
                ods = self._process_ods(cell)
                if ods:
                    measurement['ods'] =ods
            elif intent_parser_constants.HEADER_TEMPERATURE_TYPE == cell_type:
                temperatures = self._process_temperature(cell)
                if temperatures:
                    measurement['temperatures'] = temperatures
            elif intent_parser_constants.HEADER_TIMEPOINT_TYPE == cell_type:
                timepoints = self._process_timepoints(cell)
                if timepoints:
                    measurement['timepoints'] = timepoints
            elif intent_parser_constants.HEADER_BATCH_TYPE == cell_type:
                batch = self._process_batch(cell)
                if batch:
                    measurement['batch'] = batch
            elif intent_parser_constants.HEADER_CONTROL_TYPE == cell_type:
                controls = self._process_control(cell, control_data)
                if controls:
                    measurement['controls'] = controls
            else:
                reagents = self._process_reagent_media(cell, header_cell)
                if reagents:
                    content.append(reagents)
        if content:
            measurement['contents'] = content
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
                    numerical_dict = {'name': name_dict,
                                      'value': value_unit_dict['value'],
                                      'unit': value_unit_dict['unit']}
                    if timepoint_dict:
                        numerical_dict['timepoint'] = timepoint_dict
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
                named_dict = {'name': name_dict, 'value': name}
                if timepoint_dict:
                    named_dict['timepoint'] = timepoint_dict
                reagents_media.append(named_dict)
        return reagents_media

    def get_validation_errors(self):
        return self._validation_errors

    def get_validation_warnings(self):
        return self._validation_warnings
    
    def _process_batch(self, cell):
        text = cell.get_text()
        if cell_parser.PARSER.is_name(text):
            err = '%s must contain a list of integer values.' % text
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.HEADER_BATCH_VALUE, err)
            self._validation_errors.append(message)
            return []
        return [int(value) for value in cell_parser.PARSER.process_numbers(text)]
    
    def _process_control(self, cell, control_tables):
        result = [] 
        if cell.get_bookmark_ids():
            result = self._process_control_with_bookmarks(cell, control_tables)
        if not result:
            return self._process_control_with_captions(cell, control_tables)
        return result
    
    def _process_control_with_bookmarks(self, cell, control_tables):
        controls = []
        for bookmark_id in cell.get_bookmark_ids():
            if bookmark_id in control_tables:
                for control in control_tables[bookmark_id]:
                    controls.append(control)
        return controls
    
    def _process_control_with_captions(self, cell, control_tables):
        controls = []
        for table_caption in cell_parser.PARSER.process_names(cell.get_text()):
            table_index = cell_parser.PARSER.process_table_caption_index(table_caption)
            if table_index in control_tables:
                for control in control_tables[table_index]:
                    controls.append(control)
        return controls       
           
    def _process_file_type(self, cell):
        file_type = cell.get_text()
        return [value for value in cell_parser.PARSER.process_names(file_type)]
    
    def _process_measurement_type(self, cell):
        measurement_type = cell.get_text().strip()
        if measurement_type not in self._measurement_types:
            err = '%s does not match one of the following measurement types: \n %s' % (measurement_type, ' ,'.join((map(str, self._measurement_types))))
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.HEADER_MEASUREMENT_TYPE_VALUE, err)
            self._validation_errors.append(message)
            return []
        return measurement_type
    
    def _process_ods(self, cell):
        return [float(value) for value in cell_parser.PARSER.process_numbers(cell.get_text())]
    
    def _process_replicate(self, cell):
        text = cell.get_text()
        if not cell_parser.PARSER.is_number(text):
            err = '%s must be a numerical value' % text
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.HEADER_REPLICATE_VALUE, err.get_message())
            self._validation_errors.append(message)
            return None
        
        list_of_replicates = cell_parser.PARSER.process_numbers(text)
        if len(list_of_replicates) > 1:
            message = ('Measurement table for %s has more than one replicate provided.'
                       'Only the first replicate will be used from %s.') % (intent_parser_constants.HEADER_REPLICATE_VALUE, text)
            self._logger.warning(message)
        return int(list_of_replicates[0])
        
    def _process_strains(self, cell):
        if cell_parser.PARSER.is_valued_cell(cell.get_text()):
            message = ('Measurement table has invalid %s value: %s' 
                       'Identified %s as a numerical value when '
                       'expecting alpha-numeric values.') % (intent_parser_constants.HEADER_STRAINS_VALUE, cell.get_text())
            self._validation_errors.append(message)
            return []
        return cell_parser.PARSER.process_names(cell.get_text())
    
    def _process_temperature(self, cell):
        text = cell.get_text()
        try:
            result = []
            for value_unit in cell_parser.PARSER.process_values_unit(text, units=self._temperature_units,
                                                                     unit_type='temperature'):
                temperature = {'value': float(value_unit['value']),
                               'unit': value_unit['unit']}
                result.append(temperature)
            return result
        except TableException as err:
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.HEADER_TEMPERATURE_VALUE, err.get_message())
            self._validation_errors.append(message)
            return []
            
    def _process_timepoints(self, cell):
        text = cell.get_text()
        try:
            result = []
            for value_unit in cell_parser.PARSER.process_values_unit(text, units=self._timepoint_units, unit_type='timepoints'):
                timepoint = {'value': float(value_unit['value']),
                             'unit': value_unit['unit']}
                result.append(timepoint)
            return result
        except TableException as err:
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.HEADER_TIMEPOINT_VALUE, err.get_message())
            self._validation_errors.append(message)
            return []
