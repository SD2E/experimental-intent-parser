'''
Class handles measurement from Experimental Request tables in Google Docs.
'''
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
    
  
    def parse_table(self, table):
        measurements = []
        rows = table['tableRows']
        for row in rows[1:]:
            measurements.append(self.parse_row(rows[0], row))
        return measurements   
            
    def parse_row(self, header_row, row):
        measurement = {}
        content = []
        num_cols = len(row['tableCells'])
        for i in range(0, num_cols): 
            paragraph_element = header_row['tableCells'][i]['content'][0]['paragraph']
            header = self.get_paragraph_text(header_row['tableCells'][i]['content'][0]['paragraph']).strip()
            cellTxt = ' '.join([self.get_paragraph_text(content['paragraph']).strip() for content in row['tableCells'][i]['content']])
            if not cellTxt:
                continue
            if header == self.COL_HEADER_MEASUREMENT_TYPE:
                measurement['measurement_type'] = self.get_measurement_type(cellTxt)
            elif header == self.COL_HEADER_FILE_TYPE:
                measurement['file_type'] = [s.strip() for s in cellTxt.split(sep=',')]
            elif header == self.COL_HEADER_REPLICATE:
                try:
                    measurement['replicates'] = int(cellTxt)
                except:
                    measurement['replicates'] = -1
                    self.logger.info('WARNING: failed to parse number of replicates! Trying to parse: %s' % cellTxt)
            elif header == self.COL_HEADER_SAMPLES:
                    pass
            elif header == self.COL_HEADER_STRAIN:
                measurement['strains'] = [s.strip() for s in cellTxt.split(sep=',')]
            elif header == self.COL_HEADER_ODS:
                ods_strings = []
                for s in cellTxt.split(sep=','):
                    ods_strings.append(float(s.strip()))
                measurement['ods'] = ods_strings
            elif header == self.COL_HEADER_TEMPERATURE:
                temps = []
                temp_strings = [s.strip() for s in cellTxt.split(sep=',')]
                # First, determine default unit
                defaultUnit = 'unspecified'
                for temp_str in temp_strings:
                    spec, unit = self.detect_and_remove_temp_unit(temp_str);
                    if unit is not None and unit is not 'unspecified':
                        defaultUnit = unit

                for temp_str in temp_strings:
                    spec, unit = self.detect_and_remove_temp_unit(temp_str);
                    if unit is None or unit == 'unspecified':
                        unit = defaultUnit
                    try:
                        temp_dict = {'value' : float(spec), 'unit' : unit}
                    except:
                        temp_dict = {'value' : -1, 'unit' : 'unspecified'}
                        self.logger.info('WARNING: failed to parse temp unit! Trying to parse: %s' % spec)
                    temps.append(temp_dict)
                measurement['temperatures'] = temps
            elif header == self.COL_HEADER_TIMEPOINT:
                timepoints = []
                timepoint_strings = [s.strip() for s in cellTxt.split(sep=',')]
                # First, determine default unit
                defaultUnit = 'unspecified'
                for time_str in timepoint_strings:
                    spec, unit = self.detect_and_remove_time_unit(time_str);
                    if unit is not None and unit is not 'unspecified':
                        defaultUnit = unit

                for time_str in timepoint_strings:
                    spec, unit = self.detect_and_remove_time_unit(time_str);
                    if unit is None or unit == 'unspecified':
                        unit = defaultUnit
                    try:
                        time_dict = {'value' : float(spec), 'unit' : unit}
                    except:
                        time_dict = {'value' : -1, 'unit' : 'unspecified'}
                        self.logger.info('WARNING: failed to parse time unit! Trying to parse: %s' % spec)
                    timepoints.append(time_dict)
                measurement['timepoints'] = timepoints
            else:
                reagents = []
                reagent_timepoint_dict = {}
                reagent_header = header
                reagent_name = header
                timepoint_str = reagent_header.split('@')
                if len(timepoint_str) > 1:
                    reagent_name = timepoint_str[0].strip()
                    timepoint_data = timepoint_str[1].split()
                    if len(timepoint_data) > 1:
                        time_val = float(timepoint_data[0].strip())
                        time_unit = timepoint_data[1].strip()
                        reagent_timepoint_dict = {'value' : time_val, 'unit' : time_unit}
                uri = 'NO PROGRAM DICTIONARY ENTRY'
                if len(paragraph_element['elements']) > 0 and 'link' in paragraph_element['elements'][0]['textRun']['textStyle']:
                    uri = paragraph_element['elements'][0]['textRun']['textStyle']['link']['url']
                reagent_strings = [s.strip() for s in cellTxt.split(sep=',')]
                    
                defaultUnit = 'unspecified'
                for value in reagent_strings:
                    spec, unit = self.detect_and_remove_fluid_unit(value);
                    if unit is not None and unit is not 'unspecified':
                        defaultUnit = unit
                for value in reagent_strings:
                    spec, unit = self.detect_and_remove_fluid_unit(value);
                    if unit is None or unit == 'unspecified':
                        unit = defaultUnit
                    try:
                        if reagent_timepoint_dict:
                            reagent_dict = {'name' : {'label' : reagent_name, 'sbh_uri' : uri}, 'value' : spec, 'unit' : unit, 'timepoint' : reagent_timepoint_dict}
                        else:
                            reagent_dict = {'name' : {'label' : reagent_name, 'sbh_uri' : uri}, 'value' : spec, 'unit' : unit}
                                
                    except:
                        self.logger.info('WARNING: failed to parse reagent! Trying to parse: %s' % spec)
                    reagents.append(reagent_dict)
                content.append(reagents)
        if content:
            measurement['contents'] = content
        return measurement 
        
    