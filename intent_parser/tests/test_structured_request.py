from intent_parser.intent_parser import IntentParser
from unittest.mock import patch
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


if __name__ == '__main__':
    unittest.main()
