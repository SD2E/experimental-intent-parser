import intent_parser.table.table_utils as table_utils
import unittest


class DetectTableTypeTest(unittest.TestCase):


    def test_detecting_lab_table_with_required_field(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'lab: abc' }}]}}]}]} ]
        }
        self.assertTrue(table_utils.detect_lab_table(input_table))
        
    def test_detecting_lab_table_with_optional_fields(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'lab: abc' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'experiment_id: ' }}]}}]}]} ]
        }
        self.assertTrue(table_utils.detect_lab_table(input_table))
    
    def test_detecting_measurement_table_with_required_field(self):
        input_table = {'tableRows': [
            {'tableCells': [
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'measurement-type\n' }}]}}]
                }, 
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'file-type\n' }}]}}]
                }, 
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'replicate\n' }}]}}]
                }, 
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'strains\n' }}]}}]
                }
            ]}]
        }
        self.assertTrue(table_utils.detect_new_measurement_table(input_table))
      
    def test_detecting_parameter_table_with_required_field(self):
        input_table = {'tableRows': [
            {'tableCells': [
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'Parameter\n' }}]}}]
                }, 
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'Value\n' }}]}}]
                }
            ]}]
        }
        self.assertTrue(table_utils.detect_parameter_table(input_table))
                        

if __name__ == "__main__":
    unittest.main()