from intent_parser.table.experiment_status_table import ExperimentStatusTableParser
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
import unittest

class ExperimentStatusTableTest(unittest.TestCase):

    def setUp(self):
        self.ip_table_factory = IntentParserTableFactory()

    def tearDown(self):
        pass

    def test_table_with_xplan_request_submitted_status_type(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Pipeline Status'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'Last updated'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'Path'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'State'}}]}}]}
            ]},

            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'xplan_request_submitted'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': '2020/6/24 15:44:00'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'unspecified'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'True'}}]}}]}
            ]}
        ]}
        ip_table = self.ip_table_factory.from_google_doc(input_table)
        ip_table.set_header_row_index(0)
        experiment_status_table_parser = ExperimentStatusTableParser(ip_table)
        experiment_status_table_parser.process_table()
        status_results = experiment_status_table_parser.get_statuses()
        self.assertEqual(1, len(status_results))
        status = status_results.pop()
        self.assertEqual(status.status_type, 'xplan_request_submitted')

if __name__ == "__main__":
    unittest.main()
