from intent_parser.intent.measure_property_intent import TimepointIntent, ReagentIntent, NamedLink, MeasuredUnit
from intent_parser.table.intent_parser_cell import IntentParserCell
import intent_parser.tests.test_util as test_utils
import unittest

class OpilTest(unittest.TestCase):


    def test_reagent_to_opil_without_timepoint(self):
        reagent_name = NamedLink('M9', 'https://hub.sd2e.org/user/sd2e/design/M9/1')
        reagent = ReagentIntent(reagent_name)
        reagent_value = MeasuredUnit(10.0, 'uM')
        reagent.add_reagent_value(reagent_value)

        #TODO:
        reagent_component = reagent.reagent_values_to_opil_measures()

    def _create_transcriptic_lab_table(self):
        lab_table = test_utils.create_fake_lab_table()
        lab_cell = IntentParserCell()
        lab_cell.add_paragraph('lab: Transcriptic')
        lab_table.add_row([lab_cell])
        return lab_table


if __name__ == '__main__':
    unittest.main()
