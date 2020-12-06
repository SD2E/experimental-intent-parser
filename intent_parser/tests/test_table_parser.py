from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
import unittest

class TableParserTest(unittest.TestCase):
    """
    Test Intent Parser when parsing content from tables.
    """

    def setUp(self):
        self.ip_table_factory = IntentParserTableFactory()

    def tearDown(self):
        pass

    def test_table_with_whitespace(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'notes'}}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'a note'}}]}}]}]}]
        }
        ip_table = self.ip_table_factory.from_google_doc({'table': input_table,
                                                         'startIndex': 0,
                                                         'endIndex': 100})

        self.assertEqual('notes', ip_table.get_cell(0, 0).get_text())
        self.assertEqual('a note', ip_table.get_cell(1, 0).get_text())

    def test_table_with_trailing_whitespace(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'notes'}}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '  a  note  '}}]}}]}]}]
        }
        ip_table = self.ip_table_factory.from_google_doc({'table': input_table,
                                                         'startIndex': 0,
                                                         'endIndex': 100})

        self.assertEqual('notes', ip_table.get_cell(0, 0).get_text())
        self.assertEqual('  a  note  ', ip_table.get_cell(1, 0).get_text())

    def test_table_with_commas(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'strains'}}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'AND_00, AND_01, AND_10'}}]}}]}]}]
        }
        ip_table = self.ip_table_factory.from_google_doc({'table': input_table,
                                                          'startIndex': 0,
                                                          'endIndex': 100})

        self.assertEqual('strains', ip_table.get_cell(0, 0).get_text())
        self.assertEqual('AND_00, AND_01, AND_10', ip_table.get_cell(1, 0).get_text())

    def test_table_with_commas_and_newline(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'strains'}}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'AND_00, AND_01, AND_10\n'}}]}}]}]}]
        }
        ip_table = self.ip_table_factory.from_google_doc({'table': input_table,
                                                          'startIndex': 0,
                                                          'endIndex': 100})

        self.assertEqual('strains', ip_table.get_cell(0, 0).get_text())
        self.assertEqual('AND_00, AND_01, AND_10\n', ip_table.get_cell(1, 0).get_text())

    def test_table_with_newline_before_commas(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'strains'}}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'AND_00, \nAND_01,\n AND_10\n'}}]}}]}]}]
        }
        ip_table = self.ip_table_factory.from_google_doc({'table': input_table,
                                                          'startIndex': 0,
                                                          'endIndex': 100})

        self.assertEqual('strains', ip_table.get_cell(0, 0).get_text())
        self.assertEqual('AND_00, \nAND_01,\n AND_10\n', ip_table.get_cell(1, 0).get_text())

if __name__ == '__main__':
    unittest.main()
