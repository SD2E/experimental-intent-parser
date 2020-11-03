from intent_parser.accessor.strateos_accessor import StrateosAccessor
import intent_parser.protocols.opil_parameter_utils as opil_util
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.utils.intent_parser_utils as ip_utils
import unittest

class StrateosAccessorTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def setup(self):
        self.maxDiff = None

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_time_series_protocol(self):
        self.maxDiff = None
        strateos_accessor = StrateosAccessor()
        protocol = strateos_accessor.get_protocol_as_schema(ip_constants.TIME_SERIES_HTP_PROTOCOL)
        ip_parameters = strateos_accessor.convert_protocol_to_ip_parameters(protocol['inputs'])
        expected_names = list(ip_parameters.keys())

        protocol_interface, sbol_doc = strateos_accessor.convert_protocol_to_opil(protocol)
        parameters = opil_util.get_parameters_from_protocol_interface(protocol_interface)
        actual_names = [parameter.name for parameter in parameters]
        mismatched_opil_names = []
        mismatched_ip_names = []
        for item in actual_names:
            if item not in expected_names:
                mismatched_opil_names.append(item)

        for item in expected_names:
            if item not in actual_names:
                mismatched_ip_names.append(item)
        ip_utils.write_json_to_file({'ip_names': expected_names,
                                     'opil_names': actual_names,
                                     'opil_only_names': mismatched_opil_names,
                                     'ip_only_names': mismatched_ip_names},
                                    'time_series_names.json')
        self.assertEqual(len(expected_names), len(actual_names))
        self.assertTrue(expected_names == actual_names)

    def test_obstacle_course_protocol(self):
        self.maxDiff = None
        strateos_accessor = StrateosAccessor()
        protocol = strateos_accessor.get_protocol_as_schema(ip_constants.OBSTACLE_COURSE_PROTOCOL)
        ip_parameters = strateos_accessor.convert_protocol_to_ip_parameters(protocol['inputs'])
        expected_names = list(ip_parameters.keys())

        protocol_interface, sbol_doc = strateos_accessor.convert_protocol_to_opil(protocol)
        parameters = opil_util.get_parameters_from_protocol_interface(protocol_interface)
        actual_names = [parameter.name for parameter in parameters]
        mismatched_opil_names = []
        mismatched_ip_names = []
        for item in actual_names:
            if item not in expected_names:
                mismatched_opil_names.append(item)

        for item in expected_names:
            if item not in actual_names:
                mismatched_ip_names.append(item)
        ip_utils.write_json_to_file({'ip_names': expected_names,
                                     'opil_names': actual_names,
                                     'opil_only_names': mismatched_opil_names,
                                     'ip_only_names': mismatched_ip_names},
                                    'obstacle_course_names.json')
        self.assertEqual(len(expected_names), len(actual_names))
        self.assertTrue(expected_names == actual_names)

    def test_growth_curve_protocol(self):
        self.maxDiff = None
        strateos_accessor = StrateosAccessor()
        protocol = strateos_accessor.get_protocol_as_schema(ip_constants.GROWTH_CURVE_PROTOCOL)
        ip_parameters = strateos_accessor.convert_protocol_to_ip_parameters(protocol['inputs'])
        expected_names = list(ip_parameters.keys())

        protocol_interface, sbol_doc = strateos_accessor.convert_protocol_to_opil(protocol)
        parameters = opil_util.get_parameters_from_protocol_interface(protocol_interface)
        actual_names = [parameter.name for parameter in parameters]
        mismatched_opil_names = []
        mismatched_ip_names = []
        for item in actual_names:
            if item not in expected_names:
                mismatched_opil_names.append(item)

        for item in expected_names:
            if item not in actual_names:
                mismatched_ip_names.append(item)
        ip_utils.write_json_to_file({'ip_names': expected_names,
                                     'opil_names': actual_names,
                                     'opil_only_names': mismatched_opil_names,
                                     'ip_only_names': mismatched_ip_names},
                                    'growth_curve_names.json')
        self.assertEqual(len(expected_names), len(actual_names))
        self.assertTrue(expected_names == actual_names)

    def test_cell_free_bioswitches_protocol(self):
        self.maxDiff = None
        strateos_accessor = StrateosAccessor()
        protocol = strateos_accessor.get_protocol_as_schema(ip_constants.CELL_FREE_RIBO_SWITCH_PROTOCOL)
        ip_parameters = strateos_accessor.convert_protocol_to_ip_parameters(protocol['inputs'])
        expected_names = list(ip_parameters.keys())

        protocol_interface, sbol_doc = strateos_accessor.convert_protocol_to_opil(protocol)
        parameters = opil_util.get_parameters_from_protocol_interface(protocol_interface)
        actual_names = [parameter.name for parameter in parameters]
        mismatched_opil_names = []
        mismatched_ip_names = []
        for item in actual_names:
            if item not in expected_names:
                mismatched_opil_names.append(item)

        for item in expected_names:
            if item not in actual_names:
                mismatched_ip_names.append(item)
        ip_utils.write_json_to_file({'ip_names': expected_names,
                                     'opil_names': actual_names,
                                     'opil_only_names': mismatched_opil_names,
                                     'ip_only_names': mismatched_ip_names},
                                    'cell_free_bioswitches_names.json')
        self.assertEqual(len(expected_names), len(actual_names))
        self.assertTrue(expected_names == actual_names)


if __name__ == "__main__":
    unittest.main()
