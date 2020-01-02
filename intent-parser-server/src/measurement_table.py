import table_utils


'''
Class handles measurement from Experimental Request tables in Google Docs.
'''
from table_utils import _temperature_units
class MeasurementTable:
    
    # String defines for headers in the new-style measurements table
    COL_HEADER_MEASUREMENT_TYPE = 'measurement-type'
    COL_HEADER_FILE_TYPE = 'file-type'
    COL_HEADER_REPLICATE = 'replicate'
    COL_HEADER_STRAIN = 'strains'
    COL_HEADER_SAMPLES = 'samples'
    COL_HEADER_ODS = 'ods'
    COL_HEADER_NOTES = 'notes'
    COL_HEADER_TEMPERATURE = 'temperature'
    COL_HEADER_TIMEPOINT = 'timepoint'
    IGNORE_COLUMNS = [COL_HEADER_SAMPLES, COL_HEADER_NOTES]
  
    def __init__(self, temperature_units={}, timepoint_units={}, fluid_units={}):
        self._temperature_units = temperature_units
        self._timepoint_units = timepoint_units
        self._fluid_units = fluid_units
        
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
            header = self.get_paragraph_text(header_row['tableCells'][i]['content'][0]['paragraph']).strip()
            cellTxt = ' '.join([self.get_paragraph_text(content['paragraph']).strip() for content in row['tableCells'][i]['content']])
            if not cellTxt or header in self.IGNORE_COLUMNS:
                continue
            elif header == self.COL_HEADER_MEASUREMENT_TYPE:
                # TODO: 
                measurement['measurement_type'] = self.get_measurement_type(cellTxt)
            elif header == self.COL_HEADER_FILE_TYPE:
                measurement['file_type'] = [value for value in table_utils.extract_name_value(cellTxt)] 
            elif header == self.COL_HEADER_REPLICATE:
                if table_utils.is_number(cellTxt):
                    measurement['replicates'] = int(cellTxt)
                else:
                    measurement['replicates'] = -1
                    self.logger.info('WARNING: failed to parse number of replicates! Trying to parse: %s' % cellTxt)
            elif header == self.COL_HEADER_STRAIN:
                measurement['strains'] = [value for value in table_utils.extract_name_value(cellTxt)]
            elif header == self.COL_HEADER_ODS:
                measurement['ods'] = [float(value) for value in table_utils.extract_number_value(cellTxt)
            elif header == self.COL_HEADER_TEMPERATURE:
                temps = []
                for value,unit in table_utils.transform_cell(cellTxt, self._temperature_units, cell_type='temperature'):
                    try:
                        temp_dict = {'value' : float(value), 'unit' : unit}
                    except:
                        temp_dict = {'value' : -1, 'unit' : 'unspecified'}
                        self.logger.info('WARNING: failed to parse temp unit! Trying to parse: %s' % cellTxt)
                    temps.append(temp_dict)
                measurement['temperatures'] = temps
            elif header == self.COL_HEADER_TIMEPOINT:
                timepoints = []
                for value,unit in table_utils.transform_cell(cellTxt, self._timepoint_units):
                    try:
                        time_dict = {'value' : float(value), 'unit' : unit}
                    except:
                        time_dict = {'value' : -1, 'unit' : 'unspecified'}
                        self.logger.info('WARNING: failed to parse time unit! Trying to parse: %s' % cellTxt)
                    timepoints.append(time_dict)
                measurement['timepoints'] = timepoint
            else:
                reagents = self._parse_reagent(header, cellTxt)
                content.append(reagents)
        if content:
            measurement['contents'] = content
        return measurement 
        
    def _parse_reagent(self, reagent_name, cellTxt):
        reagents = []
      
        timepoint_str = reagent_name.split('@')
        # Check header if it contains time sequence
        if len(timepoint_str) > 1:
            reagent_name = timepoint_str[0].strip()
            defaultUnit = 'unspecified'
            spec, unit = self.detect_and_remove_time_unit(timepoint_str[1]);
            if unit is not None and unit is not 'unspecified':
                defaultUnit = unit
            reagent_timepoint_dict = {'value' : float(spec), 'unit' : defaultUnit}
                        
        # Retrieve SBH URI
        uri = 'NO PROGRAM DICTIONARY ENTRY'
        if len(paragraph_element['elements']) > 0 and 'link' in paragraph_element['elements'][0]['textRun']['textStyle']:
            uri = paragraph_element['elements'][0]['textRun']['textStyle']['link']['url']
                        
        # Determine if cells is reagent or media
        for value,unit in table_utils.transform_cell(cellTxt, self._fluid_units, cell_type='fluid'):
            try:
                if reagent_timepoint_dict:
                    reagent_dict = {'name' : {'label' : reagent_name, 'sbh_uri' : uri}, 'value' : value, 'unit' : unit, 'timepoint' : reagent_timepoint_dict}
                else:
                    reagent_dict = {'name' : {'label' : reagent_name, 'sbh_uri' : uri}, 'value' : value, 'unit' : unit}
                                    
            except:
                self.logger.info('WARNING: failed to parse reagent! Trying to parse: %s' % cellTxt)
            reagents.append(reagent_dict)
        
        return reagents 