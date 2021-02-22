from intent_parser.accessor.sbol_dictionary_accessor import SBOLDictionaryAccessor
from intent_parser.accessor.strateos_accessor import StrateosAccessor
from intent_parser.intent.measure_property_intent import TimepointIntent, ReagentIntent, NamedLink, MeasuredUnit
from intent_parser.intent.measurement_intent import MeasurementIntent, ContentIntent
from intent_parser.protocols.protocol_factory import ProtocolFactory
from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.table.table_processor.opil_processor import OPILProcessor
from intent_parser.utils.id_provider import IdProvider
from unittest.mock import patch
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.tests.test_util as test_utils
import unittest
import opil

class OpilTest(unittest.TestCase):

    @patch('intent_parser.accessor.intent_parser_sbh.IntentParserSBH')
    def setUp(self, mock_intent_parser_sbh):
        strateos_accesor = StrateosAccessor()
        protocol_factory = ProtocolFactory(strateos_accesor)
        protocol_factory.set_selected_lab(ip_constants.LAB_TRANSCRIPTIC)

        sbol_dictionary = SBOLDictionaryAccessor(ip_constants.SD2_SPREADSHEET_ID,
                                                      mock_intent_parser_sbh)
        sbol_dictionary.initial_fetch()

        self.opil_processor = OPILProcessor(protocol_factory,
                                            sbol_dictionary,
                                            file_types=['CSV'],
                                            lab_names=[ip_constants.LAB_TRANSCRIPTIC])
        self._id_provider = IdProvider()

    def tearDown(self):
        pass

    @unittest.skip("dictionary lookup failed for strains")
    def test_export_experiment_with_measurement_type(self):
        measurement_table = test_utils.create_fake_measurement_table()
        measurement_type = IntentParserCell()
        measurement_type.add_paragraph('PLATE_READER')
        data_row = test_utils.create_measurement_table_row(measurement_type_cell=measurement_type)
        measurement_table.add_row(data_row)
        self.opil_processor.process_intent(lab_tables=[self._create_transcriptic_lab_table()],
                                           measurement_tables=[measurement_table])
        opil_doc = self.opil_processor.get_intent()
        self.assertIsNotNone(opil_doc)

        self.assertEqual(1, len(opil_doc.objects))
        actual_experimental_request = opil_doc.objects[0]
        self.assertEqual('Experimental Result', actual_experimental_request.name)
        self.assertTrue(isinstance(actual_experimental_request, opil.ExperimentalRequest))

        self.assertEqual(1, len(actual_experimental_request.measurements))
        actual_measurement = actual_experimental_request.measurements[0]

    def test_measurement_type_to_opil(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type('PLATE_READER')
        opil_measurement, measurement_type = measurement_intent.to_opil()
        self.assertIsNotNone(measurement_type)
        self.assertTrue(measurement_type.required)
        self.assertEqual(ip_constants.NCIT_PLATE_READER_URI, measurement_type.type)
        self.assertTrue(opil_measurement.instance_of == measurement_type.identity)

    def test_file_type_size_1(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type('PLATE_READER')
        measurement_intent.add_file_type('CSV')
        opil_measurement, _ = measurement_intent.to_opil()
        self.assertIsNotNone(opil_measurement)
        self.assertEqual(['CSV'], opil_measurement.file_type)

    def test_file_type_size_3(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type('PLATE_READER')
        measurement_intent.add_file_type('CSV')
        measurement_intent.add_file_type('SPREADSHEET')
        measurement_intent.add_file_type('PDF')
        opil_measurement, _ = measurement_intent.to_opil()
        self.assertIsNotNone(opil_measurement)
        self.assertEqual(3, len(opil_measurement.file_type))
        self.assertEqual(['CSV', 'SPREADSHEET', 'PDF'], opil_measurement.file_type)

    def test_timepoint_to_opil(self):
        timepoint = TimepointIntent(12.0, 'hour')
        opil_timepoint = timepoint.to_opil()
        self.assertIsNotNone(opil_timepoint)
        self.assertEqual(opil_timepoint.value, 12.0)
        self.assertEqual(opil_timepoint.unit, ip_constants.NCIT_HOUR)

    def test_add_1_timepoint_to_measurement(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type('PLATE_READER')
        timepoint = TimepointIntent(12.0, 'hour')
        measurement_intent.add_timepoint(timepoint)

        opil_measurement, _ = measurement_intent.to_opil()
        self.assertIsNotNone(opil_measurement)
        self.assertEqual(1, len(opil_measurement.time))
        opil_measurement_time = opil_measurement.time[0]

        self.assertEqual(1, len(opil_measurement.time))
        opil_measurement_time = opil_measurement.time[0]
        expected_timepoint = timepoint.to_opil()

        self.assertEqual(opil_measurement_time.value, expected_timepoint.value)
        self.assertEqual(opil_measurement_time.value, 12.0)

        self.assertEqual(opil_measurement_time.unit, expected_timepoint.unit)
        self.assertEqual(opil_measurement_time.unit, ip_constants.NCIT_HOUR)
        self.assertEqual(opil_measurement_time.unit, expected_timepoint.unit)
        self.assertEqual(opil_measurement_time.unit, ip_constants.NCIT_HOUR)

    def test_reagent_to_opil_without_timepoint(self):
        reagent_name = NamedLink('M9', 'https://hub.sd2e.org/user/sd2e/design/M9/1')
        reagent = ReagentIntent(reagent_name)
        reagent_value = MeasuredUnit(10.0, 'uM')
        reagent.add_reagent_value(reagent_value)

        #TODO:
        reagent_doc = opil.Document()
        reagent_template, reagent_variable, reagent_component = reagent.to_sbol(reagent_doc)

    def _create_transcriptic_lab_table(self):
        lab_table = test_utils.create_fake_lab_table()
        lab_cell = IntentParserCell()
        lab_cell.add_paragraph('lab: Transcriptic')
        lab_table.add_row([lab_cell])
        return lab_table


if __name__ == '__main__':
    unittest.main()
