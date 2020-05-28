from intent_parser.table.controls_table import ControlsTable
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
import unittest

class ControlsTableTest(unittest.TestCase):
    """
    Test parsing information from a measurement table
    """
    
    def setUp(self):
        self.ip_table_factory = IntentParserTableFactory()

    def tearDown(self):
        pass

    def test_table_with_control_type(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Table 1: Control\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Control Type\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'HIGH_FITC\n'}}]}}]}]}]
        } 
        ip_table = self.ip_table_factory.from_google_doc(input_table) 
        control_table_parser = ControlsTable(ip_table, control_types={'HIGH_FITC'})
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        self.assertEqual(control_result[0]['type'], 'HIGH_FITC')
        
    def test_table_with_1_channel(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Table 1: Control\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Channel\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'BL1-A\n'}}]}}]}]}]
        } 
        ip_table = self.ip_table_factory.from_google_doc(input_table) 
        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        self.assertEqual(control_result[0]['channels'], 'BL1-A')
    
    def test_table_with_2_channels(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Table 1: Control\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Channel\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'BL1-A, BL2-A\n'}}]}}]}]}]
        } 
        ip_table = self.ip_table_factory.from_google_doc(input_table) 
        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        self.assertEqual(control_result[0]['channels'], 'BL1-A')
        
    def test_table_with_1_strain(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Table 1: Control\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Strains\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'UWBF_25784\n'}}]}}]}]}]
        } 
    
        ip_table = self.ip_table_factory.from_google_doc(input_table) 
        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        actual_strains = control_result[0]['strains']
        self.assertEqual(1, len(actual_strains))
        self.assertEqual(actual_strains[0], 'UWBF_25784')
    
    def test_table_with_2_strains(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Table 1: Control\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Strains\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'UWBF_6390, UWBF_24864\n'}}]}}]}]}]
        } 
    
        ip_table = self.ip_table_factory.from_google_doc(input_table) 
        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        actual_strains = control_result[0]['strains']
        self.assertEqual(2, len(actual_strains))
        self.assertEqual(actual_strains[0], 'UWBF_6390')
        self.assertEqual(actual_strains[1], 'UWBF_24864')
        
    def test_table_with_1_timepoint(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Table 1: Control\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Timepoints\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '8 hour\n'}}]}}]}]}]
        } 
    
        ip_table = self.ip_table_factory.from_google_doc(input_table) 
        control_table_parser = ControlsTable(ip_table, timepoint_units={'hour'})
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        timepoint_list = control_result[0]['timepoints']
        self.assertEqual(1, len(timepoint_list))
        expected_timepoint = {'value': 8.0, 'unit': 'hour'}
        self.assertEqual(timepoint_list[0], expected_timepoint)


if __name__ == "__main__":
    unittest.main()