from http import HTTPStatus
from intent_parser.server.http_message import HttpMessage
from intent_parser.server.intent_parser_server import IntentParserServer
from unittest.mock import Mock, patch
import intent_parser.constants.ip_app_script_constants as addon_constants
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.utils.intent_parser_view as intent_parser_view
import json
import unittest

class IntentParserServerTest(unittest.TestCase):
    """
    Test IntentParserServer response for different requests made to the server. 
    """

    @patch('intent_parser.accessor.mongo_db_accessor.TA4DBAccessor')
    @patch('intent_parser.accessor.tacc_go_accessor.TACCGoAccessor')
    @patch('intent_parser.intent_parser_factory.IntentParserFactory')
    @patch('intent_parser.accessor.strateos_accessor.StrateosAccessor')
    @patch('intent_parser.accessor.sbol_dictionary_accessor.SBOLDictionaryAccessor')
    @patch('intent_parser.intent_parser_sbh.IntentParserSBH')
    def setUp(self, mock_intent_parser_sbh,
              mock_sbol_dictionary_accessor,
              mock_strateos_accessor,
              mock_intent_parser_factory,
              mock_tacc_go_accessor,
              mock_ta4_db_accessor):
        self.mock_intent_parser_sbh = mock_intent_parser_sbh
        self.mock_sbol_dictionary_accessor = mock_sbol_dictionary_accessor
        self.mock_strateos_accessor = mock_strateos_accessor
        self.mock_intent_parser_factory = mock_intent_parser_factory
        self.mock_tacc_go_accessor = mock_tacc_go_accessor
        self.mock_ta4_db_accessor = mock_ta4_db_accessor
        self.mock_intent_parser = Mock()
        self.mock_intent_parser_factory.create_intent_parser.return_value = self.mock_intent_parser
        self.ip_server = IntentParserServer(self.mock_intent_parser_sbh,
                                            self.mock_sbol_dictionary_accessor,
                                            self.mock_strateos_accessor,
                                            self.mock_intent_parser_factory,
                                            bind_ip='localhost', bind_port=8081)
    
    def tearDown(self):
        pass

    def test_process_execute_experiment(self):
        http_host = 'fake_host'
        http_message = HttpMessage()
        http_message.process_header('Host:%s' % http_host)
        document_id = 'foo'
        expected_response = 'The request was successful'
        experiment_request = {'documentId': document_id}
        expected_actions = {'actions': [intent_parser_view.message_dialog('Experiment Execution Status', expected_response)]}
        self.mock_intent_parser.get_experiment_request.return_value = experiment_request
        self.mock_intent_parser.get_validation_warnings.return_value = []
        self.mock_intent_parser.get_validation_errors.return_value = []
        self.mock_tacc_go_accessor.execute_experiment.return_value = "The request was successful"
        http_message.set_body(json.dumps(experiment_request).encode('utf-8'))

        response = self.ip_server.process_execute_experiment(http_message)
        self._verify_response_status(response, HTTPStatus.OK)
        self._verify_response_body(response, expected_actions)

    def test_process_run_experiment(self):
        test_data = {ip_constants.PARAMETER_XPLAN_REACTOR: 'xplan',
                             ip_constants.PARAMETER_PLATE_SIZE: 96,
                             ip_constants.PARAMETER_PROTOCOL: ip_constants.OBSTACLE_COURSE_PROTOCOL,
                             ip_constants.PARAMETER_PLATE_NUMBER: 2,
                             ip_constants.PARAMETER_CONTAINER_SEARCH_STRING: ['ct1e3qc85mqwbz8', 'ct1e3qc85jc4gj5'],
                             ip_constants.PARAMETER_STRAIN_PROPERTY: 'SD2_common_name',
                             ip_constants.PARAMETER_XPLAN_PATH: 'data-sd2e-projects.sd2e-project-14/xplan-reactor/NOVEL_CHASSIS/experiments',
                             ip_constants.PARAMETER_SUBMIT: True,
                             ip_constants.PARAMETER_PROTOCOL_ID: 'pr1e5gw8bdekdxv',
                             ip_constants.PARAMETER_TEST_MODE: False,
                             ip_constants.PARAMETER_EXPERIMENT_REFERENCE_URL_FOR_XPLAN: 'foo',
                             ip_constants.DEFAULT_PARAMETERS: {'exp_info.sample_time': '8:hour'}}
        self.mock_intent_parser.get_experiment_request.return_value = test_data
        expected_message = 'The request was successful'
        self.mock_tacc_go_accessor.execute_experiment.return_value = expected_message
        self.mock_intent_parser.get_validation_warnings.return_value = []
        self.mock_intent_parser.get_validation_errors.return_value = []

        http_message = HttpMessage()
        http_message.resource = '/run_experiment?foo'
        response = self.ip_server.process_run_experiment(http_message)
        self._verify_response_status(response, HTTPStatus.OK)
        self._verify_response_body(response, {'result': expected_message})

    def test_process_document_report(self):
        expected_report = {'challenge_problem_id': 'undefined',
                            'experiment_reference_url': 'foo',
                            'labs': [],
                            'mapped_names': {'label': 'iptg', 'sbh_url': 'url'}}
        self.mock_intent_parser.generate_report.return_value = expected_report
    
        http_message = HttpMessage()
        http_message.resource = '/document_report?foo'
        response = self.ip_server.process_document_report(http_message)
        self._verify_response_status(response, HTTPStatus.OK)
        self._verify_response_body(response, expected_report)
    
    def test_process_document_request_ok(self):
        expected_structured_request = {'foo': 'bar'}
        self.mock_intent_parser.get_structured_request.return_value = expected_structured_request
        self.mock_intent_parser.get_validation_errors.return_value = []
        
        http_message = HttpMessage()
        http_message.resource = '/document_request?foo'
        
        response = self.ip_server.process_document_request(http_message)
        self._verify_response_status(response, HTTPStatus.OK)
        self._verify_response_body(response, expected_structured_request)

    def test_process_document_request_validation_errors(self):
        expected_validation_errors = {'errors': ['error1', 'error2', 'error3']}
        self.mock_intent_parser.get_validation_errors.return_value = expected_validation_errors['errors']
        
        http_message = HttpMessage()
        http_message.resource = '/document_request?foo'
        
        response = self.ip_server.process_document_request(http_message)
        self._verify_response_status(response, HTTPStatus.BAD_REQUEST)
        self._verify_response_body(response, expected_validation_errors)
        
    def test_process_calculate_samples(self):
        calculate_samples = {'documentId': 'foo'}
        expected_actions = {'actions': [calculate_samples]}
        self.mock_intent_parser.calculate_samples.return_value = calculate_samples
        
        http_message = HttpMessage()
        http_message.set_body(json.dumps(calculate_samples).encode('utf-8'))
        
        response = self.ip_server.process_calculate_samples(http_message)
        self._verify_response_status(response, HTTPStatus.OK)
        self._verify_response_body(response, expected_actions)
        
    def test_process_update_exp_results(self):
        experimental_results = {'documentId': 'foo'}
        expected_actions = {'actions': [experimental_results]}
        self.mock_intent_parser.update_experimental_results.return_value = experimental_results
        
        http_message = HttpMessage()
        http_message.set_body(json.dumps(experimental_results).encode('utf-8'))
        
        response = self.ip_server.process_update_exp_results(http_message)
        self._verify_response_status(response, HTTPStatus.OK)
        self._verify_response_body(response, expected_actions)
    
    def test_process_validate_structured_request(self):
        structured_request = {'documentId': 'foo'}
        warnings = []
        errors = []
        
        expected_actions = {'actions': [intent_parser_view.valid_request_model_dialog(warnings)]}
        self.mock_intent_parser.process_structure_request.return_value = structured_request
        self.mock_intent_parser.get_validation_warnings.return_value = warnings
        self.mock_intent_parser.get_validation_errors.return_value = errors 
        http_message = HttpMessage()
        http_message.set_body(json.dumps(structured_request).encode('utf-8'))
        
        response = self.ip_server.process_validate_structured_request(http_message)
        self._verify_response_status(response, HTTPStatus.OK)
        self._verify_response_body(response, expected_actions)
        
    def test_process_generate_structured_request(self):
        http_host = 'fake_host'
        document_id = 'foo'
        structured_request = {'documentId': document_id}
        warnings = []
        errors = []
        
        expected_actions = {'actions': [intent_parser_view.valid_request_model_dialog(warnings, intent_parser_view.get_download_link(http_host, document_id))]}
        self.mock_intent_parser.process_structure_request.return_value = structured_request
        self.mock_intent_parser.get_validation_warnings.return_value = warnings
        self.mock_intent_parser.get_validation_errors.return_value = errors 
        http_message = HttpMessage()
        http_message.process_header('Host:%s' % http_host)
        http_message.set_body(json.dumps(structured_request).encode('utf-8'))
        
        response = self.ip_server.process_generate_structured_request(http_message)
        self._verify_response_status(response, HTTPStatus.OK)
        self._verify_response_body(response, expected_actions)

    def test_process_analyze_document(self):
        http_host = 'fake_host'
        json_body = {'documentId': 'foo', 'user':{}, 'userEmail': {}}
        http_message = HttpMessage()
        http_message.process_header('Host:%s' % http_host)
        http_message.set_body(json.dumps(json_body).encode('utf-8'))

        expected_actions = {'actions': [intent_parser_view.progress_sidebar_dialog()]}
        response = self.ip_server.process_analyze_document(http_message)
        self._verify_response_status(response, HTTPStatus.OK)
        self._verify_response_body(response, expected_actions)

    def test_process_analyze_yes_for_search_results_size_1(self):
        text_paragraph_index = 13
        text_start_offset = 183
        text_end_offset = 185
        document_term = 'DNA'
        dictionary_matched_term = 'DNA'
        desired_sbh_link = 'https://hub.sd2e.org/user/sd2e/design/DNA/1'
        self.mock_sbol_dictionary_accessor.get_common_names_to_uri.return_value = {dictionary_matched_term: desired_sbh_link}
        json_body = {addon_constants.DATA: {addon_constants.BUTTON_ID: {addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                                                       addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                                                       addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                                       addon_constants.ANALYZE_CONTENT_TERM: document_term,
                                                                       addon_constants.DOCUMENT_ID: 'foo',
                                                                       addon_constants.ANALYZE_LINK: desired_sbh_link,
                                                                       addon_constants.ANALYZE_OFFSET: text_start_offset}}}
        client_state = {addon_constants.ANALYZE_SEARCH_RESULTS: [{addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                                                  addon_constants.ANALYZE_OFFSET: text_start_offset,
                                                                  addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                                                  addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                                  'uri': desired_sbh_link,
                                                                  addon_constants.ANALYZE_LINK: None,
                                                                  'text': document_term}],
                        addon_constants.ANALYZE_SEARCH_RESULT_INDEX: 0}
        response = self.ip_server.process_analyze_yes(json_body=json_body, client_state=client_state)
        expected_actions = [intent_parser_view.simple_sidebar_dialog('Finished Analyzing Document.', [])]
        self.assertEqual(response, expected_actions)

    def test_process_analyze_yes_for_search_results_size_2(self):
        text_paragraph_index = 13
        text_start_offset = 183
        text_end_offset = 185
        document_term = 'DNA'
        dictionary_matched_term = 'DNA'
        desired_sbh_link = 'https://hub.sd2e.org/user/sd2e/design/DNA/1'
        self.mock_sbol_dictionary_accessor.get_common_names_to_uri.return_value = {dictionary_matched_term: desired_sbh_link,
                                                                                   'protein': 'https://hub.sd2e.org/user/sd2e/design/protein/1'}
        json_body = {addon_constants.DATA: {addon_constants.BUTTON_ID: {addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                                                       addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                                                       addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                                       addon_constants.ANALYZE_CONTENT_TERM: document_term,
                                                                       addon_constants.DOCUMENT_ID: 'foo',
                                                                       addon_constants.ANALYZE_LINK: desired_sbh_link,
                                                                       addon_constants.ANALYZE_OFFSET: text_start_offset}}}
        client_state = {addon_constants.ANALYZE_SEARCH_RESULTS: [{addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                                                  addon_constants.ANALYZE_OFFSET: text_start_offset,
                                                                  addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                                                  addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                                  'uri': desired_sbh_link,
                                                                  addon_constants.ANALYZE_LINK: None,
                                                                  'text': document_term},
                                                                 {addon_constants.ANALYZE_PARAGRAPH_INDEX: 20,
                                                                  addon_constants.ANALYZE_OFFSET: 15,
                                                                  addon_constants.ANALYZE_END_OFFSET: 23,
                                                                  addon_constants.ANALYZE_TERM: 'protein',
                                                                  'uri': 'https://hub.sd2e.org/user/sd2e/design/protein/1',
                                                                  addon_constants.ANALYZE_LINK: None,
                                                                  'text': 'protein'}
                                                                 ],
                        addon_constants.ANALYZE_SEARCH_RESULT_INDEX: 0,
                        'document_id': 'document_foo'}
        response = self.ip_server.process_analyze_yes(json_body=json_body, client_state=client_state)
        expected_actions = [intent_parser_view.link_text(text_paragraph_index, text_start_offset, text_end_offset, desired_sbh_link)]
        expected_actions.extend(intent_parser_view.create_search_result_dialog('protein', 'https://hub.sd2e.org/user/sd2e/design/protein/1', 'protein', 'document_foo', 20, 15, 23))
        self.assertEqual(response, expected_actions)

    def test_process_analyze_no_for_search_results_size_1(self):
        text_paragraph_index = 13
        text_start_offset = 183
        text_end_offset = 185
        document_term = 'DNA'
        dictionary_matched_term = 'DNA'
        desired_sbh_link = 'https://hub.sd2e.org/user/sd2e/design/DNA/1'
        self.mock_sbol_dictionary_accessor.get_common_names_to_uri.return_value = {dictionary_matched_term: desired_sbh_link}
        json_body = {addon_constants.DATA: {
            addon_constants.BUTTON_ID: {addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                        addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                        addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                        addon_constants.ANALYZE_CONTENT_TERM: document_term,
                                        addon_constants.DOCUMENT_ID: 'foo',
                                        addon_constants.ANALYZE_LINK: desired_sbh_link,
                                        addon_constants.ANALYZE_OFFSET: text_start_offset}}}
        client_state = {
            addon_constants.ANALYZE_SEARCH_RESULTS: [{addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                                      addon_constants.ANALYZE_OFFSET: text_start_offset,
                                                      addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                                      addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                      'uri': desired_sbh_link,
                                                      addon_constants.ANALYZE_LINK: None,
                                                      'text': document_term}],
            addon_constants.ANALYZE_SEARCH_RESULT_INDEX: 0}
        response = self.ip_server.process_analyze_no(json_body=json_body, client_state=client_state)
        expected_actions = [intent_parser_view.simple_sidebar_dialog('Finished Analyzing Document.', [])]
        self.assertEqual(response, expected_actions)

    def test_process_analyze_no_for_search_results_size_2(self):
        text_paragraph_index = 13
        text_start_offset = 183
        text_end_offset = 185
        document_term = 'DNA'
        dictionary_matched_term = 'DNA'
        desired_sbh_link = 'https://hub.sd2e.org/user/sd2e/design/DNA/1'
        self.mock_sbol_dictionary_accessor.get_common_names_to_uri.return_value = {dictionary_matched_term: desired_sbh_link,
                                                                                   'protein': 'https://hub.sd2e.org/user/sd2e/design/protein/1'}
        json_body = {addon_constants.DATA: {addon_constants.BUTTON_ID: {addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                                                       addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                                                       addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                                       addon_constants.ANALYZE_CONTENT_TERM: document_term,
                                                                       addon_constants.DOCUMENT_ID: 'foo',
                                                                       addon_constants.ANALYZE_LINK: desired_sbh_link,
                                                                       addon_constants.ANALYZE_OFFSET: text_start_offset}}}
        client_state = {addon_constants.ANALYZE_SEARCH_RESULTS: [{addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                                                  addon_constants.ANALYZE_OFFSET: text_start_offset,
                                                                  addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                                                  addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                                  'uri': desired_sbh_link,
                                                                  addon_constants.ANALYZE_LINK: None,
                                                                  'text': document_term},
                                                                 {addon_constants.ANALYZE_PARAGRAPH_INDEX: 20,
                                                                  addon_constants.ANALYZE_OFFSET: 15,
                                                                  addon_constants.ANALYZE_END_OFFSET: 23,
                                                                  addon_constants.ANALYZE_TERM: 'protein',
                                                                  'uri': 'https://hub.sd2e.org/user/sd2e/design/protein/1',
                                                                  addon_constants.ANALYZE_LINK: None,
                                                                  'text': 'protein'}
                                                                 ],
                        addon_constants.ANALYZE_SEARCH_RESULT_INDEX: 0,
                        'document_id': 'document_foo'}
        response = self.ip_server.process_analyze_no(json_body=json_body, client_state=client_state)
        expected_actions = intent_parser_view.create_search_result_dialog('protein', 'https://hub.sd2e.org/user/sd2e/design/protein/1', 'protein', 'document_foo', 20, 15, 23)
        self.assertEqual(response, expected_actions)

    def test_process_analyze_no_to_all_for_1_term_occurrence_with_search_results_size_1(self):
        text_paragraph_index = 13
        text_start_offset = 183
        text_end_offset = 185
        document_term = 'DNA'
        dictionary_matched_term = 'DNA'
        desired_sbh_link = 'https://hub.sd2e.org/user/sd2e/design/DNA/1'
        self.mock_sbol_dictionary_accessor.get_common_names_to_uri.return_value = {
            dictionary_matched_term: desired_sbh_link}
        json_body = {addon_constants.DATA: {
            addon_constants.BUTTON_ID: {addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                        addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                        addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                        addon_constants.ANALYZE_CONTENT_TERM: document_term,
                                        addon_constants.DOCUMENT_ID: 'foo',
                                        addon_constants.ANALYZE_LINK: desired_sbh_link,
                                        addon_constants.ANALYZE_OFFSET: text_start_offset}}}
        client_state = {
            addon_constants.ANALYZE_SEARCH_RESULTS: [{addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                                      addon_constants.ANALYZE_OFFSET: text_start_offset,
                                                      addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                                      addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                      'uri': desired_sbh_link,
                                                      addon_constants.ANALYZE_LINK: None,
                                                      'text': document_term}
                                                     ],
            addon_constants.ANALYZE_SEARCH_RESULT_INDEX: 0}
        response = self.ip_server.process_no_to_all(json_body=json_body, client_state=client_state)
        expected_actions = [intent_parser_view.simple_sidebar_dialog('Finished Analyzing Document.', [])]
        self.assertEqual(response, expected_actions)

    def test_process_analyze_no_to_all_for_2_term_occurrences_with_search_results_size_2(self):
        text_paragraph_index = 13
        text_start_offset = 183
        text_end_offset = 185
        document_term = 'DNA'
        dictionary_matched_term = 'DNA'
        desired_sbh_link = 'https://hub.sd2e.org/user/sd2e/design/DNA/1'
        self.mock_sbol_dictionary_accessor.get_common_names_to_uri.return_value = {
            dictionary_matched_term: desired_sbh_link}
        json_body = {addon_constants.DATA: {
            addon_constants.BUTTON_ID: {addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                        addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                        addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                        addon_constants.ANALYZE_CONTENT_TERM: document_term,
                                        addon_constants.DOCUMENT_ID: 'foo',
                                        addon_constants.ANALYZE_LINK: desired_sbh_link,
                                        addon_constants.ANALYZE_OFFSET: text_start_offset}}}
        client_state = {
            addon_constants.ANALYZE_SEARCH_RESULTS: [{addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                                      addon_constants.ANALYZE_OFFSET: text_start_offset,
                                                      addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                                      addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                      'uri': desired_sbh_link,
                                                      addon_constants.ANALYZE_LINK: None,
                                                      'text': document_term},
                                                     {addon_constants.ANALYZE_PARAGRAPH_INDEX: 20,
                                                      addon_constants.ANALYZE_OFFSET: 200,
                                                      addon_constants.ANALYZE_END_OFFSET: 210,
                                                      addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                      'uri': desired_sbh_link,
                                                      addon_constants.ANALYZE_LINK: None,
                                                      'text': document_term}
                                                     ],
            addon_constants.ANALYZE_SEARCH_RESULT_INDEX: 0}
        response = self.ip_server.process_no_to_all(json_body=json_body, client_state=client_state)
        expected_actions = [intent_parser_view.simple_sidebar_dialog('Finished Analyzing Document.', [])]
        self.assertEqual(response, expected_actions)

    def test_process_analyze_yes_to_all_for_1_term_occurrence(self):
        text_paragraph_index = 13
        text_start_offset = 183
        text_end_offset = 185
        document_term = 'DNA'
        dictionary_matched_term = 'DNA'
        desired_sbh_link = 'https://hub.sd2e.org/user/sd2e/design/DNA/1'
        self.mock_sbol_dictionary_accessor.get_common_names_to_uri.return_value = {
            dictionary_matched_term: desired_sbh_link}
        json_body = {addon_constants.DATA: {
            addon_constants.BUTTON_ID: {addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                        addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                        addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                        addon_constants.ANALYZE_CONTENT_TERM: document_term,
                                        addon_constants.DOCUMENT_ID: 'foo',
                                        addon_constants.ANALYZE_LINK: desired_sbh_link,
                                        addon_constants.ANALYZE_OFFSET: text_start_offset}}}
        client_state = {
            addon_constants.ANALYZE_SEARCH_RESULTS: [{addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                                      addon_constants.ANALYZE_OFFSET: text_start_offset,
                                                      addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                                      addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                      'uri': desired_sbh_link,
                                                      addon_constants.ANALYZE_LINK: None,
                                                      'text': document_term}
                                                     ],
            addon_constants.ANALYZE_SEARCH_RESULT_INDEX: 0}
        response = self.ip_server.process_link_all(json_body=json_body, client_state=client_state)
        expected_actions = [intent_parser_view.link_text(text_paragraph_index, text_start_offset, text_end_offset, desired_sbh_link),
                            intent_parser_view.simple_sidebar_dialog('Finished Analyzing Document.', [])]
        self.assertEqual(response, expected_actions)

    def test_process_analyze_yes_to_all_for_2_term_occurrences_with_search_results_size_2(self):
        text_paragraph_index = 13
        text_start_offset = 183
        text_end_offset = 185
        document_term = 'DNA'
        dictionary_matched_term = 'DNA'
        desired_sbh_link = 'https://hub.sd2e.org/user/sd2e/design/DNA/1'
        self.mock_sbol_dictionary_accessor.get_common_names_to_uri.return_value = {
            dictionary_matched_term: desired_sbh_link}
        json_body = {addon_constants.DATA: {
            addon_constants.BUTTON_ID: {addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                        addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                        addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                        addon_constants.ANALYZE_CONTENT_TERM: document_term,
                                        addon_constants.DOCUMENT_ID: 'foo',
                                        addon_constants.ANALYZE_LINK: desired_sbh_link,
                                        addon_constants.ANALYZE_OFFSET: text_start_offset}}}
        client_state = {
            addon_constants.ANALYZE_SEARCH_RESULTS: [{addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                                      addon_constants.ANALYZE_OFFSET: text_start_offset,
                                                      addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                                      addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                      'uri': desired_sbh_link,
                                                      addon_constants.ANALYZE_LINK: None,
                                                      'text': document_term},
                                                     {addon_constants.ANALYZE_PARAGRAPH_INDEX: 20,
                                                      addon_constants.ANALYZE_OFFSET: 200,
                                                      addon_constants.ANALYZE_END_OFFSET: 210,
                                                      addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                      'uri': desired_sbh_link,
                                                      addon_constants.ANALYZE_LINK: None,
                                                      'text': document_term}
                                                     ],
            addon_constants.ANALYZE_SEARCH_RESULT_INDEX: 0}
        response = self.ip_server.process_link_all(json_body=json_body, client_state=client_state)
        expected_actions = [intent_parser_view.link_text(text_paragraph_index, text_start_offset, text_end_offset, desired_sbh_link),
                            intent_parser_view.link_text(20, 200, 210, desired_sbh_link),
                            intent_parser_view.simple_sidebar_dialog('Finished Analyzing Document.', [])]
        self.assertEqual(response, expected_actions)

    def test_process_analyze_yes_to_all_for_2_term_occurrences_with_search_results_size_3(self):
        text_paragraph_index = 13
        text_start_offset = 183
        text_end_offset = 185
        document_term = 'DNA'
        dictionary_matched_term = 'DNA'
        desired_sbh_link = 'https://hub.sd2e.org/user/sd2e/design/DNA/1'
        self.mock_sbol_dictionary_accessor.get_common_names_to_uri.return_value = {
            dictionary_matched_term: desired_sbh_link,
            'protein': 'https://hub.sd2e.org/user/sd2e/design/protein/1'}
        json_body = {addon_constants.DATA: {
            addon_constants.BUTTON_ID: {addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                        addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                        addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                        addon_constants.ANALYZE_CONTENT_TERM: document_term,
                                        addon_constants.DOCUMENT_ID: 'foo',
                                        addon_constants.ANALYZE_LINK: desired_sbh_link,
                                        addon_constants.ANALYZE_OFFSET: text_start_offset}}}
        client_state = {
            addon_constants.ANALYZE_SEARCH_RESULTS: [{addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                                      addon_constants.ANALYZE_OFFSET: text_start_offset,
                                                      addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                                      addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                      'uri': desired_sbh_link,
                                                      addon_constants.ANALYZE_LINK: None,
                                                      'text': document_term},
                                                     {addon_constants.ANALYZE_PARAGRAPH_INDEX: 20,
                                                      addon_constants.ANALYZE_OFFSET: 200,
                                                      addon_constants.ANALYZE_END_OFFSET: 210,
                                                      addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                      'uri': desired_sbh_link,
                                                      addon_constants.ANALYZE_LINK: None,
                                                      'text': document_term},
                                                     {addon_constants.ANALYZE_PARAGRAPH_INDEX: 20,
                                                      addon_constants.ANALYZE_OFFSET: 15,
                                                      addon_constants.ANALYZE_END_OFFSET: 23,
                                                      addon_constants.ANALYZE_TERM: 'protein',
                                                      'uri': 'https://hub.sd2e.org/user/sd2e/design/protein/1',
                                                      addon_constants.ANALYZE_LINK: None,
                                                      'text': 'protein'}
                                                     ],
            addon_constants.ANALYZE_SEARCH_RESULT_INDEX: 0,
            'document_id': 'document_foo'}
        response = self.ip_server.process_link_all(json_body=json_body, client_state=client_state)
        expected_actions = [intent_parser_view.link_text(text_paragraph_index, text_start_offset, text_end_offset, desired_sbh_link),
                            intent_parser_view.link_text(20, 200, 210, desired_sbh_link)]
        expected_actions.extend(intent_parser_view.create_search_result_dialog('protein', 'https://hub.sd2e.org/user/sd2e/design/protein/1', 'protein', 'document_foo', 20, 15, 23))
        self.assertEqual(response, expected_actions)

    def test_process_analyze_never_link_terms_for_1_occurrence_with_search_results_size_1(self):
        text_paragraph_index = 13
        text_start_offset = 183
        text_end_offset = 185
        document_term = 'foo'
        dictionary_matched_term = 'foo'
        desired_sbh_link = 'https://hub.sd2e.org/user/sd2e/design/DNA/1'

        json_body = {addon_constants.DATA: {
            addon_constants.BUTTON_ID: {addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                        addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                        addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                        addon_constants.ANALYZE_CONTENT_TERM: document_term,
                                        addon_constants.DOCUMENT_ID: 'foo',
                                        addon_constants.ANALYZE_LINK: desired_sbh_link,
                                        addon_constants.ANALYZE_OFFSET: text_start_offset}}}
        client_state = {
            addon_constants.ANALYZE_SEARCH_RESULTS: [{addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                                      addon_constants.ANALYZE_OFFSET: text_start_offset,
                                                      addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                                      addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                      'uri': desired_sbh_link,
                                                      addon_constants.ANALYZE_LINK: None,
                                                      'text': document_term}
                                                     ],
            addon_constants.ANALYZE_SEARCH_RESULT_INDEX: 0,
            addon_constants.USER_ID: 'admin',
            'document_id': 'document_foo'}
        response = self.ip_server.process_never_link(json_body=json_body, client_state=client_state)
        expected_actions = [intent_parser_view.simple_sidebar_dialog('Finished Analyzing Document.', [])]
        self.assertEqual(response, expected_actions)

    def test_process_analyze_never_link_terms_for_1_occurrence_with_search_results_size_3(self):
        text_paragraph_index = 13
        text_start_offset = 183
        text_end_offset = 185
        document_term = 'foo'
        dictionary_matched_term = 'foo'
        desired_sbh_link = 'https://hub.sd2e.org/user/sd2e/design/DNA/1'

        json_body = {addon_constants.DATA: {
            addon_constants.BUTTON_ID: {addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                        addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                        addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                        addon_constants.ANALYZE_CONTENT_TERM: document_term,
                                        addon_constants.DOCUMENT_ID: 'foo',
                                        addon_constants.ANALYZE_LINK: desired_sbh_link,
                                        addon_constants.ANALYZE_OFFSET: text_start_offset}}}
        client_state = {
            addon_constants.ANALYZE_SEARCH_RESULTS: [{addon_constants.ANALYZE_PARAGRAPH_INDEX: text_paragraph_index,
                                                      addon_constants.ANALYZE_OFFSET: text_start_offset,
                                                      addon_constants.ANALYZE_END_OFFSET: text_end_offset,
                                                      addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                      'uri': desired_sbh_link,
                                                      addon_constants.ANALYZE_LINK: None,
                                                      'text': document_term},
                                                     {addon_constants.ANALYZE_PARAGRAPH_INDEX: 20,
                                                      addon_constants.ANALYZE_OFFSET: 200,
                                                      addon_constants.ANALYZE_END_OFFSET: 210,
                                                      addon_constants.ANALYZE_TERM: dictionary_matched_term,
                                                      'uri': desired_sbh_link,
                                                      addon_constants.ANALYZE_LINK: None,
                                                      'text': document_term},
                                                     {addon_constants.ANALYZE_PARAGRAPH_INDEX: 20,
                                                      addon_constants.ANALYZE_OFFSET: 15,
                                                      addon_constants.ANALYZE_END_OFFSET: 23,
                                                      addon_constants.ANALYZE_TERM: 'protein',
                                                      'uri': 'https://hub.sd2e.org/user/sd2e/design/protein/1',
                                                      addon_constants.ANALYZE_LINK: None,
                                                      'text': 'protein'}
                                                     ],
            addon_constants.ANALYZE_SEARCH_RESULT_INDEX: 0,
            addon_constants.USER_ID: 'admin',
            'document_id': 'document_foo'}
        response = self.ip_server.process_never_link(json_body=json_body, client_state=client_state)
        expected_actions = intent_parser_view.create_search_result_dialog('protein', 'https://hub.sd2e.org/user/sd2e/design/protein/1', 'protein', 'document_foo', 20, 15, 23)
        self.assertEqual(response, expected_actions)

    def _verify_response_status(self, response, expected_status):
        header_from_status = 'HTTP/1.1 %s %s' % (expected_status.value, expected_status.name)
        assert response.requestLine == header_from_status
        
    def _verify_response_body(self, response, expected_body):
        response_json = json.loads(response.get_body())
        expected_json = json.dumps(expected_body)
        assert response_json == expected_body
     
if __name__ == "__main__":
    unittest.main()