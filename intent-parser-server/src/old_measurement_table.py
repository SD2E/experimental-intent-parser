import intent_parser_utils

class OldMeasurementTable(object):
    '''
    Class to parse old Measurement Table.
    '''

    def __init__(self):
        pass
    
    def parse_table(self, table): 
        measurements = []
        rows = table['tableRows']
        
        # Each non-header row represents a measurement in the run
        for row in rows[1:]:
            cells = row['tableCells']
            measurement_type = self._get_measurement_type(self.get_paragraph_text(cells[0]['content'][0]['paragraph']))
            
            # Ignore the rest of the cells for now
            measurement = {'measurement_type' : measurement_type}
            measurements.append(measurement)
        
        return measurements
    
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
     