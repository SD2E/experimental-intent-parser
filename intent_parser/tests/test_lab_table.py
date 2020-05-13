from intent_parser.table.lab_table import LabTable
import unittest

class LabTableTest(unittest.TestCase):
    """
    Test parsing content from a lab table
    """
    
    def test_table_with_experiment_id(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'lab: abc\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'experiment_id: defg\n' }}]}}]}]} ]
        }
        
        table_parser =  LabTable()
        table_content = table_parser.parse_table(input_table)
        self.assertEqual(table_content['lab'], 'abc')
        self.assertEqual(table_content['experiment_id'], 'experiment.abc.defg')
        
    def test_table_with_empty_experiment_id(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'lab: abc' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'experiment_id: ' }}]}}]}]} ]
        }
        
        table_parser =  LabTable()
        table_content = table_parser.parse_table(input_table)
        self.assertEqual(table_content['lab'], 'abc')
        self.assertEqual(table_content['experiment_id'], 'experiment.abc.TBD')
    
    def test_table_without_experiment_id(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'lab: abc' }}]}}]}]} ]
        }
        
        table_parser =  LabTable()
        table_content = table_parser.parse_table(input_table)
        self.assertEqual(table_content['lab'], 'abc')
        self.assertEqual(table_content['experiment_id'], 'experiment.abc.TBD')

if __name__ == "__main__":
    unittest.main()