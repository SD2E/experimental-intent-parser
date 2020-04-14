from google_accessor import GoogleAccessor
from intent_parser_server import IntentParserServer
from os import listdir
from os.path import isfile
from unittest.mock import Mock
import git
import intent_parser_utils
import unittest
import json 
import time

class GoldenFileTest(unittest.TestCase):
    """
    Test a selection of Google docs by generating a structured request for each document and comparing the result to its expected result. 
    """
    
    @classmethod
    def setUpClass(self):
        curr_path = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(curr_path, 'data')
        
        cp_request_dir = os.path.join(curr_path, 'data', 'cp-request')
        git_accessor = git.cmd.Git(cp_request_dir)
        git_accessor.pull()
        self.structured_request_dir = os.path.join(cp_request_dir, 'input', 'structured_requests')
        print(self.structured_request_dir)
        
        with open(os.path.join(curr_path, 'sbh_creds.json'), 'r') as file:
            creds = json.load(file)
            self.sbh_username = creds['username']
            self.sbh_password = creds['password']
        
        with open(os.path.join(self.data_dir, 'authn.json'), 'r') as file:
            self.authn = json.load(file)['authn']
            
        self.google_accessor = GoogleAccessor.create()
        self.template_spreadsheet_id = '1r3CIyv75vV7A7ghkB0od-TM_16qSYd-byAbQ1DhRgB0'
        self.spreadsheet_id = self.google_accessor.copy_file(file_id = self.template_spreadsheet_id,
                                                     new_title='Intent Parser Server Test Sheet')


        self.google_accessor.set_spreadsheet_id(self.spreadsheet_id)

        sbh_collection_uri = 'https://hub-staging.sd2e.org/user/sd2e/intent_parser/intent_parser_collection/1'

        self.intent_parser = IntentParserServer(sbh_collection_uri=sbh_collection_uri,
                                                sbh_username=self.sbh_username,
                                                sbh_password=self.sbh_password,
                                                spreadsheet_id=self.spreadsheet_id,
                                                item_map_cache=False,
                                                bind_ip='localhost',
                                                bind_port=8081,
                                                datacatalog_authn=self.authn)

        self.intent_parser.initialize_server()
        self.intent_parser.start(background=True) 
        self.maxDiff = None # Set flag for testing to diff between large strings 

                
    def test_document_requests_using_golden_files(self):
        '''
        Compare a list of Google documents with its corresponding golden file.
        Golden files used for testing these Google documents should be updated when new feature are supported for intent parser.   
        '''
        
        '''
        List of google document ids used for comparing with its golden file. 
        The commented ids represents actual documents used for SD2 program and should not be modified for testing.
        '''
        doc_id_list = ['13tJ1JdCxL9bA9x3oNxGPm-LymW91-OT7SRW6fHyEBCo', 
                        '1A8-57gZue9h0ryDfASF7fH2maBPhOZ1e_AJCtIAez58', # 1WOa8crKEpJX0ZFJv4NtMjVaI-35__sdEMc5aPxb1al4
                        '1180pM7EEEboemf_wdAdw6RnwD0-dk9o4OJpvSdmhaIY', # 1uv_X7CSD5cONEjW7yq4ecI89XQxPQuG5lnmaqshj47o 
#                         '1YlmQGx-i8IhLpWAp6lEiuRHNuGHzfNkgVfk1UhsPW1c', # 1XFC1onvvrhggNHiAci-iu2msXZQg3_SyiGdKnKUwrpM
                        '1ANYsKgAkY1InQmaIPMJ91-GOgBJpBveWcngFCl6fPdY', # 1v5UHLS4qvVovMK8GP9MgoboiPGsg_YzgyE9H4E5DTHg 
                        '1sM6wz4s7K5DpPupz8Jn5RFW1ETkP91_zLpBCJPP7HC8', # 15aMX9WdN1gyvjG30sXQZYPdTSTGbxoIRJbqtOvoKyQ0
                        '1xzl0dgRLuSLDvAcsNzZwvZL3ILAzq03Xbj9oAlLe9lo', # 1N0i5RPY-xEsM_MIjqeWZI6cjb9rj3B7L1PGR-Q-ufe0 Note: contain list of strings 
                        '1WjMSia1kHh9szIuIZ6VAlWl5-rCbTQ9GGzetqPds0qM', # 16p9WmU9_dEz6wGN5_maotPl5uGrAIxPZ3-pNq1hipfI
                        '1TeJpHmKOSm8Lhc-7V0Csl0x8fPL83lFCZV16HXFge80', # 1ZPLjkEODVzRlqRA110cDVT3wK6nvvNr4wKMMPoDLnTY 
                        '1XbmjAgXl5U66ETKJqyUEVuI8FNuKw-BIh4tJ_xeGRd0', # 16eroq4UtIPhP89_PiKnvfi4wxV52vdKtUwPmBBu6OMc 
                        '1qNcpdPbyf-hb5w_nV9Nu7TC6nvzdcdUKQtS0kKJCMI4', # 1IlR2-ufP_vVfHt15uYocExhyQfEkPnOljYf3Y-rB08g Note: contain list of float
                        '1TMNRf0CB_7wCQEq7Rq4_gfpcnRke7B-Px4c3ZFr7a4o', # 1ISVqTR3GfnzWB7pq66CbAWdVTn2RHBs4rgBbQt9N2Oo Note: contain list of float
                        '13qZX3MdSMiGx0wYDCATJpvEXcxbIdrwDJmlctrdUk8o', # 138hHqZ-HT6owJ3DxANcrds67j8dZG8GPt4KLTTS1jU4 
                        '12S2lPHkvjiX97lTxIlAcWuGiemL7AqGbT4s8oNMX0vU', # 1PmSRNQUpvFTjANQpktjxjrfItPMTNgGVry5fT3mLmzc 
                        '1Sw5pjLu3HZnX4JKDSbXCHUL8Xgla5mpsRCvdmdhDv78', # 1oIBd-a_n8pGNtoM9zYkWjhlsG04B2lmfYKhlLSAkRFw Note: contain list of strings
                        '1usvQw8uwvg61j7gnaEE3eSl7y69rdQYirnkNIzLdKdQ', # 1h_VBtGgUa4pFrR5pTksogFpzSMuE6cyRRjJmFuJpKSk Note: contain list of strings
                        '112W4VmUTwXmJzREeQqZPNiFElwJvzZd8m-v5_rES49I' # 1b81XIA-e_5D6we8nVnMJe6fahizTw4qNSxlOkTI2PNs  
                       ]
        for doc_id in doc_id_list:
            httpMessage = Mock()
            httpMessage.get_resource = Mock(return_value='/document_report?' + doc_id)
            payload = {'documentId':  doc_id, 'user' : 'test@bbn.com', 'userEmail' : 'test@bbn.com'}
            payload_bytes = json.dumps(payload).encode()
            
            self.intent_parser.send_response = Mock()
            self.intent_parser.process_document_request(httpMessage, [])

            result = self.intent_parser.send_response.call_args[0][1]
            actual_data = json.loads(result)
            with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
                expected_data = json.load(file)
                self.assertEqual(expected_data, actual_data)
   
    def test_golden_files(self):
        """
        The selected documents come from SD2 cp-request repository. 
        The document id and the revision id are recorded in cp-request/inpt/structured_request directory.
        Each document are retrieved from  GoogleAccessor by using these document id and its revision id.
        The document is then pass into intent parser to generate a structured request. 
        The structured request is compared with the structured_request result for equivalency.
        """
        for file in listdir(self.structured_request_dir):
            file_path = os.path.join(self.structured_request_dir, file)
            if not isfile(file_path):
                continue
            golden_structured_request = intent_parser_utils.load_json_file(file_path)
            doc_url = golden_structured_request['experiment_reference_url']
            doc_id = ''
            if 'doc_revision_id' not in golden_structured_request:
                continue
            doc_revision_id = golden_structured_request['doc_revision_id']
            
            output_file_path = os.path.join(self.data_dir, 'doc_%s' % file)
            html_doc = self.google_accessor.download_file_with_revision(output_file_path, doc_id, doc_revision_id, 'text/html')
            
            http_message = HttpMessage()
            http_message.process_header('Host:%s' % http_host)
            http_message.set_body(json.dumps(structured_request).encode('utf-8'))
            response = self.intent_parser.process_generate_structured_request(http_message)
            
            
    @classmethod
    def tearDownClass(self):
        print('\nstart teardown')
        if self.intent_parser is not None:
            self.intent_parser.stop()
        if self.spreadsheet_id is not None:
            self.google_accessor.delete_file(file_id=self.spreadsheet_id)
        print('done')
        
if __name__ == "__main__":
    unittest.main()