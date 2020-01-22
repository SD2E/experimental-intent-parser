from parameter_table import ParameterTable
import unittest


class ParameterTableTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.parameter_fields = {
            'Inoculation volume' : 'inoc_info.inoc_vol',
            'Inoculation media volume' : 'inoc_info.inoc_media_vol',
            'Inoculation increment time 1' : 'inoc_info.inc_time_1'
            }

    def test_parameter_field(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Parameter\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Inoculation volume\n'}}]}}]}]}]
        } 
        
        param_table = ParameterTable(parameter_fields=self.parameter_fields)
        param_result = param_table.parse_table(input_table)
        self.assertEquals(1, len(param_result))
        self.assertTrue('inoc_info.inoc_vol' in param_result[0])
       
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
        self.assertEquals('5:microliter', param_result[0]['inoc_info.inoc_vol'])
        
    def test_parameter_string_value_with_colon_separator(self):
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
        self.assertEquals('sc_media', param_result[0]['inoc_info.inoculation_media'])
        
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
        self.assertEquals(False, param_result[0]['validate_samples'])

if __name__ == "__main__":
    unittest.main()