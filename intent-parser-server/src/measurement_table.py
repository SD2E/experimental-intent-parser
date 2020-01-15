import constants
import intent_parser_utils
import logging
import table_utils

'''
Class handles measurement from Experimental Request tables in Google Docs.
'''
class MeasurementTable:
    
    _logger = logging.getLogger('intent_parser_server')
    IGNORE_COLUMNS = [constants.COL_HEADER_SAMPLES, constants.COL_HEADER_NOTES]
  
    def __init__(self, temperature_units={}, timepoint_units={}, fluid_units={}, measurement_types={}, file_type={}):
        self._temperature_units = temperature_units
        self._timepoint_units = timepoint_units
        self._fluid_units = fluid_units
        self._measurement_types = measurement_types
        self._file_type = file_type
         
    def parse_table(self, table):
        measurements = []
        rows = table['tableRows']
        for row in rows[1:]:
            measurements.append(self._parse_row(rows[0], row))
        return measurements   
            
    def _parse_row(self, header_row, row):
        measurement = {}
        content = []
        num_cols = len(row['tableCells'])
        for i in range(0, num_cols): 
            paragraph_element = header_row['tableCells'][i]['content'][0]['paragraph']
            header = table_utils.get_paragraph_text(paragraph_element).strip()
            cellTxt = ' '.join([table_utils.get_paragraph_text(content['paragraph']).strip() for content in row['tableCells'][i]['content']])
            if not cellTxt or header in self.IGNORE_COLUMNS:
                continue
            elif header == constants.COL_HEADER_MEASUREMENT_TYPE:
                measurement['measurement_type'] = self._get_measurement_type(cellTxt)
            elif header == constants.COL_HEADER_FILE_TYPE:
                measurement['file_type'] = [value for value in table_utils.extract_name_value(cellTxt)] 
            elif header == constants.COL_HEADER_REPLICATE:
                if table_utils.is_number(cellTxt):
                    measurement['replicates'] = int(cellTxt)
                else:
                    measurement['replicates'] = -1
                    self._logger.info('WARNING: failed to parse number of replicates! Trying to parse: %s' % cellTxt)
            elif header == constants.COL_HEADER_STRAIN:
                measurement['strains'] = [value for value in table_utils.extract_name_value(cellTxt)]
            elif header == constants.COL_HEADER_ODS:
                measurement['ods'] = [float(value) for value in table_utils.extract_number_value(cellTxt)]
            elif header == constants.COL_HEADER_TEMPERATURE:
                temps = []
                for value,unit in table_utils.transform_cell(cellTxt, self._temperature_units, cell_type='temperature'):
                    try:
                        temp_dict = {'value' : float(value), 'unit' : unit}
                    except:
                        temp_dict = {'value' : -1, 'unit' : 'unspecified'}
                        self._logger.info('WARNING: failed to parse temp unit! Trying to parse: %s' % cellTxt)
                    temps.append(temp_dict)
                measurement['temperatures'] = temps
            elif header == constants.COL_HEADER_TIMEPOINT:
                timepoints = []
                for value,unit in table_utils.transform_cell(cellTxt, self._timepoint_units):
                    try:
                        time_dict = {'value' : float(value), 'unit' : unit}
                    except:
                        time_dict = {'value' : -1, 'unit' : 'unspecified'}
                        self._logger.info('WARNING: failed to parse time unit! Trying to parse: %s' % cellTxt)
                    timepoints.append(time_dict)
                measurement['timepoints'] = timepoints
            else:
                reagents = self._parse_reagent_media(paragraph_element, cellTxt)
                content.append(reagents)
        if content:
            measurement['contents'] = content
        return measurement 
    
    
    
    def _parse_reagent_media(self, paragraph_element, cellTxt):
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
            for value,unit in table_utils.transform_cell(timepoint_str[1], self._timepoint_units):
                timepoint_dict = {'value' : float(value), 'unit' : unit}
        
        label_uri_dict = {'label' : reagent_media_name, 'sbh_uri' : uri}    
        
        # Determine if cells is reagent or media. 
        if table_utils.is_name(cellTxt):
            value = ' '.join(table_utils.extract_name_value(cellTxt))
            named_dict = {'name' : label_uri_dict, 'value' : value}
            reagents_media.append(named_dict)
        else:                   
            for value,unit in table_utils.transform_cell(cellTxt, self._fluid_units, cell_type='fluid'):
                try:
                    if timepoint_dict:
                        numerical_dict = {'name' : label_uri_dict, 'value' : value, 'unit' : unit, 'timepoint' : timepoint_dict}
                    else:
                        numerical_dict = {'name' : label_uri_dict, 'value' : value, 'unit' : unit}
                                    
                    reagents_media.append(numerical_dict)
                except:
                    self._logger.info('WARNING: failed to parse reagent! Trying to parse: %s' % cellTxt)
        
        return reagents_media
    
    
    def _get_measurement_type(self, text):
        """
        Find the closest matching measurement type to the given type, and return that as a string
        """
        # measurement types have underscores, so replace spaces with underscores to make the inputs match better
        text = text.replace(' ', '_')
        best_match_type = ''
        best_match_size = 0
        for mtype in self._measurement_types:
            matches = intent_parser_utils.find_common_substrings(text.lower(), mtype.lower(), 1, 0)
            for m in matches:
                if m.size > best_match_size:
                    best_match_type = mtype
                    best_match_size = m.size
        return best_match_type
     