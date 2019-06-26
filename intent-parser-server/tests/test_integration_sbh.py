import unittest
import warnings
import json
import getopt
import sys
import os
import time
import urllib.request

from unittest.mock import Mock, patch, DEFAULT

try:
    from intent_parser_server import IntentParserServer
except Exception as e:
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../src'))
    from intent_parser_server import IntentParserServer

from google_accessor import GoogleAccessor


class TestIntentParserServer(unittest.TestCase):

    spellcheckFile = 'doc_1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA.json'

    dataDir = 'data'

    template_spreadsheet_id = '1r3CIyv75vV7A7ghkB0od-TM_16qSYd-byAbQ1DhRgB0'
    
    template_sheet_last_rev = '2019-06-12T20:29:13.519Z'

    def setUp(self):
        """
        Configure an instance of IntentParserServer for spellcheck testing.
        """
        # If we don't have the necessary credentials, try reading them in from json
        if not hasattr(TestIntentParserServer, 'sbh_username') or not hasattr(TestIntentParserServer, 'sbh_password'):
            with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sbh_creds.json'), 'r') as fin:
                creds = json.load(fin)
                TestIntentParserServer.sbh_username = creds['username']
                TestIntentParserServer.sbh_password = creds['password']

        self.google_accessor = GoogleAccessor.create()

        rev_results = self.google_accessor.get_document_revisions(document_id=self.template_spreadsheet_id)
        if 'revisions' not in rev_results or len(rev_results['revisions']) < 1 :
            print('ERROR: Failed to retrieve revisions for spreadsheet template!')
            raise Exception
        last_rev = rev_results['revisions'][0]['modifiedTime']
        if not last_rev == self.template_sheet_last_rev:
            print('ERROR: template spreadsheet has been modified! Expected last revision: %s, received %s!' % (self.template_sheet_last_rev, last_rev))
            raise Exception

        self.spreadsheet_id = self.google_accessor.copy_file(file_id=self.template_spreadsheet_id,
                                                     new_title='Intent Parser Server Test Sheet')

        sbh_collection_uri = 'https://hub-staging.sd2e.org/user/sd2e/' + \
            'intent_parser/intent_parser_collection/1'

        self.doc_content = None
        with open(os.path.join(self.dataDir,self.spellcheckFile), 'r') as fin:
            self.doc_content = json.loads(fin.read())

        if self.doc_content is None:
            self.fail('Failed to read in test document! Path: ' + os.path.join(self.dataDir,self.spellcheckFile))

        self.ips = IntentParserServer(sbh_collection_uri=sbh_collection_uri,
                                    sbh_spoofing_prefix='https://hub.sd2e.org',
                                    sbh_username=TestIntentParserServer.sbh_username,
                                    sbh_password=TestIntentParserServer.sbh_password,
                                    spreadsheet_id=self.spreadsheet_id, init_server=False)

        self.ips.google_accessor = Mock()
        self.ips.google_accessor.get_document = Mock(return_value=self.doc_content)
        self.ips.send_response = Mock()

    def test_add_sbh(self):
        """
        Integration test for Add to SynbioHub feature
        """
        term = 'proteomics'
        data = {'term' : term, 'offset' : 0}
        self.json_body = {'data' : data}
        self.ips.get_json_body = Mock(return_value=self.json_body)

        self.ips.process_search_syn_bio_hub([],[])

        results_count = self.ips.sparql_similar_count_cache[term]
        results_count = int(results_count)

        actions = json.loads(self.ips.send_response.call_args[0][2])
        self.assertTrue(len(self.ips.send_response.call_args) == 2)
        self.assertTrue(len(self.ips.send_response.call_args[0]) == 5)
        self.assertTrue(len(actions['results']['search_results']) == 0)
        self.assertTrue(actions['results']['operationSucceeded'])
        
        for line in actions['results']['table_html'].split('\n'):
            if 'Showing' in line:
                self.assertTrue(line.strip() == 'Showing 0 - 5 of %d' % results_count)
        
        # Test value that's larger than results
        data['offset'] = results_count + 10
        self.ips.process_search_syn_bio_hub([],[])
        
        actions = json.loads(self.ips.send_response.call_args[0][2])
        self.assertTrue(len(self.ips.send_response.call_args) == 2)
        self.assertTrue(len(self.ips.send_response.call_args[0]) == 5)
        self.assertTrue(len(actions['results']['search_results']) == 0)
        self.assertTrue(actions['results']['operationSucceeded'])
        
        for line in actions['results']['table_html'].split('\n'):
            if 'Showing' in line:
                self.assertTrue(line.strip() == 'Showing %d - %d of %s' % (results_count - self.ips.sparql_limit, results_count, results_count))
                
        # Simulate "last"
        data['offset'] = results_count - self.ips.sparql_limit
        self.ips.process_search_syn_bio_hub([],[])
        
        actions = json.loads(self.ips.send_response.call_args[0][2])
        self.assertTrue(len(self.ips.send_response.call_args) == 2)
        self.assertTrue(len(self.ips.send_response.call_args[0]) == 5)
        self.assertTrue(len(actions['results']['search_results']) == 0)
        self.assertTrue(actions['results']['operationSucceeded'])
        
        for line in actions['results']['table_html'].split('\n'):
            if 'Showing' in line:
                self.assertTrue(line.strip() == 'Showing %d - %d of %s' % (results_count - self.ips.sparql_limit, results_count, results_count))
                
        # Previous
        data['offset'] = data['offset'] - self.ips.sparql_limit
        self.ips.process_search_syn_bio_hub([],[])
        
        actions = json.loads(self.ips.send_response.call_args[0][2])
        self.assertTrue(len(self.ips.send_response.call_args) == 2)
        self.assertTrue(len(self.ips.send_response.call_args[0]) == 5)
        self.assertTrue(len(actions['results']['search_results']) == 0)
        self.assertTrue(actions['results']['operationSucceeded'])
        
        for line in actions['results']['table_html'].split('\n'):
            if 'Showing' in line:
                self.assertTrue(line.strip() == 'Showing %d - %d of %s' % (results_count -  2 * self.ips.sparql_limit, results_count -  1 * self.ips.sparql_limit, results_count))
                
        # Previous
        data['offset'] = data['offset'] - self.ips.sparql_limit
        self.ips.process_search_syn_bio_hub([],[])
        
        actions = json.loads(self.ips.send_response.call_args[0][2])
        self.assertTrue(len(self.ips.send_response.call_args) == 2)
        self.assertTrue(len(self.ips.send_response.call_args[0]) == 5)
        self.assertTrue(len(actions['results']['search_results']) == 0)
        self.assertTrue(actions['results']['operationSucceeded'])
        
        for line in actions['results']['table_html'].split('\n'):
            if 'Showing' in line:
                self.assertTrue(line.strip() == 'Showing %d - %d of %s' % (results_count -  3 * self.ips.sparql_limit, results_count -  2 * self.ips.sparql_limit, results_count))
                
        # Next
        data['offset'] = data['offset'] + self.ips.sparql_limit
        self.ips.process_search_syn_bio_hub([],[])
        
        actions = json.loads(self.ips.send_response.call_args[0][2])
        self.assertTrue(len(self.ips.send_response.call_args) == 2)
        self.assertTrue(len(self.ips.send_response.call_args[0]) == 5)
        self.assertTrue(len(actions['results']['search_results']) == 0)
        self.assertTrue(actions['results']['operationSucceeded'])
        
        for line in actions['results']['table_html'].split('\n'):
            if 'Showing' in line:
                self.assertTrue(line.strip() == 'Showing %d - %d of %s' % (results_count -  2 * self.ips.sparql_limit, results_count -  1 * self.ips.sparql_limit, results_count))
                
        # First
        data['offset'] = 0
        self.ips.process_search_syn_bio_hub([],[])
        
        actions = json.loads(self.ips.send_response.call_args[0][2])
        self.assertTrue(len(self.ips.send_response.call_args) == 2)
        self.assertTrue(len(self.ips.send_response.call_args[0]) == 5)
        self.assertTrue(len(actions['results']['search_results']) == 0)
        self.assertTrue(actions['results']['operationSucceeded'])
        
        for line in actions['results']['table_html'].split('\n'):
            if 'Showing' in line:
                self.assertTrue(line.strip() == 'Showing 0 - 5 of %d' % results_count)
        
    def tearDown(self):
        """
        Perform teardown.
        """
        self.ips.stop()
