from intent_parser.table.controls_table import ControlsTable
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
import unittest

class ControlsTableTest(unittest.TestCase):
    """
    Test parsing information from a control table
    """
    
    def setUp(self):
        self.ip_table_factory = IntentParserTableFactory()

    def tearDown(self):
        pass

    def test_table_with_control_type(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Control Type\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'HIGH_FITC\n'}}]}}]}]}]
        } 
        ip_table = self.ip_table_factory.from_google_doc(input_table) 
        ip_table.set_header_row_index(0)
        control_table_parser = ControlsTable(ip_table, control_types={'HIGH_FITC'})
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        self.assertEqual(control_result[0]['type'], 'HIGH_FITC')
        
    def test_table_with_1_channel(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Channel\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'BL1-A\n'}}]}}]}]}]
        } 
        ip_table = self.ip_table_factory.from_google_doc(input_table) 
        ip_table.set_header_row_index(0)
        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        self.assertEqual(control_result[0]['channel'], 'BL1-A')
    
    def test_table_with_multiple_channels(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Channel\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'BL1-A, BL2-A\n'}}]}}]}]}]
        } 
        ip_table = self.ip_table_factory.from_google_doc(input_table) 
        ip_table.set_header_row_index(0)
        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        self.assertEqual(control_result[0]['channel'], 'BL1-A')
        
    def test_table_with_1_strain(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Strains\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'UWBF_25784\n'}}]}}]}]}]
        } 
    
        ip_table = self.ip_table_factory.from_google_doc(input_table) 
        ip_table.set_header_row_index(0)
        
        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        actual_strains = control_result[0]['strains']
        self.assertEqual(1, len(actual_strains))
        self.assertEqual(actual_strains[0], 'UWBF_25784')
    
    def test_table_with_1_timepoint(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Timepoint\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '8 hour\n'}}]}}]}]}]
        } 
    
        ip_table = self.ip_table_factory.from_google_doc(input_table) 
        ip_table.set_header_row_index(0)
        
        control_table_parser = ControlsTable(ip_table, timepoint_units={'hour'})
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        timepoint_list = control_result[0]['timepoints']
        self.assertEqual(1, len(timepoint_list))
        expected_timepoint = {'value': 8.0, 'unit': 'hour'}
        self.assertEqual(timepoint_list[0], expected_timepoint)

    def test_strains_with_uris(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Strains\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'UWBF_7376','textStyle': {'link': {'url': 'https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1'}
                        }}}]}}]}]}]
        } 
        ip_table = self.ip_table_factory.from_google_doc(input_table)
        ip_table.set_header_row_index(0)
        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEquals(1, len(control_result))
        self.assertEqual(1, len(control_result[0]['strains']))
        self.assertEqual('UWBF_7376', control_result[0]['strains'][0])
    
    def test_strains_with_uri_and_trailing_strings(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Strains\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'MG1655','textStyle': {'link': {'url': 'https://hub.sd2e.org/user/sd2e/design/MG1655/1'}
                        }}}]}},
                {'paragraph': {'elements': [{'textRun': {
                'content': ', MG1655_LPV3,MG1655_RPU_Standard\n'}}]}}]}]}]
        } 
    
        ip_table = self.ip_table_factory.from_google_doc(input_table)
        ip_table.set_header_row_index(0)
        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEquals(1, len(control_result))
        
        exp_res = ['MG1655', 'MG1655_LPV3','MG1655_RPU_Standard']
        self.assertListEqual(exp_res, control_result[0]['strains'])
        
    def test_strains_with_string_and_trailing_uris(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Strains\n' }}]}}]}]},
            {'tableCells': [{'content': [
                {'paragraph': {'elements': [{'textRun': {
                'content': 'MG1655_RPU_Standard,\n'}}]}},
                {'paragraph': {'elements': [{'textRun': {
                'content': 'MG1655','textStyle': {'link': {'url': 'https://hub.sd2e.org/user/sd2e/design/MG1655/1'}
                        }}}]}},
                {'paragraph': {'elements': [{'textRun': {
                'content': ','}}]}},
                {'paragraph': {'elements': [{'textRun': {
                'content': 'MG1655_LPV3','textStyle': {'link': {'url': 'https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1'}
                        }}}]}} ]}]}]
        } 
    
        ip_table = self.ip_table_factory.from_google_doc(input_table)
        ip_table.set_header_row_index(0)
        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        
        exp_res = ['MG1655_RPU_Standard',
                   'MG1655',
                   'MG1655_LPV3']
        self.assertListEqual(exp_res, control_result[0]['strains'])
    
    def test_strains_with_mix_string_and_uri(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Strains\n' }}]}}]}]},
            {'tableCells': [{'content': [ 
                {'paragraph': {'elements': [{'textRun': {
                'content': 'MG1655','textStyle': {'link': {'url': 'https://hub.sd2e.org/user/sd2e/design/MG1655/1'}
                        }}}]}},
                {'paragraph': {'elements': [{'textRun': {
                'content': ',\n'}}]}},
                {'paragraph': {'elements': [{'textRun': {
                'content': 'MG1655_RPU_Standard\n'}}]}},
                {'paragraph': {'elements': [{'textRun': {
                'content': ',\n'}}]}},
                {'paragraph': {'elements': [{'textRun': {
                'content': 'MG1655_LPV3','textStyle': {'link': {'url': 'https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1'}
                        }}}]}} ]}]}]
        } 
    
        ip_table = self.ip_table_factory.from_google_doc(input_table)
        ip_table.set_header_row_index(0)
        
        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        
        exp_res = ['MG1655', 'MG1655_RPU_Standard', 'MG1655_LPV3']
        self.assertListEqual(exp_res, control_result[0]['strains'])
    
    def test_table_with_contents(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Contents\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'beta_estradiol\n','textStyle': {'link': {'url': 'https://hub.sd2e.org/user/sd2e/design/beta_estradiol/1'}
                        } }}]}}]}]}]
        } 
        ip_table = self.ip_table_factory.from_google_doc(input_table) 
        ip_table.set_header_row_index(0)
        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        self.assertEqual(1, len(control_result[0]['contents']))
        content = control_result[0]['contents'][0]
        self.assertEqual(2, len(content['name']))
        self.assertEqual(content['name']['label'], 'beta_estradiol') 
        self.assertEqual(content['name']['sbh_uri'], 'https://hub.sd2e.org/user/sd2e/design/beta_estradiol/1') 
     
if __name__ == "__main__":
    unittest.main()

