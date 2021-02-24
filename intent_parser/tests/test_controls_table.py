from intent_parser.table.controls_table import ControlsTable
from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
from intent_parser.intent.sbol_dictionary_strain_intent import SBOLDictionaryStrainIntent
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.tests.test_util as test_utils
import unittest

class ControlsTableTest(unittest.TestCase):
    """
    Test parsing information from a control table
    """
    
    def setUp(self):
        self.ip_table_factory = IntentParserTableFactory()

        strain1 = SBOLDictionaryStrainIntent('https://hub.sd2e.org/user/sd2e/design/MG1655/1', 'ip_admin', 'strain1', lab_strain_names=['MG1655'])
        strain2 = SBOLDictionaryStrainIntent('https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1', 'ip_admin', 'strain2', lab_strain_names=['MG1655_LPV3'])
        strain3 = SBOLDictionaryStrainIntent('https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1', 'ip_admin', 'strain3', lab_strain_names=['UWBF_7376'])
        self.strain_mappings = {'https://hub.sd2e.org/user/sd2e/design/MG1655/1': strain1,
                                'https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1': strain2,
                                'https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1': strain3}

    def tearDown(self):
        pass

    def test_table_with_control_type(self):
        ip_table = test_utils.create_fake_controls_table()
        control_type = IntentParserCell()
        control_type.add_paragraph('HIGH_FITC')
        data_row = test_utils.create_control_table_row(control_type_cell=control_type)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table, control_types={'HIGH_FITC'})
        control_table_parser.process_table()
        control_result = control_table_parser.get_intents()
        self.assertEqual(1, len(control_result))
        expected_result = {dc_constants.TYPE: 'HIGH_FITC'}
        self.assertEqual(expected_result, control_result[0].to_structured_request())
        
    def test_table_with_1_channel(self):
        ip_table = test_utils.create_fake_controls_table()
        control_type = IntentParserCell()
        control_type.add_paragraph('HIGH_FITC')

        channel = IntentParserCell()
        channel.add_paragraph('BL1-A')
        data_row = test_utils.create_control_table_row(channel_cell=channel,
                                                       control_type_cell=control_type)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table, control_types={'HIGH_FITC'})
        control_table_parser.process_table()
        control_result = control_table_parser.get_intents()
        expected_result = {dc_constants.TYPE: 'HIGH_FITC',
                           dc_constants.CHANNEL: 'BL1-A'}
        self.assertEqual(expected_result, control_result[0].to_structured_request())
    
    def test_table_with_multiple_channels(self):
        ip_table = test_utils.create_fake_controls_table()
        control_type = IntentParserCell()
        control_type.add_paragraph('HIGH_FITC')

        channel = IntentParserCell()
        channel.add_paragraph('BL1-A, BL2-A')
        data_row = test_utils.create_control_table_row(channel_cell=channel,
                                                       control_type_cell=control_type)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table, control_types={'HIGH_FITC'})
        control_table_parser.process_table()
        control_result = control_table_parser.get_intents()
        expected_result = {dc_constants.TYPE: 'HIGH_FITC',
                           dc_constants.CHANNEL: 'BL1-A'}
        self.assertEqual(expected_result, control_result[0].to_structured_request())
        
    def test_table_with_1_strain(self):
        ip_table = test_utils.create_fake_controls_table()
        strains = IntentParserCell()
        strains.add_paragraph('UWBF_25784')

        control_type = IntentParserCell()
        control_type.add_paragraph('HIGH_FITC')

        data_row = test_utils.create_control_table_row(strains_cell=strains,
                                                       control_type_cell=control_type)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table, control_types={'HIGH_FITC'})
        control_table_parser.process_table()
        control_result = control_table_parser.get_intents()
        self.assertEqual(1, len(control_result))
        expected_result = {dc_constants.TYPE: 'HIGH_FITC'}
        self.assertEqual(expected_result, control_result[0].to_structured_request())

    def test_table_with_1_timepoint(self):
        ip_table = test_utils.create_fake_controls_table()
        content = IntentParserCell()
        content.add_paragraph('8 hour')

        control_type = IntentParserCell()
        control_type.add_paragraph('HIGH_FITC')

        data_row = test_utils.create_control_table_row(timepoint_cell=content,
                                                       control_type_cell=control_type)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table, timepoint_units={'hour'}, control_types={'HIGH_FITC'})
        control_table_parser.process_table()
        control_result = control_table_parser.get_intents()
        self.assertEqual(1, len(control_result))
        expected_timepoint = {dc_constants.VALUE: 8.0, dc_constants.UNIT: 'hour'}
        expected_result = {dc_constants.TYPE: 'HIGH_FITC',
                           dc_constants.TIMEPOINTS: [expected_timepoint]}
        self.assertEqual(expected_result, control_result[0].to_structured_request())

    def test_strains_with_uris(self):
        ip_table = test_utils.create_fake_controls_table()
        control_type = IntentParserCell()
        control_type.add_paragraph('HIGH_FITC')

        strains = IntentParserCell()
        strains.add_paragraph('UWBF_7376', link='https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1')
        data_row = test_utils.create_control_table_row(strains_cell=strains,
                                                       control_type_cell=control_type)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table,
                                             strain_mapping=self.strain_mappings,
                                             control_types={'HIGH_FITC'})
        control_table_parser.process_table()
        control_result = control_table_parser.get_intents()
        self.assertEquals(1, len(control_result))
        exp_res = {'sbh_uri': 'https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1', 'label': 'strain3',
                    'lab_id': 'name.ip_admin.UWBF_7376'}
        expected_result = {dc_constants.TYPE: 'HIGH_FITC',
                           dc_constants.STRAINS: [exp_res]}
        self.assertEqual(expected_result, control_result[0].to_structured_request())
    
    def test_strains_with_uri_and_trailing_strings(self):
        ip_table = test_utils.create_fake_controls_table()
        control_type = IntentParserCell()
        control_type.add_paragraph('HIGH_FITC')

        strains = IntentParserCell()
        strains.add_paragraph('MG1655', link='https://hub.sd2e.org/user/sd2e/design/MG1655/1')
        strains.add_paragraph(', MG1655_LPV3,MG1655_RPU_Standard')
        data_row = test_utils.create_control_table_row(strains_cell=strains,
                                                       control_type_cell=control_type)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table,
                                             strain_mapping=self.strain_mappings,
                                             control_types={'HIGH_FITC'})
        control_table_parser.process_table()
        control_result = control_table_parser.get_intents()
        self.assertEquals(1, len(control_result))

        exp_res = {'sbh_uri': 'https://hub.sd2e.org/user/sd2e/design/MG1655/1', 'label': 'strain1',
                    'lab_id': 'name.ip_admin.MG1655'}
        expected_result = {dc_constants.TYPE: 'HIGH_FITC',
                           dc_constants.STRAINS: [exp_res]}
        self.assertEqual(expected_result, control_result[0].to_structured_request())
        
    def test_strains_with_string_and_trailing_uris(self):
        ip_table = test_utils.create_fake_controls_table()
        control_type = IntentParserCell()
        control_type.add_paragraph('HIGH_FITC')

        strains = IntentParserCell()
        strains.add_paragraph('MG1655_RPU_Standard,')
        strains.add_paragraph('MG1655', link='https://hub.sd2e.org/user/sd2e/design/MG1655/1')
        strains.add_paragraph(',')
        strains.add_paragraph('MG1655_LPV3', link='https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1')
        data_row = test_utils.create_control_table_row(strains_cell=strains,
                                                       control_type_cell=control_type)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table,
                                             strain_mapping=self.strain_mappings,
                                             control_types={'HIGH_FITC'})
        control_table_parser.process_table()
        control_result = control_table_parser.get_intents()
        self.assertEqual(1, len(control_result))
        
        exp_res = [{'sbh_uri': 'https://hub.sd2e.org/user/sd2e/design/MG1655/1', 'label': 'strain1',
                    'lab_id': 'name.ip_admin.MG1655'},
                   {'sbh_uri': 'https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1', 'label': 'strain2',
                    'lab_id': 'name.ip_admin.MG1655_LPV3'}]
        expected_result = {dc_constants.TYPE: 'HIGH_FITC',
                           dc_constants.STRAINS: exp_res}
        self.assertEqual(expected_result, control_result[0].to_structured_request())
    
    def test_strains_with_mix_string_and_uri(self):
        ip_table = test_utils.create_fake_controls_table()
        control_type = IntentParserCell()
        control_type.add_paragraph('HIGH_FITC')

        strains = IntentParserCell()
        strains.add_paragraph('MG1655', link='https://hub.sd2e.org/user/sd2e/design/MG1655/1')
        strains.add_paragraph(',')
        strains.add_paragraph('MG1655_RPU_Standard\n')
        strains.add_paragraph(',\n')
        strains.add_paragraph('MG1655_LPV3', link='https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1')
        data_row = test_utils.create_control_table_row(strains_cell=strains,
                                                       control_type_cell=control_type)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table,
                                             strain_mapping=self.strain_mappings,
                                             control_types={'HIGH_FITC'})
        control_table_parser.process_table()
        control_result = control_table_parser.get_intents()
        self.assertEqual(1, len(control_result))
        
        exp_res = [{'sbh_uri': 'https://hub.sd2e.org/user/sd2e/design/MG1655/1', 'label': 'strain1', 'lab_id': 'name.ip_admin.MG1655'},
                   {'sbh_uri': 'https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1', 'label': 'strain2', 'lab_id': 'name.ip_admin.MG1655_LPV3'}]
        expected_result = {dc_constants.TYPE: 'HIGH_FITC',
                           dc_constants.STRAINS: exp_res}
        self.assertEqual(expected_result, control_result[0].to_structured_request())
    
    def test_table_with_contents(self):
        ip_table = test_utils.create_fake_controls_table()
        control_type = IntentParserCell()
        control_type.add_paragraph('HIGH_FITC')

        content = IntentParserCell()
        content.add_paragraph('beta_estradiol', link='https://hub.sd2e.org/user/sd2e/design/beta_estradiol/1')
        data_row = test_utils.create_control_table_row(contents_cell=content,
                                                       control_type_cell=control_type)
        ip_table.add_row(data_row)

        control_table_parser = ControlsTable(ip_table, control_types={'HIGH_FITC'})
        control_table_parser.process_table()
        control_result = control_table_parser.get_intents()

        content = {dc_constants.NAME: {dc_constants.LABEL: 'beta_estradiol',
                                       dc_constants.SBH_URI: 'https://hub.sd2e.org/user/sd2e/design/beta_estradiol/1'}}

        expected_result = {dc_constants.TYPE: 'HIGH_FITC',
                           dc_constants.CONTENTS: [content]}
        self.assertEqual(expected_result, control_result[0].to_structured_request())

if __name__ == "__main__":
    unittest.main()

