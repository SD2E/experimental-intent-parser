from intent_parser.intent_parser_exceptions import TableException
from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
from intent_parser.table.parameter_table import ParameterTable
import intent_parser.constants.intent_parser_constants as ip_constants
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
            'Sample has sbh_uri as an aliquot property': 'validate_samples',
            'Plate Size': ip_constants.PARAMETER_PLATE_SIZE,
            'Plate Number': ip_constants.PARAMETER_PLATE_NUMBER,
            'Container Search String': ip_constants.PARAMETER_CONTAINER_SEARCH_STRING,
            'Strain Property': ip_constants.PARAMETER_STRAIN_PROPERTY,
            'XPlan Path': ip_constants.PARAMETER_XPLAN_PATH,
            'Protocol ID': ip_constants.PARAMETER_PROTOCOL_ID,
            'Experiment reference url for xplan': ip_constants.PARAMETER_EXPERIMENT_REFERENCE_URL_FOR_XPLAN
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
                           'inoc_info.inoculation_media.1': 'Modified M9 Media'}
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

    def test_process_complete_experiment_data_from_parameter_table(self):
        ip_table = test_utils.create_fake_parameter()
        plate_size = IntentParserCell()
        plate_size.add_paragraph('Plate Size')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('96')
        data_row = test_utils.create_parameter_table_row(parameter_cell=plate_size,
                                                         parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        plate_number = IntentParserCell()
        plate_number.add_paragraph('Plate Number')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('2')
        data_row = test_utils.create_parameter_table_row(parameter_cell=plate_number,
                                                         parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        protocol_name = IntentParserCell()
        protocol_name.add_paragraph('Protocol')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('ObstacleCourse')
        data_row = test_utils.create_parameter_table_row(parameter_cell=protocol_name,
                                                         parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        container_search_string = IntentParserCell()
        container_search_string.add_paragraph('Container Search String')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('Ct1e3qc85mqwbz8, ct1e3qc85jc4gj52')
        data_row = test_utils.create_parameter_table_row(parameter_cell=container_search_string,
                                                         parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        strain_property = IntentParserCell()
        strain_property.add_paragraph('Strain Property')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('SD2_common_name')
        data_row = test_utils.create_parameter_table_row(parameter_cell=strain_property,
                                                         parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        xplan_path = IntentParserCell()
        xplan_path.add_paragraph('XPlan Path')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('path/foo/xplan_path')
        data_row = test_utils.create_parameter_table_row(parameter_cell=xplan_path,
                                                         parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        experiment_reference_url = IntentParserCell()
        experiment_reference_url.add_paragraph('Experiment reference url for xplan')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('path/foo/experiment_reference')
        data_row = test_utils.create_parameter_table_row(parameter_cell=experiment_reference_url,
                                                         parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        protocol_id = IntentParserCell()
        protocol_id.add_paragraph('Protocol ID')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('pr1e5gw8bdekdxv')
        data_row = test_utils.create_parameter_table_row(parameter_cell=protocol_id,
                                                         parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        deafult_params = IntentParserCell()
        deafult_params.add_paragraph('Inoculation volume')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('5 microliter')
        data_row = test_utils.create_parameter_table_row(parameter_cell=deafult_params,
                                                         parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        param_table = ParameterTable(ip_table, parameter_fields=self.parameter_fields)
        param_table.process_table()
        sr_result = param_table.get_structured_request()
        exp_result = param_table.get_experiment()
        expected_sr_result = {'inoc_info.inoc_vol': '5:microliter'}
        expected_experiment_result = {ip_constants.PARAMETER_XPLAN_REACTOR: 'xplan',
                           ip_constants.PARAMETER_PLATE_SIZE: 96,
                           ip_constants.PARAMETER_PROTOCOL: 'ObstacleCourse',
                           ip_constants.PARAMETER_PLATE_NUMBER: 2,
                           ip_constants.PARAMETER_CONTAINER_SEARCH_STRING: ['Ct1e3qc85mqwbz8', 'ct1e3qc85jc4gj52'],
                           ip_constants.PARAMETER_STRAIN_PROPERTY: 'SD2_common_name',
                           ip_constants.PARAMETER_XPLAN_PATH: 'path/foo/xplan_path',
                           ip_constants.PARAMETER_SUBMIT: False,
                           ip_constants.PARAMETER_PROTOCOL_ID: 'pr1e5gw8bdekdxv',
                           ip_constants.PARAMETER_TEST_MODE: True,
                           ip_constants.PARAMETER_EXPERIMENT_REFERENCE_URL_FOR_XPLAN: 'path/foo/experiment_reference',
                           ip_constants.DEFAULT_PARAMETERS: {'inoc_info.inoc_vol': '5:microliter'}}
        self.assertEqual(1, len(expected_sr_result))
        self.assertDictEqual(expected_sr_result, sr_result)

        self.assertEqual(12, len(expected_experiment_result))
        self.assertDictEqual(expected_experiment_result, exp_result)

    def test_process_incomplete_experiment_data_from_parameter_table(self):
        ip_table = test_utils.create_fake_parameter()
        plate_size = IntentParserCell()
        plate_size.add_paragraph('Plate Size')
        parameter_value = IntentParserCell()
        parameter_value.add_paragraph('96')
        data_row = test_utils.create_parameter_table_row(parameter_cell=plate_size,
                                                         parameter_value_cell=parameter_value)
        ip_table.add_row(data_row)

        param_table = ParameterTable(ip_table, parameter_fields=self.parameter_fields)
        param_table.process_table()
        with self.assertRaises(TableException):
            self.assertEqual(0, len(param_table.get_experiment()))

if __name__ == "__main__":
    unittest.main()
