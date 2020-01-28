from google_accessor import GoogleAccessor
from intent_parser_server import IntentParserServer
from unittest.mock import Mock
import unittest
import json 
import os 
import time

class GenerateStruturedRequestTest(unittest.TestCase):
    """
    Class to test RESTful API calls to generate a structural request from intent parser.
    """
    
    @classmethod
    def setUpClass(self):
        curr_path = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(curr_path, '../tests/data')
       
        with open(os.path.join(curr_path, 'sbh_creds.json'), 'r') as fin:
            creds = json.load(fin)
            self.sbh_username = creds['username']
            self.sbh_password = creds['password']
        
        with open(os.path.join(self.data_dir, 'authn.json'), 'r') as file:
            self.authn = json.load(file)['authn']
            
        self.google_accessor = GoogleAccessor.create()
        
        self.template_spreadsheet_id = '1r3CIyv75vV7A7ghkB0od-TM_16qSYd-byAbQ1DhRgB0'
        self.spreadsheet_id = self.google_accessor.copy_file(file_id = self.template_spreadsheet_id,
                                                     new_title='Intent Parser Server Test Sheet')

        self.doc = self.google_accessor.set_spreadsheet_id(self.spreadsheet_id)

        sbh_collection_uri = 'https://hub-staging.sd2e.org/user/sd2e/' + \
            'intent_parser/intent_parser_collection/1'

        self.intent_parser = IntentParserServer(sbh_collection_uri=sbh_collection_uri,
                                                sbh_username=GenerateStruturedRequestTest.sbh_username,
                                                sbh_password=GenerateStruturedRequestTest.sbh_password,
                                                spreadsheet_id=self.spreadsheet_id,
                                                item_map_cache=False,
                                                bind_ip='localhost',
                                                bind_port=8081,
                                                datacatalog_authn=self.authn)

        self.maxDiff = None # Set flag for testing to diff between large strings 
   
    @unittest.skip('Skip test for comparing Google Documents results')
    def test_document_requests(self):
        '''
        This method compares a list of Google documents with its corresponding golden file.
        This test method should be skipped when for deployment. 
        This test method should only run locally by commenting out the @unittest.skip. 
        These Google documents are modified by active users in the SD2 program and information generated for a structured request will change.
        Golden files used for testing these Google documents should be updated when new feature are supported for intent parser.   
        '''
        doc_id_list = ['13tJ1JdCxL9bA9x3oNxGPm-LymW91-OT7SRW6fHyEBCo',
                        '1WOa8crKEpJX0ZFJv4NtMjVaI-35__sdEMc5aPxb1al4', 
                        '1uv_X7CSD5cONEjW7yq4ecI89XQxPQuG5lnmaqshj47o', 
                        '1XFC1onvvrhggNHiAci-iu2msXZQg3_SyiGdKnKUwrpM', 
#                         '1v5UHLS4qvVovMK8GP9MgoboiPGsg_YzgyE9H4E5DTHg', #expected: UWBF_6390, actual: \u000bUWBF_6390
                        '15aMX9WdN1gyvjG30sXQZYPdTSTGbxoIRJbqtOvoKyQ0', 
                        '1N0i5RPY-xEsM_MIjqeWZI6cjb9rj3B7L1PGR-Q-ufe0', 
#                        '16p9WmU9_dEz6wGN5_maotPl5uGrAIxPZ3-pNq1hipfI', #expected: celsius actual: unspecified
                        '1ZPLjkEODVzRlqRA110cDVT3wK6nvvNr4wKMMPoDLnTY', 
                        '16eroq4UtIPhP89_PiKnvfi4wxV52vdKtUwPmBBu6OMc', 
                        '1IlR2-ufP_vVfHt15uYocExhyQfEkPnOljYf3Y-rB08g', 
                        '1ISVqTR3GfnzWB7pq66CbAWdVTn2RHBs4rgBbQt9N2Oo', 
                        '138hHqZ-HT6owJ3DxANcrds67j8dZG8GPt4KLTTS1jU4', 
                        '1PmSRNQUpvFTjANQpktjxjrfItPMTNgGVry5fT3mLmzc', 
                        '1oIBd-a_n8pGNtoM9zYkWjhlsG04B2lmfYKhlLSAkRFw', 
                        '1h_VBtGgUa4pFrR5pTksogFpzSMuE6cyRRjJmFuJpKSk', 
                        '1b81XIA-e_5D6we8nVnMJe6fahizTw4qNSxlOkTI2PNs'  
                       ]
        for doc_id in doc_id_list:
            httpMessage = Mock()
            httpMessage.get_resource = Mock(return_value='/document_report?' + doc_id)
            payload = {'documentId':  doc_id, 'user' : 'test@bbn.com', 'userEmail' : 'test@bbn.com'}
            payload_bytes = json.dumps(payload).encode()
            
            self.intent_parser.send_response = Mock()
            self.intent_parser.process_generate_request(httpMessage, [])

            actual_data = json.loads(self.intent_parser.send_response.call_args[0][2])
            with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
                expected_data = json.load(file)
                self.assertEqual(expected_data, actual_data)
    
    @classmethod
    def tearDownClass(self):
        print('\nstart teardown')
        if self.intent_parser is not None:
            self.intent_parser.stop()
        if self.doc is not None:
            self.google_accessor.delete_file(file_id=self.spreadsheet_id)
        print('done')
        
if __name__ == "__main__":
    unittest.main()