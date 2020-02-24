from intent_parser_exceptions import TableException
from parameter_table import ParameterTable
import unittest


class ParameterTableTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.parameter_fields = {
            'Inoculation volume' : 'inoc_info.inoc_vol',
            'Inoculation media volume' : 'inoc_info.inoc_media_vol',
            'Inoculation media' : 'inoc_info.inoculation_media',
            'Inoculation increment time 1' : 'inoc_info.inc_time_1',
            'Sample has sbh_uri as an aliquot property' : 'validate_samples',
            'Plate reader gain' : 'plate_reader_info.gain'
            }

    def test_parameter_field_with_empty_value(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Parameter\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Inoculation volume\n'}}]}}]}]}]
        } 
        
        param_table = ParameterTable(parameter_fields=self.parameter_fields)
        param_result = param_table.parse_table(input_table)
        self.assertEquals(0, len(param_result))
       
    def test_parameter_string_value_with_colon_separator(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Parameter\n' }}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Value\n' }}]}}]}
            ]},
            
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Inoculation volume\n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '5 microliter\n'}}]}}]}
            ]}
        ]} 
        
        param_table = ParameterTable(parameter_fields=self.parameter_fields)
        param_result = param_table.parse_table(input_table)
        self.assertEquals(1, len(param_result))
        self.assertEquals('5:microliter', param_result['inoc_info.inoc_vol'])
        
    def test_one_parameter_string_value_without_colon_separator(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Parameter\n' }}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Value\n' }}]}}]}
            ]},
            
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Inoculation media\n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'sc_media\n'}}]}}]}
            ]}
        ]} 
        
        param_table = ParameterTable(parameter_fields=self.parameter_fields)
        param_result = param_table.parse_table(input_table)
        self.assertEquals(1, len(param_result))
        self.assertEquals('sc_media', param_result['inoc_info.inoculation_media'])
    
    def test_two_parameter_string_value_without_colon_separator(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Parameter\n' }}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Value\n' }}]}}]}
            ]},
            
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Inoculation media\n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'S750, Modified M9 Media\n'}}]}}]}
            ]}
        ]} 
        
        param_table = ParameterTable(parameter_fields=self.parameter_fields)
        param_result = param_table.parse_table(input_table)
        expected_result = {'inoc_info.inoculation_media.0': 'S750', 
                           'inoc_info.inoculation_media.1' : 'Modified M9 Media'}
        self.assertEquals(2, len(param_result))
        self.assertDictEqual(expected_result, param_result)
        
    def test_parameter_boolean_value(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Parameter\n' }}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Value\n' }}]}}]}
            ]},
            
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Sample has sbh_uri as an aliquot property\n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'false\n'}}]}}]}
            ]}
        ]} 
        
        param_table = ParameterTable(parameter_fields=self.parameter_fields)
        param_result = param_table.parse_table(input_table)
        self.assertEquals(1, len(param_result))
        self.assertEquals(False, param_result['validate_samples'])
    
    def test_parameter_with_case_insensitive_boolean_value(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Parameter\n' }}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Value\n' }}]}}]}
            ]},
            
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Sample has sbh_uri as an aliquot property\n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'FaLse\n'}}]}}]}
            ]}
        ]} 
        
        param_table = ParameterTable(parameter_fields=self.parameter_fields)
        param_result = param_table.parse_table(input_table)
        self.assertEquals(1, len(param_result))
        self.assertEquals(False, param_result['validate_samples'])
    
    def test_parameter_with_non_boolean_value(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Parameter\n' }}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Value\n' }}]}}]}
            ]},
            
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Sample has sbh_uri as an aliquot property\n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'neither\n'}}]}}]}
            ]}
        ]} 
        
        param_table = ParameterTable(parameter_fields=self.parameter_fields)
        param_result = param_table.parse_table(input_table)
        self.assertEquals(0, len(param_result))
       
    def test_parameter_with_one_float_value(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Parameter\n' }}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Value\n' }}]}}]}
            ]},
            
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Plate reader gain\n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '0.1\n'}}]}}]}
            ]}
        ]} 
        
        param_table = ParameterTable(parameter_fields=self.parameter_fields)
        param_result = param_table.parse_table(input_table)
        self.assertEquals(1, len(param_result))
        self.assertEquals(0.1, param_result['plate_reader_info.gain'])
    
    def test_parameter_with_three_float_values(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Parameter\n' }}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Value\n' }}]}}]}
            ]},
            
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Plate reader gain\n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '0.1, 0.2, 0.3\n'}}]}}]}
            ]}
        ]} 
        
        param_table = ParameterTable(parameter_fields=self.parameter_fields)
        param_result = param_table.parse_table(input_table)
        expected_result = {'plate_reader_info.gain.0': 0.1, 
                           'plate_reader_info.gain.1' : 0.2,
                           'plate_reader_info.gain.2' : 0.3}
        self.assertEquals(3, len(param_result))
        self.assertDictEqual(expected_result, param_result)

if __name__ == "__main__":
    unittest.main()