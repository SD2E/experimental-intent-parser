from intent_parser.table.experiment_status_table import ExperimentStatusTable
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
import unittest

class ExperimentStatusTableTest(object):

    def setUp(self):
        self.ip_table_factory = IntentParserTableFactory()

    def tearDown(self):
        pass

    def test_table_with_xplan_request_submitted_status_type(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Pipeline Status\n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'Last Updated\n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'Path\n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'State\n'}}]}}]}
            ]},

            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'xplan_request_submitted\n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'Wed Jun 24 15:44:00 2020 \n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'unspecified\n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'True\n'}}]}}]}
            ]}
        ]}
        ip_table = self.ip_table_factory.from_google_doc(input_table)
        ip_table.set_header_row_index(0)
        experiment_status_table_parser = ExperimentStatusTable(ip_table)
        experiment_status_table_parser.process_table()
        status_result = experiment_status_table_parser.get_statuses()
        self.assertEqual(1, len(status_result))
        self.assertEqual(status_result[0].status_type, 'xplan_request_submitted')


if __name__ == "__main__":
    unittest.main()
