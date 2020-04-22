from http import HTTPStatus
from http_message import HttpMessage
from intent_parser_server import IntentParserServer
from unittest.mock import Mock, patch
import intent_parser_view
import json
import unittest

class IntentParserServerTest(unittest.TestCase):
    """
    Test IntentParserServer response for different requests made to the server. 
    """

    @patch('intent_parser_factory.IntentParserFactory')
    @patch('strateos_accessor.StrateosAccessor')
    @patch('sbol_dictionary_accessor.SBOLDictionaryAccessor')
    @patch('intent_parser_sbh.IntentParserSBH')
    def setUp(self, mock_intent_parser_sbh, mock_sbol_dictionary_accessor, mock_strateos_accessor, mock_intent_parser_factory):
        self.mock_intent_parser_sbh = mock_intent_parser_sbh
        self.mock_sbol_dictionary_accessor = mock_sbol_dictionary_accessor
        self.mock_strateos_accessor = mock_strateos_accessor
        self.mock_intent_parser_factory = mock_intent_parser_factory
        
        self.mock_intent_parser = Mock()
        self.mock_intent_parser_factory.create_intent_parser.return_value = self.mock_intent_parser
        
        self.ip_server = IntentParserServer(self.mock_intent_parser_sbh, self.mock_sbol_dictionary_accessor, self.mock_strateos_accessor, self.mock_intent_parser_factory, 'localhost', 8081)
    
    def tearDown(self):
        pass

    def test_process_document_report(self):
        expected_report = {'challenge_problem_id' : 'undefined',
                            'experiment_reference_url' : 'foo',
                            'labs' : [],
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
        self.mock_intent_parser.process.return_value = structured_request
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
        self.mock_intent_parser.process.return_value = structured_request
        self.mock_intent_parser.get_validation_warnings.return_value = warnings
        self.mock_intent_parser.get_validation_errors.return_value = errors 
        http_message = HttpMessage()
        http_message.process_header('Host:%s' % http_host)
        http_message.set_body(json.dumps(structured_request).encode('utf-8'))
        
        response = self.ip_server.process_generate_structured_request(http_message)
        self._verify_response_status(response, HTTPStatus.OK)
        self._verify_response_body(response, expected_actions)
       
    def _verify_response_status(self, response, expected_status):
        header_from_status = 'HTTP/1.1 %s %s' % (expected_status.value, expected_status.name)
        assert response.requestLine == header_from_status
        
    def _verify_response_body(self, response, expected_body):
        response_json = json.loads(response.get_body())
        expected_json = json.dumps(expected_body)
        assert response_json == expected_body
     
if __name__ == "__main__":
    unittest.main()