from datetime import datetime
from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.table.experiment_status_table import ExperimentStatusTableParser
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
import intent_parser.constants.ta4_db_constants as ta4_constants
import intent_parser.tests.test_util as test_utils
import unittest

class ExperimentStatusTableTest(unittest.TestCase):

    def setUp(self):
        self.ip_table_factory = IntentParserTableFactory()
        self.status_mappings = {ta4_constants.XPLAN_REQUEST_SUBMITTED: 'When the experiment was submitted to the lab',
                                'annotated': 'When the lab trace was annotated, and its associated path',
                                'comparison_passed': 'Whether the annotated lab trace passed metadata comparison',
                                'converted': 'When the lab trace was converted after upload, and its associated path',
                                'ingested': 'When the annotated lab trace was ingested, and its associated path',
                                'mtypes': 'The state is a string that contains an encoding of the experiment\'s measurement types: Plate Reader (P), Flow (F), RNASeq (R), DNASeq (D), and CFU counts (C)',
                                'obs_load': 'When the ingested experiment observations were loaded',
                                'uploaded': 'When the experiment was uploaded by the lab, and its associated path'}

    def tearDown(self):
        pass

    def test_table_with_xplan_request_submitted_status_type(self):
        ip_table = test_utils.create_fake_experiment_status_table()
        status_type = IntentParserCell()
        status_type.add_paragraph('When the experiment was submitted to the lab')

        last_updated = IntentParserCell()
        last_updated.add_paragraph('2020/6/24 15:44:00')

        path = IntentParserCell()
        path.add_paragraph('agave://foo.json')

        state = IntentParserCell()
        state.add_paragraph('Succeeded')
        data_row = test_utils.create_experiment_status_table_row(pipeline_status_cell=status_type,
                                                                 last_updated_cell=last_updated,
                                                                 path_cell=path,
                                                                 state_cell=state)
        ip_table.add_row(data_row)

        experiment_status_table_parser = ExperimentStatusTableParser(ip_table, self.status_mappings)
        experiment_status_table_parser.process_table()
        status_results = experiment_status_table_parser.get_statuses()
        self.assertEqual(8, len(status_results))
        for status in status_results:
            if status.status_type == ta4_constants.XPLAN_REQUEST_SUBMITTED:
                self.assertEqual(status.last_updated, datetime.strptime('2020/6/24 15:44:00', '%Y/%m/%d %H:%M:%S'))
                self.assertEqual(status.state, True)
                self.assertEqual(status.path, 'agave://foo.json')
            else:
                self.assertEqual(status.state, 'unspecified')
                self.assertEqual(status.path, 'no data')


if __name__ == "__main__":
    unittest.main()
