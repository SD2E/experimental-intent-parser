from intent_parser.table.controls_table import ControlsTable
from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.tests.test_util as test_utils
import unittest

class ControlsTableTest(unittest.TestCase):
    """
    Test parsing information from a control table
    """
    
    def setUp(self):
        self.ip_table_factory = IntentParserTableFactory()

    def tearDown(self):
        pass

    def test_table_with_control_type(self):
        ip_table = test_utils.create_fake_controls_table()
        control_type = IntentParserCell()
        control_type.add_paragraph('HIGH_FITC')
        data_row = test_utils.create_control_table_row(control_type_cell=control_type)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table, control_types={'HIGH_FITC'})
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        self.assertEqual(control_result[0][dc_constants.TYPE], 'HIGH_FITC')
        
    def test_table_with_1_channel(self):
        ip_table = test_utils.create_fake_controls_table()
        channel = IntentParserCell()
        channel.add_paragraph('BL1-A')
        data_row = test_utils.create_control_table_row(channel_cell=channel)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        self.assertEqual(control_result[0][dc_constants.CHANNEL], 'BL1-A')
    
    def test_table_with_multiple_channels(self):
        ip_table = test_utils.create_fake_controls_table()
        channel = IntentParserCell()
        channel.add_paragraph('BL1-A, BL2-A')
        data_row = test_utils.create_control_table_row(channel_cell=channel)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        self.assertEqual(control_result[0][dc_constants.CHANNEL], 'BL1-A')
        
    def test_table_with_1_strain(self):
        ip_table = test_utils.create_fake_controls_table()
        strains = IntentParserCell()
        strains.add_paragraph('UWBF_25784')
        data_row = test_utils.create_control_table_row(strains_cell=strains)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        actual_strains = control_result[0][dc_constants.STRAINS]
        self.assertEqual(1, len(actual_strains))
        self.assertEqual(actual_strains[0], 'UWBF_25784')
    
    def test_table_with_1_timepoint(self):
        ip_table = test_utils.create_fake_controls_table()
        content = IntentParserCell()
        content.add_paragraph('8 hour')
        data_row = test_utils.create_control_table_row(timepoint_cell=content)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table, timepoint_units={'hour'})
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        timepoint_list = control_result[0][dc_constants.TIMEPOINTS]
        self.assertEqual(1, len(timepoint_list))
        expected_timepoint = {dc_constants.VALUE: 8.0, dc_constants.UNIT: 'hour'}
        self.assertEqual(timepoint_list[0], expected_timepoint)

    def test_strains_with_uris(self):
        ip_table = test_utils.create_fake_controls_table()
        strains = IntentParserCell()
        strains.add_paragraph('UWBF_7376', link='https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1')
        data_row = test_utils.create_control_table_row(strains_cell=strains)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEquals(1, len(control_result))
        self.assertEqual(1, len(control_result[0][dc_constants.STRAINS]))
        self.assertEqual('UWBF_7376', control_result[0][dc_constants.STRAINS][0])
    
    def test_strains_with_uri_and_trailing_strings(self):
        ip_table = test_utils.create_fake_controls_table()
        strains = IntentParserCell()
        strains.add_paragraph('MG1655', link='https://hub.sd2e.org/user/sd2e/design/MG1655/1')
        strains.add_paragraph(', MG1655_LPV3,MG1655_RPU_Standard')
        data_row = test_utils.create_control_table_row(strains_cell=strains)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEquals(1, len(control_result))

        exp_res = ['MG1655', 'MG1655_LPV3','MG1655_RPU_Standard']
        self.assertListEqual(exp_res, control_result[0]['strains'])
        
    def test_strains_with_string_and_trailing_uris(self):
        ip_table = test_utils.create_fake_controls_table()
        strains = IntentParserCell()
        strains.add_paragraph('MG1655_RPU_Standard,')
        strains.add_paragraph('MG1655,', link='https://hub.sd2e.org/user/sd2e/design/MG1655/1')
        strains.add_paragraph('MG1655_LPV3', link='https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1')
        data_row = test_utils.create_control_table_row(strains_cell=strains)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        
        exp_res = ['MG1655_RPU_Standard',
                   'MG1655',
                   'MG1655_LPV3']
        self.assertListEqual(exp_res, control_result[0][dc_constants.STRAINS])
    
    def test_strains_with_mix_string_and_uri(self):
        ip_table = test_utils.create_fake_controls_table()
        strains = IntentParserCell()
        strains.add_paragraph('MG1655', link='https://hub.sd2e.org/user/sd2e/design/MG1655/1')
        strains.add_paragraph(',')
        strains.add_paragraph('MG1655_RPU_Standard\n')
        strains.add_paragraph(',\n')
        strains.add_paragraph('MG1655_LPV3', link='https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1')
        data_row = test_utils.create_control_table_row(strains_cell=strains)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        
        exp_res = ['MG1655', 'MG1655_RPU_Standard', 'MG1655_LPV3']
        self.assertListEqual(exp_res, control_result[0]['strains'])
    
    def test_table_with_contents(self):
        ip_table = test_utils.create_fake_controls_table()
        content = IntentParserCell()
        content.add_paragraph('beta_estradiol', link='https://hub.sd2e.org/user/sd2e/design/beta_estradiol/1')
        data_row = test_utils.create_control_table_row(contents_cell=content)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
        self.assertEqual(1, len(control_result))
        self.assertEqual(1, len(control_result[0][dc_constants.CONTENTS]))
        content = control_result[0][dc_constants.CONTENTS][0]
        self.assertEqual(2, len(content[dc_constants.NAME]))
        self.assertEqual(content[dc_constants.NAME][dc_constants.LABEL], 'beta_estradiol')
        self.assertEqual(content[dc_constants.NAME][dc_constants.SBH_URI], 'https://hub.sd2e.org/user/sd2e/design/beta_estradiol/1')

    def test_(self):
        ip_table = test_utils.create_fake_controls_table()
        control_type = IntentParserCell()
        control_type.add_paragraph('EMPTY_VECTOR')

        strains = IntentParserCell()
        strains.add_paragraph('https://hub.sd2e.org/user/sd2e/design/W303/1', link='https://hub.sd2e.org/user/sd2e/design/W303/1')
        channel = IntentParserCell()
        channel.add_paragraph('\n')

        content = IntentParserCell()
        content.add_paragraph('EMPTY_VECTOR', )

        timepoint = IntentParserCell()
        timepoint.add_paragraph('0 hours')

        data_row = test_utils.create_control_table_row(control_type_cell=control_type,
                                                       strains_cell=strains,
                                                       channel_cell=channel,
                                                       contents_cell=content,
                                                       timepoint_cell=timepoint)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table)
        control_result = control_table_parser.process_table()
     
if __name__ == "__main__":
    unittest.main()

