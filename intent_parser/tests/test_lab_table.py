from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
from intent_parser.table.lab_table import LabTable
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.tests.test_util as test_utils
import unittest

class LabTableTest(unittest.TestCase):
    """
    Test parsing content from a lab table
    """
    def setUp(self):
        self.ip_table_factory = IntentParserTableFactory()

    def tearDown(self):
        pass
        
    def test_table_with_experiment_id(self):
        ip_table = test_utils.create_fake_lab_table()
        lab_cell = IntentParserCell()
        lab_cell.add_paragraph('lab: abc')
        ip_table.add_row([lab_cell])

        experiment_id_cell = IntentParserCell()
        experiment_id_cell.add_paragraph('experiment_id: defg')
        ip_table.add_row([experiment_id_cell])

        table_parser = LabTable(ip_table)
        table_parser.process_table()
        table_content = table_parser.get_structured_request()
        self.assertEqual(table_content[dc_constants.LAB], 'abc')
        self.assertEqual(table_content[dc_constants.EXPERIMENT_ID], 'experiment.abc.defg')
        
    def test_table_with_empty_experiment_id(self):
        ip_table = test_utils.create_fake_lab_table()
        lab_cell = IntentParserCell()
        lab_cell.add_paragraph('lab: abc')
        ip_table.add_row([lab_cell])

        experiment_id_cell = IntentParserCell()
        experiment_id_cell.add_paragraph('experiment_id: ')
        ip_table.add_row([experiment_id_cell])

        table_parser = LabTable(ip_table)
        table_parser.process_table()
        table_content = table_parser.get_structured_request()
        self.assertEqual(table_content[dc_constants.LAB], 'abc')
        self.assertEqual(table_content[dc_constants.EXPERIMENT_ID], 'experiment.abc.TBD')
    
    def test_table_without_experiment_id(self):
        ip_table = test_utils.create_fake_lab_table()
        lab_cell = IntentParserCell()
        lab_cell.add_paragraph('lab: abc')
        ip_table.add_row([lab_cell])

        experiment_id_cell = IntentParserCell()
        experiment_id_cell.add_paragraph('experiment_id: ')
        ip_table.add_row([experiment_id_cell])

        table_parser = LabTable(ip_table)
        table_parser.process_table()
        table_content = table_parser.get_structured_request()
        self.assertEqual(table_content[dc_constants.LAB], 'abc')
        self.assertEqual(table_content[dc_constants.EXPERIMENT_ID], 'experiment.abc.TBD')
        
    def test_table_with_experiment_id_spacing(self):
        ip_table = test_utils.create_fake_lab_table()
        experiment_id_cell = IntentParserCell()
        experiment_id_cell.add_paragraph('experiment_id:29422')
        ip_table.add_row([experiment_id_cell])

        table_parser = LabTable(ip_table)
        table_parser.process_table()
        table_content = table_parser.get_structured_request()
        self.assertEqual(table_content[dc_constants.LAB], 'TACC')
        self.assertEqual(table_content[dc_constants.EXPERIMENT_ID], 'experiment.tacc.29422')

if __name__ == "__main__":
    unittest.main()