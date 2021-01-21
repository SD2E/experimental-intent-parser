
from intent_parser.intent.measurement_intent import MeasurementIntent
import intent_parser.constants.intent_parser_constants as ip_constants
import unittest


class StructureRequestTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_measurement_with_measurement_type(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE)
        opil_measurement = measurement_intent.to_sbol_for_measurement()

        self.assertIsNotNone(opil_measurement.instance_of)
        # TODO: unable to call get methods from opil
        # actual_measurement_type = opil_measurement.instance_of
        # self.assertTrue(actual_measurement_type.required)

    def test_measurement_with_file_type(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.add_file_type('SPREADSHEET')
        opil_measurement = measurement_intent.to_sbol_for_measurement()

if __name__ == '__main__':
    unittest.main()
