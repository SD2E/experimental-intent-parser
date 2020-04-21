from intent_parser_exceptions import TableException
import constants
import intent_parser_utils
import logging
import table_utils


class MeasurementTable:
    '''
    Class handles measurement from Experimental Request tables in Google Docs.
    '''    
    _logger = logging.getLogger('intent_parser_server')
    IGNORE_COLUMNS = [constants.COL_HEADER_SAMPLES, constants.COL_HEADER_NOTES]
  
    def __init__(self, temperature_units={}, timepoint_units={}, fluid_units={}, measurement_types={}, file_type={}):
        self._temperature_units = temperature_units
        self._timepoint_units = timepoint_units
        self._fluid_units = fluid_units
        self._measurement_types = measurement_types
        self._file_type = file_type
        self._validation_errors = []
        
    def parse_table(self, table):
        measurements = []
        rows = table['tableRows']
        for row in rows[1:]:
            meas_data = self._parse_row(rows[0], row)
            if meas_data:
                measurements.append(meas_data)
        return measurements   
            
    def _parse_row(self, header_row, row):
        measurement = {}
        content = []
        num_cols = len(row['tableCells'])
        for i in range(0, num_cols): 
            paragraph_element = header_row['tableCells'][i]['content'][0]['paragraph']
            header = table_utils.get_paragraph_text(paragraph_element).strip()
            cell_txt = ' '.join([table_utils.get_paragraph_text(content['paragraph']).strip() for content in row['tableCells'][i]['content']])
            if not cell_txt or header in self.IGNORE_COLUMNS:
                continue
            elif header == constants.COL_HEADER_MEASUREMENT_TYPE:
                try:  
                    measurement['measurement_type'] = self._get_measurement_type(cell_txt.strip())
                except TableException as err:
                    message = ' '.join(['Under measurement_type: ', err.get_expression(), err.get_message()]) 
                    self._logger.info('WARNING ' + message)
                    self._validation_errors.append(message)
            elif header == constants.COL_HEADER_FILE_TYPE:
                measurement['file_type'] = [value for value in table_utils.extract_name_value(cell_txt)] 
            elif header == constants.COL_HEADER_REPLICATE:
                try:
                    if not table_utils.is_number(cell_txt):
                        raise TableException(cell_txt, 'is not a numerical value')
                    measurement['replicates'] = int(cell_txt)
                except TableException as err:
                    message =  ' '.join(['Under replicate: ', err.get_expression(), err.get_message(), 'for', cell_txt]) 
                    self._logger.info('WARNING ' + message)
                    self._validation_errors.append(message)
            elif header == constants.COL_HEADER_STRAIN:
                measurement['strains'] = [value for value in table_utils.extract_name_value(cell_txt)]
            elif header == constants.COL_HEADER_ODS:
                measurement['ods'] = [float(value) for value in table_utils.extract_number_value(cell_txt)]
            elif header == constants.COL_HEADER_TEMPERATURE:
                try:
                    measurement['temperatures'] = self._parse_and_append_value_unit(cell_txt, 'temperature', self._temperature_units)
                except TableException as err:
                    message = ' '.join(['Under temperature: ', err.get_expression(), err.get_message(), 'for', cell_txt]) 
                    self._logger.info('WARNING ' + message)
                    self._validation_errors.append(message)
            elif header == constants.COL_HEADER_TIMEPOINT:
                try:
                    measurement['timepoints'] = self._parse_and_append_value_unit(cell_txt, 'timepoints', self._timepoint_units) 
                except TableException as err:
                    message = ' '.join(['Under timepoint: ', err.get_expression(), err.get_message(), 'for', cell_txt]) 
                    self._logger.info('WARNING ' + message)
                    self._validation_errors.append(message)
            else:
                try:
                    reagents = self._parse_reagent_media(paragraph_element, cell_txt)
                    if not reagents:
                        raise TableException(header, 'cannot parse as a reagent/media')
                    content.append(reagents)
                except TableException as err:
                    message = ' '.join(['Under', header, ':', err.get_expression(), err.get_message()]) 
                    self._logger.info('Warning ' + message)
                    self._validation_errors.append(message)
            
        if content:
            measurement['contents'] = content
        return measurement 
    
    def _parse_and_append_value_unit(self, cell_txt, cell_type, unit_list):
        result = []
        for value,unit in table_utils.transform_cell(cell_txt, unit_list, cell_type=cell_type):
            temp_dict = {'value' : float(value), 'unit' : unit}
            result.append(temp_dict)
        return result 
        
    
    def _parse_reagent_media(self, paragraph_element, cell_txt):
        reagents_media = []
        reagent_media_name = table_utils.get_paragraph_text(paragraph_element).strip()
       
        # Retrieve SBH URI
        uri = 'NO PROGRAM DICTIONARY ENTRY'
        if len(paragraph_element['elements']) > 0 and 'link' in paragraph_element['elements'][0]['textRun']['textStyle']:
            uri = paragraph_element['elements'][0]['textRun']['textStyle']['link']['url']
             
        # Check header if it contains time sequence
        timepoint_str = reagent_media_name.split('@')
        timepoint_dict = {}
        if len(timepoint_str) > 1:
            reagent_media_name = timepoint_str[0].strip()
            for value,unit in table_utils.transform_cell(timepoint_str[1], self._timepoint_units, cell_type='timepoints'):
                timepoint_dict = {'value' : float(value), 'unit' : unit}
        
        label_uri_dict = {'label' : reagent_media_name, 'sbh_uri' : uri}    
        
        # Determine if cells is numerical or name value 
        if table_utils.is_valued_cells(cell_txt):                   
            try:
                for value,unit in table_utils.transform_cell(cell_txt, self._fluid_units, cell_type='fluid'):
                    if timepoint_dict:
                        numerical_dict = {'name' : label_uri_dict, 'value' : value, 'unit' : unit, 'timepoint' : timepoint_dict}
                    else:
                        numerical_dict = {'name' : label_uri_dict, 'value' : value, 'unit' : unit}
                    reagents_media.append(numerical_dict)
            except TableException as err:
                message = ' '.join([err.get_expression(), err.get_message(), 'for', cell_txt]) 
                self._logger.info('Warning ' + message)
                self._validation_errors.append(message)
        elif table_utils.is_number(cell_txt):
            raise TableException(cell_txt, 'is missing a unit')
        else:
            for name in table_utils.extract_name_value(cell_txt):
                if timepoint_dict::
                    named_dict = {'name' : label_uri_dict, 'value' : name, 'timepoint' : timepoint_dict}
                else:
                    named_dict = {'name' : label_uri_dict, 'value' : name}
                reagents_media.append(named_dict)
        
        return reagents_media
    
    
    def _get_measurement_type(self, text):
        result = None 
        for mtype in self._measurement_types:
            if mtype == text:
                result = mtype
                break
        
        if result is None:
            raise TableException(text, 'does not match one of the following measurement types: \n' + '\n'.join((map(str, self._measurement_types))))
        return result 
    
    def get_validation_errors(self):
        return self._validation_errors
    