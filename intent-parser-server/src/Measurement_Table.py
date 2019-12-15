'''
Class for parsing information from a measurement table within an experimental request document.
'''
class Measurement_Table:
    
    table_dict = None
    
    # String defines for headers in the new-style measurements table
    col_header_measurement_type = 'measurement-type'
    col_header_file_type = 'file-type'
    col_header_replicate = 'replicate'
    col_header_strain = 'strains'
    col_header_samples = 'samples'
    col_header_ods = 'ods'
    col_header_notes = 'notes'
    col_header_temperature = 'temperature'
    col_header_timepoint = 'timepoint'
    
     
    def __init__(self, table):
        table_dict = table
    
            
    def get_measurement_data(self):
        measurements = []

        rows = self.table_dict['tableRows']
        headerRow = rows[0]
        numCols = len(headerRow['tableCells'])
        for row in rows[1:]:
            cells = row['tableCells']
            content = []
            
            # Parse rest of table
            measurement = {}
            for i in range(0, numCols): 
                paragraph_element = headerRow['tableCells'][i]['content'][0]['paragraph']
                header = self.get_paragraph_text(headerRow['tableCells'][i]['content'][0]['paragraph']).strip()
                cellTxt = ' '.join([self.get_paragraph_text(content['paragraph']).strip() for content in cells[i]['content']])
                if not cellTxt:
                    continue
                if header == self.col_header_measurement_type:
                    measurement['measurement_type'] = self.get_measurement_type(cellTxt)
                elif header == self.col_header_file_type:
                    measurement['file_type'] = [s.strip() for s in cellTxt.split(sep=',')]
                elif header == self.col_header_replicate:
                    try:
                        measurement['replicates'] = int(cellTxt)
                    except:
                        measurement['replicates'] = -1
                        self.logger.info('WARNING: failed to parse number of replicates! Trying to parse: %s' % cellTxt)
                elif header == self.col_header_samples:
                    #measurement['samples'] = cellTxt
                    #samples isn't part of the schema and is just there for auditing purposes
                    pass
                elif header == self.col_header_strain:
                    measurement['strains'] = [s.strip() for s in cellTxt.split(sep=',')]
                elif header == self.col_header_ods:
                    #ods_strings = [float(s.strip()) for s in cellTxt.split(sep=',')]
                    ods_strings = []
                    for s in cellTxt.split(sep=','):
                        ods_strings.append(float(s.strip()))
                    measurement['ods'] = ods_strings
                elif header == self.col_header_temperature:
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
                elif header == self.col_header_timepoint:
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
                        reagent_amount = float(spec)
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
            measurements.append(measurement)
        return measurements
    
    
    
    
    