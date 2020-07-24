from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.table.experiment_specification_table import ExperimentSpecificationTable
import intent_parser.tests.test_util as test_utils
import unittest

class ExperimentSpecificationTableTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_table(self):
        ip_table = test_utils.create_fake_experiment_specification_table()
        experiment_id = IntentParserCell()
        experiment_id.add_paragraph('experiment.transcriptic.foo')
        status_table1 = IntentParserCell()
        status_table1.add_paragraph('Table 3')
        data_row = test_utils.create_experiment_specification_table_row(experiment_id_cell=experiment_id,
                                                      experiment_status_cell=status_table1)
        ip_table.add_row(data_row)
        exp_spec_table = ExperimentSpecificationTable(intent_parser_table=ip_table, lab_ids={'Transcriptic'})
        exp_spec_table.process_table()
        result = exp_spec_table.experiment_id_to_status_table()
        self.assertEqual(1, len(result))
        self.assertTrue('experiment.transcriptic.foo' in result)
        self.assertEqual(3, result['experiment.transcriptic.foo'])


if __name__ == '__main__':
    unittest.main()
