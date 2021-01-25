from intent_parser.intent_parser_factory import IntentParserFactory
from intent_parser.accessor.catalog_accessor import CatalogAccessor
from intent_parser.accessor.sbol_dictionary_accessor import SBOLDictionaryAccessor
from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.table.table_processor.opil_processor import OPILProcessor
from unittest.mock import patch
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.tests.test_util as test_utils
import unittest

class OpilTest(unittest.TestCase):

    @patch('intent_parser.accessor.intent_parser_sbh.IntentParserSBH')
    def setUp(self, mock_intent_parser_sbh):
        self.mock_intent_parser_sbh = mock_intent_parser_sbh
        self.sbol_dictionary = SBOLDictionaryAccessor(ip_constants.SD2_SPREADSHEET_ID,
                                                      self.mock_intent_parser_sbh)
        self.sbol_dictionary.initial_fetch()
        self.catalog_accessor = CatalogAccessor()

        self.control_table = test_utils.create_fake_controls_table(1)
        control_type = IntentParserCell()
        control_type.add_paragraph('HIGH_FITC')
        channel = IntentParserCell()
        channel.add_paragraph('BL1-A')
        timepoint = IntentParserCell()
        timepoint.add_paragraph('8 hour')
        strain = IntentParserCell()
        strain.add_paragraph('UWBF_7300', link='https://hub.sd2e.org/user/sd2e/design/UWBF_7300/1')
        content = IntentParserCell()
        content.add_paragraph('beta_estradiol 0.05 micromole')
        data_row = test_utils.create_control_table_row(control_type_cell=control_type,
                                                       channel_cell=channel,
                                                       timepoint_cell=timepoint,
                                                       strains_cell=strain,
                                                       contents_cell=content)
        self.control_table.add_row(data_row)

        self.lab_table = test_utils.create_fake_lab_table()
        lab_cell = IntentParserCell()
        lab_cell.add_paragraph('lab: Transcriptic')
        self.lab_table.add_row([lab_cell])

    def tearDown(self):
        pass

    def test_output_for_control_table_size_1(self):
        opil_processor = OPILProcessor(self.catalog_accessor,
                                       self.sbol_dictionary,
                                       lab_names=['Transcriptic'])
        opil_processor.process_intent(lab_tables=[self.lab_table],
                                      control_tables=[self.control_table],
                                      parameter_tables=[],
                                      measurement_tables=[])


if __name__ == '__main__':
    unittest.main()
