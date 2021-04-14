from intent_parser.accessor.google_accessor import GoogleAccessor
from intent_parser.intent_parser_factory import IntentParserFactory
from intent_parser.accessor.sbol_dictionary_accessor import SBOLDictionaryAccessor
from datetime import datetime
from intent_parser.protocols.labs.aquarium_opil_accessor import AquariumOpilAccessor
from unittest.mock import patch
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.utils.intent_parser_utils as intent_parser_utils
import os
import json
import unittest

from intent_parser.protocols.lab_protocol_accessor import LabProtocolAccessor
from intent_parser.protocols.labs.strateos_accessor import StrateosAccessor
from intent_parser.protocols.templates.experimental_request_template import ExperimentalRequest
from intent_parser.table.table_processor.opil_processor import OpilProcessor


class JellyFishProtocolOutputTest(unittest.TestCase):

    @patch('intent_parser.accessor.intent_parser_sbh.IntentParserSBH')
    def setUp(self, mock_intent_parser_sbh):
        aquarium_accessor = AquariumOpilAccessor()
        strateos_accessor = StrateosAccessor()
        lab_protocol_accessor = LabProtocolAccessor(strateos_accessor, aquarium_accessor)
        self.opil_lab_template = lab_protocol_accessor.load_experimental_protocol_from_lab('High-Throughput Culturing',
                                                                                      ip_constants.LAB_DUKE_HASE)



    def test_size_of_load_experimental_request(self):
        experimental_request = ExperimentalRequest(ip_constants.AQUARIUM_NAMESPACE,
                                                        self.opil_lab_template,
                                                        'foo_id',
                                                        'IntentParserCopy_foo',
                                                        'https://docs.google.com/document/d/foo')
        experimental_request.load_experimental_request()
        self.assertEqual(1, len(experimental_request.opil_experimental_requests))

    def test_experimental_id_annotation(self):
        experimental_request = ExperimentalRequest(ip_constants.AQUARIUM_NAMESPACE,
                                                   self.opil_lab_template,
                                                   'foo_id',
                                                   'IntentParserCopy_foo',
                                                   'https://docs.google.com/document/d/foo')
        experimental_request.load_experimental_request()
        self.assertEqual('foo_id',
                         experimental_request.opil_experimental_requests[0].experiment_id)

    def test_experimental_reference_annotation(self):
        experimental_request = ExperimentalRequest(ip_constants.AQUARIUM_NAMESPACE,
                                                   self.opil_lab_template,
                                                   'foo_id',
                                                   'IntentParserCopy_foo',
                                                   'https://docs.google.com/document/d/foo')
        experimental_request.load_experimental_request()
        self.assertEqual('IntentParserCopy_foo',
                         experimental_request.opil_experimental_requests[0].experiment_reference)

    def test_experimental_reference_url_annotation(self):
        experimental_request = ExperimentalRequest(ip_constants.AQUARIUM_NAMESPACE,
                                                   self.opil_lab_template,
                                                   'foo_id',
                                                   'IntentParserCopy_foo',
                                                   'https://docs.google.com/document/d/foo')
        experimental_request.load_experimental_request()
        self.assertEqual('https://docs.google.com/document/d/foo',
                         experimental_request.opil_experimental_requests[0].experiment_reference_url)

    def test_size_of_load_sampleset_from_protocol_interface(self):
        experimental_request = ExperimentalRequest(ip_constants.AQUARIUM_NAMESPACE,
                                                   self.opil_lab_template,
                                                   'foo_id',
                                                   'IntentParserCopy_foo',
                                                   'https://docs.google.com/document/d/foo')
        experimental_request.load_sample_template_from_protocol_interface()
        self.assertEqual(1, len(experimental_request.opil_sample_sets))

    def test_size_of_load_sampleset_template_from_protocol_interface(self):
        experimental_request = ExperimentalRequest(ip_constants.AQUARIUM_NAMESPACE,
                                                   self.opil_lab_template,
                                                   'foo_id',
                                                   'IntentParserCopy_foo',
                                                   'https://docs.google.com/document/d/foo')
        experimental_request.load_sample_template_from_protocol_interface()
        self.assertIsNotNone(experimental_request.sample_template)
        self.assertEqual('http://aquarium.bio/htc_design',
                         experimental_request.sample_template.identity)



    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main()