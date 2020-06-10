from intent_parser.intent_parser_exceptions import TableException
import intent_parser.table.cell_parser as cell_parser
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.table.table_utils as table_utils
import logging

class MeasurementTable(object):
    """
    Process information from Intent Parser's Measurement Table
    """
    _logger = logging.getLogger('intent_parser')
    IGNORE_COLUMNS = ['SAMPLES', 'NOTES']
    
    def __init__(self, intent_parser_table, temperature_units={}, timepoint_units={}, fluid_units={}, measurement_types={}, file_type={}):
        self._temperature_units = temperature_units
        self._timepoint_units = timepoint_units
        self._fluid_units = fluid_units
        self._measurement_types = measurement_types
        self._file_type = file_type
        self._validation_errors = []
        self._validation_warnings = []
        self._intent_parser_table = intent_parser_table 
        self._table_caption = ''
    
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
        for table_caption,control_data in control_tables.items():
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
            cell_type = cell_parser.PARSER.get_header_type(header_cell)
            
            if not cell.get_text() or cell_type in self.IGNORE_COLUMNS:
                continue
            
            elif 'MEASUREMENT_TYPE' == cell_type:
                measurement_type = self._process_measurement_type(cell)
                if measurement_type:
                    measurement['measurement_type'] = measurement_type
            elif 'FILE_TYPE' == cell_type:
                file_type = self._process_file_type(cell) 
                if file_type:
                    measurement['file_type'] = file_type  
            elif 'REPLICATE' == cell_type:
                replicates = self._process_replicate(cell)
                if replicates:
                    measurement['replicates'] = replicates
            elif 'STRAINS' == cell_type:
                strains = self._process_strains(cell)
                if strains:
                    measurement['strains'] = strains
            elif 'ODS' == cell_type:
                ods = self._process_ods(cell)
                if ods:
                    measurement['ods'] =ods
            elif 'TEMPERATURE' == cell_type:
                temperatures = self._process_temperature(cell)
                if temperatures:
                    measurement['temperatures'] = temperatures
            elif 'TIMEPOINT'  == cell_type:
                timepoints = self._process_timepoints(cell)
                if timepoints:
                    measurement['timepoints'] = timepoints
            elif 'BATCH' == cell_type:
                batch = self._process_batch(cell)
                if batch:
                    measurement['batch'] = batch
            elif 'CONTROL' == cell_type:
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
    
    def _process_reagent_header(self, cell):
        text_with_urls = cell.get_text_with_url()
        name, value, unit = table_utils.parse_reagent_header(cell.get_text(), self._timepoint_units, unit_type='timepoints')
        
        uri = 'NO PROGRAM DICTIONARY ENTRY'
        if name in text_with_urls and text_with_urls[name] is not None:
            uri = text_with_urls[name]
            
        name_dict = {'label' : name, 'sbh_uri' : uri}
        timepoint_dict = {}
        if value and unit:
            timepoint_dict['value'] = float(value)
            timepoint_dict['unit'] = unit  
        return name_dict, timepoint_dict  
         
    def _process_reagent_media(self, cell, header_cell):
        reagents_media = []
        text = cell.get_text()
        name_dict, timepoint_dict = cell_parser.PARSER.process_reagent_header(header_cell, self._timepoint_units, unit_type='timepoints')
        # Determine if cells is numerical or name value 
        if table_utils.is_valued_cells(text):                   
            try:
                for value,unit in table_utils.transform_cell(text, self._fluid_units, cell_type='fluid'):
                    if timepoint_dict:
                        numerical_dict = {'name' : name_dict, 'value' : value, 'unit' : unit, 'timepoint' : timepoint_dict}
                    else:
                        numerical_dict = {'name' : name_dict, 'value' : value, 'unit' : unit}
                    reagents_media.append(numerical_dict)
            except TableException as err:
                message = err.get_message()
                self._validation_errors.append(message)
        elif table_utils.is_number(text):
            err = '%s is missing a unit' % text
            message = 'Measurement table has invalid reagent/media value: %s' % err
            self._validation_errors.append(message)
            return []
        else:
            for name in table_utils.extract_name_value(text):
                if timepoint_dict:
                    named_dict = {'name' : name_dict, 'value' : name, 'timepoint' : timepoint_dict}
                else:
                    named_dict = {'name' : name_dict, 'value' : name}
                reagents_media.append(named_dict)
        return reagents_media

    def get_validation_errors(self):
        return self._validation_errors

    def get_validation_warnings(self):
        return self._validation_warnings
    
    def _process_batch(self, cell):
        text = cell.get_text()
        if table_utils.is_name(text):
            err = '%s must contain a list of integer values.' % text
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_BATCH, err)
            self._validation_errors.append(message)
            return []
        return [int(value) for value in table_utils.extract_number_value(text)] 
    
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
        for table_caption in table_utils.extract_name_value(cell.get_text()):
            canonicalize_caption = ''.join(table_caption.lower().split())
            if canonicalize_caption in control_tables:
                for control in control_tables[canonicalize_caption]:
                    controls.append(control)
        return controls       
           
    def _process_file_type(self, cell):
        file_type = cell.get_text()
        return [value for value in table_utils.extract_name_value(file_type)] 
    
    def _process_measurement_type(self, cell):
        measurement_type = cell.get_text().strip()
        if measurement_type not in self._measurement_types:
            err = '%s does not match one of the following measurement types: \n %s' % (measurement_type, ' ,'.join((map(str, self._measurement_types))))
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_MEASUREMENT_TYPE, err)
            self._validation_errors.append(message)
            return []
        return measurement_type
    
    def _process_ods(self, cell):
        text = cell.get_text()
        return [float(value) for value in table_utils.extract_number_value(text)]
    
    def _process_replicate(self, cell):
        text = cell.get_text()
        if not table_utils.is_number(text):
            err = '%s must be a numerical value' % text
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_REPLICATE, err.get_message())
            self._validation_errors.append(message)
            return None
        
        list_of_replicates = table_utils.extract_number_value(text)
        if len(list_of_replicates) > 1:
            message = ('Measurement table for %s has more than one replicate provided.'
                       'Only the first replicate will be used from %s.') % (intent_parser_constants.COL_HEADER_REPLICATE, text)
            self._logger.warning(message)
        return int(list_of_replicates[0])
        
    def _process_strains(self, cell):
        if cell_parser.PARSER.is_valued_cell(cell):
            message = ('Measurement table has invalid %s value: %s' 
                       'Identified %s as a numerical value when '
                       'expecting alpha-numeric values.') % (intent_parser_constants.COL_HEADER_STRAIN, cell.get_text())
            self._validation_errors.append(message)
            return []
        return cell_parser.PARSER.process_names(cell, check_name_in_url=True)
    
    def _process_temperature(self, cell):
        text = cell.get_text()
        try:
            return table_utils.parse_and_append_value_unit(text, 'temperature', self._temperature_units)
        except TableException as err:
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_TEMPERATURE, err.get_message())
            self._validation_errors.append(message)
            return []
            
    def _process_timepoints(self, cell):
        text = cell.get_text()
        try:
            return table_utils.parse_and_append_value_unit(text, 'timepoints', self._timepoint_units) 
        except TableException as err:
            message = 'Measurement table has invalid %s value: %s' % (intent_parser_constants.COL_HEADER_TIMEPOINT, err.get_message())
            self._validation_errors.append(message)
            return []
    