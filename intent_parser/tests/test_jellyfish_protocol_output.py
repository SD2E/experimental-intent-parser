from intent_parser.protocols.lab_protocol_accessor import LabProtocolAccessor
from intent_parser.protocols.labs.aquarium_opil_accessor import AquariumOpilAccessor
from intent_parser.protocols.labs.strateos_accessor import StrateosAccessor
from intent_parser.protocols.templates.experimental_request_template import ExperimentalRequest
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
from intent_parser.table.measurement_table import MeasurementTable
from unittest.mock import MagicMock, patch
import intent_parser.constants.intent_parser_constants as ip_constants
import unittest


class JellyFishProtocolOutputTest(unittest.TestCase):

    def setUp(self):
        aquarium_accessor = AquariumOpilAccessor()
        strateos_accessor = StrateosAccessor()
        lab_protocol_accessor = LabProtocolAccessor(strateos_accessor, aquarium_accessor)
        self.opil_lab_template = lab_protocol_accessor.load_protocol_interface_from_lab('High-Throughput Culturing',
                                                                                        ip_constants.LAB_DUKE_HASE)
        self.ip_table_factory = IntentParserTableFactory()

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

    def test_size_of_create_subcomponents_from_template(self):
        experimental_request = ExperimentalRequest(ip_constants.AQUARIUM_NAMESPACE,
                                                   self.opil_lab_template,
                                                   'foo_id',
                                                   'IntentParserCopy_foo',
                                                   'https://docs.google.com/document/d/foo')
        measurement_table = MeasurementTable(self._create_dummy_measurement_table())
        measurement_table.process_table()
        experimental_request.load_from_measurement_table(measurement_table)
        experimental_request.load_sample_template_from_protocol_interface()
        experimental_request.create_subcomponents_from_template()
        self.assertEqual(4, len(experimental_request.sample_template.features))

    def test_subcomponent_names(self):
        experimental_request = ExperimentalRequest(ip_constants.AQUARIUM_NAMESPACE,
                                                   self.opil_lab_template,
                                                   'foo_id',
                                                   'IntentParserCopy_foo',
                                                   'https://docs.google.com/document/d/foo')
        measurement_table = MeasurementTable(self._create_dummy_measurement_table())
        measurement_table.process_table()
        experimental_request.load_from_measurement_table(measurement_table)
        experimental_request.load_sample_template_from_protocol_interface()
        experimental_request.create_subcomponents_from_template()
        expected_subcomponent_names = ['Antibiotic', 'Inducer', 'Media', 'Strain']
        for feature in experimental_request.sample_template.features:
            self.assertTrue(feature.name in expected_subcomponent_names)

    def test_size_of_sample_sets(self):
        experimental_request = ExperimentalRequest(ip_constants.AQUARIUM_NAMESPACE,
                                                   self.opil_lab_template,
                                                   'foo_id',
                                                   'IntentParserCopy_foo',
                                                   'https://docs.google.com/document/d/foo')
        measurement_table = MeasurementTable(self._create_dummy_measurement_table())
        measurement_table.process_table()
        experimental_request.load_from_measurement_table(measurement_table)
        experimental_request.load_sample_template_from_protocol_interface()
        experimental_request.create_subcomponents_from_template()
        experimental_request.load_sample_set(len(measurement_table.get_intents()))
        self.assertEqual(2, len(experimental_request.opil_sample_sets))

    def test_for_original_sample_set_by_identity(self):
        experimental_request = ExperimentalRequest(ip_constants.AQUARIUM_NAMESPACE,
                                                   self.opil_lab_template,
                                                   'foo_id',
                                                   'IntentParserCopy_foo',
                                                   'https://docs.google.com/document/d/foo')
        measurement_table = MeasurementTable(self._create_dummy_measurement_table())
        measurement_table.process_table()
        experimental_request.load_from_measurement_table(measurement_table)
        experimental_request.load_sample_template_from_protocol_interface()
        experimental_request.create_subcomponents_from_template()
        experimental_request.load_sample_set(len(measurement_table.get_intents()))
        actual_sample_set_identities = [sample.identity for sample in experimental_request.opil_sample_sets]
        self.assertTrue('http://aquarium.bio/culture_conditions' in actual_sample_set_identities)

    def test_size_of_add_variable_features_from_measurement_intents(self):
        experimental_request = ExperimentalRequest(ip_constants.AQUARIUM_NAMESPACE,
                                                   self.opil_lab_template,
                                                   'foo_id',
                                                   'IntentParserCopy_foo',
                                                   'https://docs.google.com/document/d/foo')
        measurement_table = MeasurementTable(self._create_dummy_measurement_table())
        measurement_table.process_table()
        experimental_request.load_from_measurement_table(measurement_table)
        experimental_request.load_sample_template_from_protocol_interface()
        experimental_request.create_subcomponents_from_template()
        experimental_request.load_sample_set(len(measurement_table.get_intents()))
        experimental_request.add_variable_features_from_measurement_intents(measurement_table.get_intents())
        self.assertEqual(2, len(experimental_request.opil_sample_sets))
        sample_set1 = experimental_request.opil_sample_sets[0]
        sample_set2 = experimental_request.opil_sample_sets[1]
        self.assertEqual(3, len(sample_set1.variable_features))
        self.assertEqual(3, len(sample_set2.variable_features))


    def _create_dummy_measurement_table(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                                'content': 'measurement-type'}}]}}]},
                            {'content': [{'paragraph': {'elements': [{'textRun': {
                                'content': 'Strains'}}]}}]},
                            {'content': [{'paragraph': {'elements': [{'textRun': {
                                'content': 'Inducer'}}]}}]},
                            {'content': [{'paragraph': {'elements': [{'textRun': {
                                'content': 'Media'}}]}}]},
                            {'content': [{'paragraph': {'elements': [{'textRun': {
                                'content': 'Antibiotic'}}]}}]}
            ]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'FLOW'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'NOR00',
                    'textStyle': {'link': {'url': 'https://hub.sd2e.org/user/sd2e/design/UWBF_6390/1'}}}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': '-1.0'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'Sytox'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': '-1.0'}}]}}]}
            ]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'FLOW'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'NOR00',
                    'textStyle': {'link': {'url': 'https://hub.sd2e.org/user/sd2e/design/UWBF_6390/1'}}}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': '-1.0'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': 'Sytox'}}]}}]},
                {'content': [{'paragraph': {'elements': [{'textRun': {
                    'content': '-1.0'}}]}}]}
            ]}
        ]
        }
        ip_table = self.ip_table_factory.from_google_doc({'table': input_table,
                                                          'startIndex': 0,
                                                          'endIndex': 100})
        return ip_table


    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main()