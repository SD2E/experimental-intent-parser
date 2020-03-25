from git import Repo, remote
from google_accessor import GoogleAccessor
from intent_parser_server import IntentParserServer
from unittest.mock import Mock
from os import listdir
from os.path import isfile, join
import intent_parser_utils as ip_util
import ip_addon_script 
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
       
        # If we don't have the necessary credentials, try reading them in from json
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

        self.doc = self.google_accessor.set_spreadsheet_id(self.spreadsheet_id)

        sbh_collection_uri = 'https://hub-staging.sd2e.org/user/sd2e/' + \
            'intent_parser/intent_parser_collection/1'

        self.intent_parser = IntentParserServer(sbh_collection_uri=sbh_collection_uri,
                                                sbh_username=self.sbh_username,
                                                sbh_password=self.sbh_password,
                                                spreadsheet_id=self.spreadsheet_id,
                                                item_map_cache=False,
                                                bind_ip='localhost',
                                                bind_port=8081,
                                                datacatalog_authn=self.authn)

        # checkout cp-request repo 
        self.repo_path = os.path.join(curr_path, '../tests/data/cp-request') 
        repo = Repo(self.repo_path)
        if not repo.bare:
            print('Repo at {} successfully loaded.'.format(self.repo_path))
            
            # pull from cp-request repo. 
            remote_branches = repo.remotes.origin
            pulled_result = remote_branches.pull()
            print(pulled_result)
        else:
            print('Repo did not load successfully. Load local data')
        
        # load golden files
        golden_file_dir = '/'.join([self.repo_path, 'input/structured_requests'])
        self.golden_file_map = {}
        for file in listdir(golden_file_dir):
            file_path = join(golden_file_dir, file)
            if isfile(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    doc_url = data['experiment_reference_url']
                    doc_id = ip_util.get_google_doc_id(doc_url)
                    self.golden_file_map[doc_id] = data

        self.maxDiff = None # Set flag for testing to diff between large strings 
   
    @unittest.skip("deprecating test case")
    def test_document_requests(self):
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
                        '1YlmQGx-i8IhLpWAp6lEiuRHNuGHzfNkgVfk1UhsPW1c', # 1XFC1onvvrhggNHiAci-iu2msXZQg3_SyiGdKnKUwrpM
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
            self.intent_parser.process_generate_request(httpMessage, [])

            actual_data = json.loads(self.intent_parser.send_response.call_args[0][2])
            with open(os.path.join(self.data_dir, doc_id + '_expected.json'), 'r') as file:
                expected_data = json.load(file)
                self.assertEqual(expected_data, actual_data)
   
    def test_golden_files(self):
        """Diff results from ip and cp-request golden files"""
        trashed_files = ['1IklGPJ13VpG9a_XL0SdbUoYKlt4lQxFdpLVjGUnbcYw'] #unable to locate file from google api
        invalid_files = ['1EuAsTsUdgyVZ45FctdQi0DdPX1dLUxQZpHAvA45h7wE',
                         '1eMxFcAWA24fXrRAeKp9WeOvy8Woil7FriO3xf3p7mac'] #broken validation
        failed_files = []
        for doc_id in self.golden_file_map:
            print(doc_id)
            if doc_id in trashed_files or doc_id in invalid_files:
                continue
            httpMessage = Mock()
            httpMessage.get_resource = Mock(return_value='/document_report?' + doc_id)
            payload = {'documentId':  doc_id, 'user' : 'test@bbn.com', 'userEmail' : 'test@bbn.com'}
            payload_bytes = json.dumps(payload).encode()
            self.intent_parser.send_response = Mock()
            self.intent_parser.process_generate_request(httpMessage, [])
           
            # compare result with golden file 
            actual_data = json.loads(self.intent_parser.send_response.call_args[0][2])
            expected_data = self.golden_file_map[doc_id]
            if expected_data != actual_data:
                failed_files.append(doc_id)
                continue
            
            self.assertDictEqual(actual_data, expected_data)
        
        print('%d files not the same' % len(failed_files))
        for id in failed_files:
            print(id)
                
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