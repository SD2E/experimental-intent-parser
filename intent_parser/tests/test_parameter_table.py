from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
from intent_parser.table.parameter_table import ParameterTable
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.tests.test_util as test_utils
import unittest

class ParameterTableTest(unittest.TestCase):
    """
    Test parsing contents from a parameter table
    """
    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass
    
    def setUp(self):
        self.ip_table_factory = IntentParserTableFactory()
        self.parameter_fields = {
            'Flow cytometer configuration': 'measurement_info.flow_info',
            'Induction inducer': 'induction_info.induction_reagents.inducer',
            'Inoculation increment time 1': 'inoc_info.inc_time_1',
            'Inoculation media': 'inoc_info.inoculation_media',
            'Inoculation media volume': 'inoc_info.inoc_media_vol',
            'Inoculation volume': 'inoc_info.inoc_vol',
            'Kill switch': 'reagent_info.kill_switch',
            'Media well ids': 'exp_info.media_well_strings',
            'Plate reader gain': 'plate_reader_info.gain',
            'Sample has sbh_uri as an aliquot property': 'validate_samples'
        }

    def tearDown(self):
        pass
        
    def test_parameter_field_with_empty_value(self):
        ip_table = test_utils.create_fake_parameter()
        parameter = IntentParserCell()
        parameter.add_paragraph('Inoculation volume')
        data_row = test_utils.create_parameter_table_row(parameter_cell=parameter)
        ip_table.add_row(data_row)

        param_table = ParameterTable(ip_table, parameter_fields=self.parameter_fields)
        param_table.process_table()
        param_result = param_table.get_structured_request()
        self.assertEqual(0, len(param_result))
       
    def test_parameter_string_value_with_colon_separator(self):
        ip_table = test_utils.create_fake_parameter()
        parameter = IntentParserCell()
        parameter.add_paragraph('Inoculation volume')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('5 microliter')
        data_row = test_utils.create_parameter_table_row(parameter_cell=parameter, parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        param_table = ParameterTable(ip_table, parameter_fields=self.parameter_fields)
        param_table.process_table()
        param_result = param_table.get_structured_request()
        self.assertEqual(1, len(param_result))
        self.assertEqual('5:microliter', param_result['inoc_info.inoc_vol'])
    
    def test_parameter_string_value_with_list_of_numbers(self):
        ip_table = test_utils.create_fake_parameter()
        parameter = IntentParserCell()
        parameter.add_paragraph('Media well ids')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('94,95')
        data_row = test_utils.create_parameter_table_row(parameter_cell=parameter, parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        param_table = ParameterTable(ip_table, parameter_fields=self.parameter_fields)
        param_table.process_table()
        param_result = param_table.get_structured_request()
        self.assertEqual(1, len(param_result))
        self.assertEqual('94,95', param_result['exp_info.media_well_strings'])

    def test_one_parameter_string_value_without_colon_separator(self):
        ip_table = test_utils.create_fake_parameter()
        parameter = IntentParserCell()
        parameter.add_paragraph('Inoculation media')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('sc_media')
        data_row = test_utils.create_parameter_table_row(parameter_cell=parameter, parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        param_table = ParameterTable(ip_table, parameter_fields=self.parameter_fields)
        param_table.process_table()
        param_result = param_table.get_structured_request()
        self.assertEqual(1, len(param_result))
        self.assertEqual('sc_media', param_result['inoc_info.inoculation_media'])
    
    def test_two_parameter_string_value_without_colon_separator(self):
        ip_table = test_utils.create_fake_parameter()
        parameter = IntentParserCell()
        parameter.add_paragraph('Inoculation media')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('S750, Modified M9 Media')
        data_row = test_utils.create_parameter_table_row(parameter_cell=parameter, parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        param_table = ParameterTable(ip_table, parameter_fields=self.parameter_fields)
        param_table.process_table()
        param_result = param_table.get_structured_request()
        expected_result = {'inoc_info.inoculation_media.0': 'S750', 
                           'inoc_info.inoculation_media.1' : 'Modified M9 Media'}
        self.assertEqual(2, len(param_result))
        self.assertDictEqual(expected_result, param_result)
    
    def test_parameter_string_for_hardcoded_kill_switch_json_values(self):
        ip_table = test_utils.create_fake_parameter()
        parameter = IntentParserCell()
        parameter.add_paragraph('Kill switch')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('{"value": "false", "inputs": {"false": {}}}')
        data_row = test_utils.create_parameter_table_row(parameter_cell=parameter, parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        param_table = ParameterTable(ip_table, parameter_fields=self.parameter_fields)
        param_table.process_table()
        param_result = param_table.get_structured_request()
        self.assertEqual(1, len(param_result))
        expected_output = {
            "value": "false",
            "inputs": {
                "false": {}
            }
        }

        self.assertEqual(expected_output, param_result['reagent_info.kill_switch'])
    
    def test_parameter_string_for_hardcoded_measurement_info_flow_info_json_values(self):
        ip_table = test_utils.create_fake_parameter()
        parameter = IntentParserCell()
        parameter.add_paragraph('Flow cytometer configuration')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('{"do_flow": {"value": "every-sampling","inputs": {"every-sampling": {"flow_params" : "yeast"}}}}')
        data_row = test_utils.create_parameter_table_row(parameter_cell=parameter, parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        param_table = ParameterTable(ip_table, parameter_fields=self.parameter_fields)
        param_table.process_table()
        param_result = param_table.get_structured_request()
        self.assertEqual(1, len(param_result))
        expected_output = {
            "do_flow": {
                "value": "every-sampling",
                "inputs": {
                    "every-sampling": {
                        "flow_params" : "yeast"
                    }
                }
            }
        }

        self.assertEqual(expected_output, param_result['measurement_info.flow_info'])
        
    def test_parameter_string_for_hardcoded_induction_info_induction_reagents_inducer_json_values(self):
        ip_table = test_utils.create_fake_parameter()
        parameter = IntentParserCell()
        parameter.add_paragraph('Induction inducer')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('{"containerId" : "ct1e262bek47rkx","wellIndex" : 0}')
        data_row = test_utils.create_parameter_table_row(parameter_cell=parameter, parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        param_table = ParameterTable(ip_table, parameter_fields=self.parameter_fields)
        param_table.process_table()
        param_result = param_table.get_structured_request()
        self.assertEqual(1, len(param_result))
        expected_output = {
            "containerId": "ct1e262bek47rkx",
            "wellIndex": 0
        }
        self.assertEqual(expected_output, param_result['induction_info.induction_reagents.inducer'])
    
    def test_parameter_boolean_value(self):
        ip_table = test_utils.create_fake_parameter()
        parameter = IntentParserCell()
        parameter.add_paragraph('Sample has sbh_uri as an aliquot property')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('false')
        data_row = test_utils.create_parameter_table_row(parameter_cell=parameter, parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        param_table = ParameterTable(ip_table, parameter_fields=self.parameter_fields)
        param_table.process_table()
        param_result = param_table.get_structured_request()
        self.assertEqual(1, len(param_result))
        self.assertEqual(False, param_result['validate_samples'])
    
    def test_parameter_with_case_insensitive_boolean_value(self):
        ip_table = test_utils.create_fake_parameter()
        parameter = IntentParserCell()
        parameter.add_paragraph('Sample has sbh_uri as an aliquot property')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('FaLse')
        data_row = test_utils.create_parameter_table_row(parameter_cell=parameter, parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        param_table = ParameterTable(ip_table, parameter_fields=self.parameter_fields)
        param_table.process_table()
        param_result = param_table.get_structured_request()
        self.assertEqual(1, len(param_result))
        self.assertEqual(False, param_result['validate_samples'])
    
    def test_parameter_with_non_boolean_value(self):
        ip_table = test_utils.create_fake_parameter()
        parameter = IntentParserCell()
        parameter.add_paragraph('Sample has sbh_uri as an aliquot property')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('neither')
        data_row = test_utils.create_parameter_table_row(parameter_cell=parameter, parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        param_table = ParameterTable(ip_table, parameter_fields=self.parameter_fields)
        param_table.process_table()
        param_result = param_table.get_structured_request()
        self.assertEqual(0, len(param_result))
       
    def test_parameter_with_one_float_value(self):
        ip_table = test_utils.create_fake_parameter()
        parameter = IntentParserCell()
        parameter.add_paragraph('Plate reader gain')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('0.1')
        data_row = test_utils.create_parameter_table_row(parameter_cell=parameter, parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        param_table = ParameterTable(ip_table, parameter_fields=self.parameter_fields)
        param_table.process_table()
        param_result = param_table.get_structured_request()
        self.assertEqual(1, len(param_result))
        self.assertEqual(0.1, param_result['plate_reader_info.gain'])
    
    def test_parameter_with_three_float_values(self):
        ip_table = test_utils.create_fake_parameter()
        parameter = IntentParserCell()
        parameter.add_paragraph('Plate reader gain')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('0.1, 0.2, 0.3')
        data_row = test_utils.create_parameter_table_row(parameter_cell=parameter, parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        param_table = ParameterTable(ip_table, parameter_fields=self.parameter_fields)
        param_table.process_table()
        param_result = param_table.get_structured_request()
        expected_result = {'plate_reader_info.gain.0': 0.1, 
                           'plate_reader_info.gain.1': 0.2,
                           'plate_reader_info.gain.2': 0.3}
        self.assertEqual(3, len(param_result))
        self.assertDictEqual(expected_result, param_result)
 
if __name__ == "__main__":
    unittest.main()
