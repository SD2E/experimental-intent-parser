from intent_parser.intent_parser import IntentParser
from intent_parser.intent.control_intent import ControlIntent
from intent_parser.intent.measurement_intent import MeasurementIntent, TemperatureIntent, TimepointIntent, \
    ContentIntent, NamedIntegerValue, NamedLink, ReagentIntent
from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.intent.strain_intent import StrainIntent
from unittest.mock import patch
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import json
import os
import unittest

class StructureRequestTest(unittest.TestCase):

    @patch('intent_parser.lab_experiment.LabExperiment')
    @patch('intent_parser.accessor.sbol_dictionary_accessor.SBOLDictionaryAccessor')
    @patch('intent_parser.accessor.intent_parser_sbh.IntentParserSBH')
    def setUp(self, mock_intent_parser_sbh, mock_sbol_dictionary_accessor, mock_lab_experiment):
        self.mock_intent_parser_sbh = mock_intent_parser_sbh
        self.mock_sbol_dictionary_accessor = mock_sbol_dictionary_accessor
        self.mock_lab_experiment = mock_lab_experiment

        curr_path = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(curr_path, 'data')
        with open(os.path.join(self.data_dir, 'authn.json'), 'r') as file:
            self.authn = json.load(file)['authn']
        self.datacatalog_config = {"mongodb": {"database": "catalog_staging", "authn": self.authn}}

    def tearDown(self):
        pass

    def test_undefined_challenge_problem(self):

        self.mock_lab_experiment.document_id.return_value = 'foo_doc_id'
        self.mock_lab_experiment.title.return_value = 'CP-Request-DB-Test'
        self.mock_lab_experiment.head_revision.return_value = 'mock_head_revision'
        measurement_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'file-type\n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'measurement-type\n'}}]}}]}
            ]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'CSV'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'RNA_SEQ'}}]}}]}
            ]}]
        }
        self.mock_lab_experiment.tables.return_value = [{'table': measurement_table,
                                                         'startIndex': 0,
                                                         'endIndex': 100}]
        ip = IntentParser(self.mock_lab_experiment,
                          self.datacatalog_config,
                          self.mock_intent_parser_sbh,
                          self.mock_sbol_dictionary_accessor)
        ip.process_structure_request()
        actual_sr = ip.get_structured_request()
        self.assertEqual(dc_constants.UNDEFINED, actual_sr[dc_constants.CHALLENGE_PROBLEM])
        errors = ip.get_validation_errors()
        self.assertTrue('Failed to map challenge problem for doc id foo_doc_id! Check that this document is in the Challenge Problem folder under DARPA SD2E Shared > CP Working Groups > ExperimentalRequests' in errors)

    def test_unknown_experiment_reference(self):
        self.mock_lab_experiment.tables.return_value = {}
        self.mock_lab_experiment.document_id.return_value = 'foo_doc_id'
        self.mock_lab_experiment.title.return_value = 'CP-Request-DB-Test'
        self.mock_lab_experiment.head_revision.return_value = 'mock_head_revision'
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'file-type\n'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'measurement-type\n'}}]}}]}
            ]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'CSV'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'RNA_SEQ'}}]}}]}
            ]}]
        }
        self.mock_lab_experiment.tables.return_value = [{'table': input_table,
                                                         'startIndex': 0,
                                                         'endIndex': 100}]
        ip = IntentParser(self.mock_lab_experiment,
                          self.datacatalog_config,
                          self.mock_intent_parser_sbh,
                          self.mock_sbol_dictionary_accessor)
        ip.process_structure_request()
        actual_sr = ip.get_structured_request()
        self.assertEqual(dc_constants.UNKOWN, actual_sr[dc_constants.EXPERIMENT_REFERENCE])
        errors = ip.get_validation_errors()
        self.assertTrue('Failed to map experiment reference for doc id foo_doc_id!' in errors)

    def test_challenge_problem(self):
        self.mock_lab_experiment.tables.return_value = {}
        self.mock_lab_experiment.document_id.return_value = '1zf9l0K4rj7I08ZRpxV2ZY54RMMQc15Rlg7ULviJ7SBQ'
        ip = IntentParser(self.mock_lab_experiment,
                          self.datacatalog_config,
                          self.mock_intent_parser_sbh,
                          self.mock_sbol_dictionary_accessor)
        ip.process_structure_request()
        actual_sr = ip.get_structured_request()
        self.assertEqual('INTENT_PARSER_TEST', actual_sr[dc_constants.CHALLENGE_PROBLEM])

    def test_experiment_reference(self):
        self.mock_lab_experiment.tables.return_value = {}
        self.mock_lab_experiment.document_id.return_value = '1sM6wz4s7K5DpPupz8Jn5RFW1ETkP91_zLpBCJPP7HC8'
        ip = IntentParser(self.mock_lab_experiment,
                          self.datacatalog_config,
                          self.mock_intent_parser_sbh,
                          self.mock_sbol_dictionary_accessor)
        ip.process_structure_request()
        actual_sr = ip.get_structured_request()
        self.assertEqual('IntentParserCopy-of-TEST-Playing-with-Intent-Parser', actual_sr[dc_constants.EXPERIMENT_REFERENCE])

    def test_measurement_with_missing_file_type(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE)
        with self.assertRaises(IntentParserException):
            measurement_intent.to_structure_request()

    def test_measurement_with_missing_measurement_type(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.add_file_type('SPREADSHEET')
        with self.assertRaises(IntentParserException):
            measurement_intent.to_structure_request()

    def test_measurement_with_file_type_and_measurement_type(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE)
        measurement_intent.add_file_type('SPREADSHEET')
        self.assertEqual({dc_constants.MEASUREMENT_TYPE: ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE,
                          dc_constants.FILE_TYPE: ['SPREADSHEET']},
                         measurement_intent.to_structure_request())

    def test_measurement_with_replicate_size_1(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE)
        measurement_intent.add_file_type('SPREADSHEET')
        measurement_intent.add_replicate(5)
        self.assertEqual({dc_constants.MEASUREMENT_TYPE: ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE,
                          dc_constants.FILE_TYPE: ['SPREADSHEET'],
                          dc_constants.REPLICATES: [5]},
                         measurement_intent.to_structure_request())

    def test_measurement_with_replicate_size_3(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE)
        measurement_intent.add_file_type('SPREADSHEET')
        measurement_intent.add_replicate(5)
        measurement_intent.add_replicate(10)
        measurement_intent.add_replicate(15)
        self.assertEqual({dc_constants.MEASUREMENT_TYPE: ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE,
                          dc_constants.FILE_TYPE: ['SPREADSHEET'],
                          dc_constants.REPLICATES: [5, 10, 15]},
                         measurement_intent.to_structure_request())

    def test_measurement_with_strain_size_1(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE)
        measurement_intent.add_file_type('SPREADSHEET')

        strain = StrainIntent('www.synbiohub.org/example/strain',
                              'my_lab',
                              'my_strain',
                              lab_strain_names=['and_00', 'and_gate'])
        strain.set_selected_strain('and_00')
        measurement_intent.add_strain(strain)

        strain_structure_request = {dc_constants.SBH_URI: 'www.synbiohub.org/example/strain',
                                    dc_constants.LABEL: 'my_strain',
                                    dc_constants.LAB_ID: 'name.my_lab.and_00'}
        self.assertEqual({dc_constants.MEASUREMENT_TYPE: ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE,
                          dc_constants.FILE_TYPE: ['SPREADSHEET'],
                          dc_constants.STRAINS: [strain_structure_request]},
                         measurement_intent.to_structure_request())

    def test_measurement_with_strain_size_2(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE)
        measurement_intent.add_file_type('SPREADSHEET')

        strain1 = StrainIntent('www.synbiohub.org/example/and_strain',
                              'my_lab',
                              'and_strain',
                              lab_strain_names=['and_00', 'and_gate'])
        strain1.set_selected_strain('and_00')
        measurement_intent.add_strain(strain1)

        strain2 = StrainIntent('www.synbiohub.org/example/or_strain',
                               'my_lab',
                               'or_strain',
                               lab_strain_names=['or_00', 'or_gate'])
        strain2.set_selected_strain('or_gate')
        measurement_intent.add_strain(strain2)

        strain_structure_request = [{dc_constants.SBH_URI: 'www.synbiohub.org/example/and_strain',
                                    dc_constants.LABEL: 'and_strain',
                                    dc_constants.LAB_ID: 'name.my_lab.and_00'},
                                    {dc_constants.SBH_URI: 'www.synbiohub.org/example/or_strain',
                                     dc_constants.LABEL: 'or_strain',
                                     dc_constants.LAB_ID: 'name.my_lab.or_gate'}
                                    ]
        self.assertEqual({dc_constants.MEASUREMENT_TYPE: ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE,
                          dc_constants.FILE_TYPE: ['SPREADSHEET'],
                          dc_constants.STRAINS: strain_structure_request},
                         measurement_intent.to_structure_request())

    def test_measurement_with_ods_size_1(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE)
        measurement_intent.add_file_type('SPREADSHEET')
        measurement_intent.add_optical_density(3.0)
        self.assertEqual({dc_constants.MEASUREMENT_TYPE: ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE,
                          dc_constants.FILE_TYPE: ['SPREADSHEET'],
                          dc_constants.ODS: [3.0]},
                         measurement_intent.to_structure_request())

    def test_measurement_with_temperature_size_1(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE)
        measurement_intent.add_file_type('SPREADSHEET')
        temperature = TemperatureIntent(75.0, 'fahrenheit')
        measurement_intent.add_temperature(temperature)

        temperature_structure_request = {dc_constants.VALUE: 75.0,
                                         dc_constants.UNIT: 'fahrenheit'}
        self.assertEqual({dc_constants.MEASUREMENT_TYPE: ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE,
                          dc_constants.FILE_TYPE: ['SPREADSHEET'],
                          dc_constants.TEMPERATURES: [temperature_structure_request]},
                         measurement_intent.to_structure_request())


    def test_measurement_with_timepoint_size_1(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE)
        measurement_intent.add_file_type('SPREADSHEET')

        timepoint = TimepointIntent(12.0, 'hour')
        measurement_intent.add_timepoint(timepoint)

        timepoint_structure_request = {dc_constants.VALUE: 12.0,
                                       dc_constants.UNIT: 'hour'}
        self.assertEqual({dc_constants.MEASUREMENT_TYPE: ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE,
                          dc_constants.FILE_TYPE: ['SPREADSHEET'],
                          dc_constants.TIMEPOINTS: [timepoint_structure_request]},
                         measurement_intent.to_structure_request())

    def test_measurement_with_batches_size_1(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE)
        measurement_intent.add_file_type('SPREADSHEET')
        measurement_intent.add_batch(5)

        self.assertEqual({dc_constants.MEASUREMENT_TYPE: ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE,
                          dc_constants.FILE_TYPE: ['SPREADSHEET'],
                          dc_constants.BATCH: [5]},
                         measurement_intent.to_structure_request())

    def test_measurement_with_control_type(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE)
        measurement_intent.add_file_type('SPREADSHEET')

        control = ControlIntent()
        control.set_control_type('HIGH_FITC')
        measurement_intent.add_control(control)

        control_structure_request = {dc_constants.TYPE: 'HIGH_FITC'}
        self.assertEqual({dc_constants.MEASUREMENT_TYPE: ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE,
                          dc_constants.FILE_TYPE: ['SPREADSHEET'],
                          dc_constants.CONTROLS: [control_structure_request]},
                         measurement_intent.to_structure_request())

    def test_measurement_with_neg_control_content_size_1(self):
        measurement_intent = MeasurementIntent()
        measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE)
        measurement_intent.add_file_type('SPREADSHEET')

        content = ContentIntent()
        num_neg_control = NamedIntegerValue(NamedLink(ip_constants.HEADER_NUMBER_OF_NEGATIVE_CONTROLS_VALUE), 2)
        content.set_numbers_of_negative_controls([num_neg_control])
        measurement_intent.add_content(content)

        content_structure_request = [{dc_constants.NAME: {dc_constants.LABEL: ip_constants.HEADER_NUMBER_OF_NEGATIVE_CONTROLS_VALUE,
                                                          dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
                                      dc_constants.VALUE: 2}]
        self.assertDictEqual({dc_constants.CONTENTS: [content_structure_request],
                              dc_constants.FILE_TYPE: ['SPREADSHEET'],
                              dc_constants.MEASUREMENT_TYPE: ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE},
                             measurement_intent.to_structure_request())

    def test_control_with_control_type(self):
        control_intent = ControlIntent()
        control_intent.set_control_type('EMPTY_VECTOR')
        self.assertEqual({dc_constants.TYPE: 'EMPTY_VECTOR'},
                         control_intent.to_structure_request())

    def test_control_with_strains_size_1(self):
        control_intent = ControlIntent()
        control_intent.set_control_type('EMPTY_VECTOR')
        strain = StrainIntent('www.synbiohub.org/example/strain',
                              'my_lab',
                              'my_strain',
                              lab_strain_names=['and_00', 'and_gate'])
        strain.set_selected_strain('and_00')
        control_intent.add_strain(strain)

        strain_structure_request = {dc_constants.SBH_URI: 'www.synbiohub.org/example/strain',
                                    dc_constants.LABEL: 'my_strain',
                                    dc_constants.LAB_ID: 'name.my_lab.and_00'}
        self.assertEqual({dc_constants.TYPE: 'EMPTY_VECTOR',
                          dc_constants.STRAINS: [strain_structure_request]},
                         control_intent.to_structure_request())

    def test_control_with_channel_size_1(self):
        control_intent = ControlIntent()
        control_intent.set_control_type('EMPTY_VECTOR')
        control_intent.set_channel('BL1-A')

        self.assertEqual({dc_constants.TYPE: 'EMPTY_VECTOR',
                          dc_constants.CHANNEL: 'BL1-A'},
                         control_intent.to_structure_request())

    def test_control_with_content_size_1(self):
        control_intent = ControlIntent()
        control_intent.set_control_type('EMPTY_VECTOR')
        content = ReagentIntent(NamedLink('beta_estradiol'), 0.05, 'micromole')
        control_intent.add_content(content)

        content_structure_request ={dc_constants.NAME: {dc_constants.LABEL: 'beta_estradiol',
                                                        dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
                                    dc_constants.VALUE: '0.05',
                                    dc_constants.UNIT: 'micromole'}
        self.assertEqual({dc_constants.TYPE: 'EMPTY_VECTOR',
                          dc_constants.CONTENTS: [content_structure_request]},
                         control_intent.to_structure_request())

    def test_control_with_timepoint_size_1(self):
        control_intent = ControlIntent()
        control_intent.set_control_type('EMPTY_VECTOR')

        timepoint = TimepointIntent(12.0, 'hour')
        control_intent.add_timepoint(timepoint)

        timepoint_structure_request = {dc_constants.VALUE: 12.0,
                                       dc_constants.UNIT: 'hour'}

        self.assertEqual({dc_constants.TYPE: 'EMPTY_VECTOR',
                          dc_constants.TIMEPOINTS: [timepoint_structure_request]},
                         control_intent.to_structure_request())

if __name__ == '__main__':
    unittest.main()
