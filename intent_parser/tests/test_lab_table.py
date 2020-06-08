from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
from intent_parser.table.lab_table import LabTable
import unittest

class LabTableTest(unittest.TestCase):
    """
    Test parsing content from a lab table
    """
    def setUp(self):
        self.ip_table_factory = IntentParserTableFactory()
        
    def test_table_with_experiment_id(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'lab: abc\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'experiment_id: defg\n' }}]}}]}]} ]
        }
        ip_table = self.ip_table_factory.from_google_doc(input_table)
        ip_table.set_header_row_index(0)
        table_parser =  LabTable(ip_table)
        table_content = table_parser.process_table()
        self.assertEqual(table_content['lab'], 'abc')
        self.assertEqual(table_content['experiment_id'], 'experiment.abc.defg')
        
    def test_table_with_empty_experiment_id(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'lab: abc' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'experiment_id: ' }}]}}]}]} ]
        }
        ip_table = self.ip_table_factory.from_google_doc(input_table)
        ip_table.set_header_row_index(0)
        table_parser =  LabTable(ip_table)
        table_content = table_parser.process_table()
        self.assertEqual(table_content['lab'], 'abc')
        self.assertEqual(table_content['experiment_id'], 'experiment.abc.TBD')
    
    def test_table_without_experiment_id(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'lab: abc' }}]}}]}]} ]
        }
        ip_table = self.ip_table_factory.from_google_doc(input_table)
        ip_table.set_header_row_index(0)
        table_parser =  LabTable(ip_table)
        table_content = table_parser.process_table()
        self.assertEqual(table_content['lab'], 'abc')
        self.assertEqual(table_content['experiment_id'], 'experiment.abc.TBD')
        
    def test_table_with_experiment_id_spacing(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Experiment_id:29422' }}]}}]}]} ]
        }
        ip_table = self.ip_table_factory.from_google_doc(input_table)
        ip_table.set_header_row_index(0)
        table_parser =  LabTable(ip_table)
        table_content = table_parser.process_table()
        self.assertEqual(table_content['lab'], 'tacc')
        self.assertEqual(table_content['experiment_id'], 'experiment.tacc.29422')

if __name__ == "__main__":
    unittest.main()