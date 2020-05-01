from intent_parser.intent_parser_sbh import IntentParserSBH
from intent_parser.server.intent_parser_server import IntentParserServer
from intent_parser.accessor.sbol_dictionary_accessor import SBOLDictionaryAccessor
from intent_parser.accessor.strateos_accessor import StrateosAccessor
from unittest.mock import Mock
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.utils.intent_parser_utils as intent_parser_utils
import json
import os
import unittest

@unittest.skip("Skip for refactoring")
class IntegrationSbhTest(unittest.TestCase):

    spellcheckFile = 'doc_1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA.json'

    dataDir = 'data'

    template_spreadsheet_id = '1r3CIyv75vV7A7ghkB0od-TM_16qSYd-byAbQ1DhRgB0'
    
    template_sheet_last_rev = '2019-06-12T20:29:13.519Z'

    def setUp(self):
        """
        Configure an instance of IntentParserServer for spellcheck testing.
        """
   
        creds = intent_parser_utils.load_json_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sbh_creds.json'))
        sbh_collection_uri = 'https://hub-staging.sd2e.org/user/sd2e/src/intent_parser_collection/1'

        sbh = IntentParserSBH(sbh_collection_uri=sbh_collection_uri,
                 sbh_spoofing_prefix='https://hub.sd2e.org',
                 spreadsheet_id=intent_parser_constants.UNIT_TEST_SPREADSHEET_ID,
                 sbh_username=creds['username'], 
                 sbh_password=creds['password'])
        
        sbol_dictionary = SBOLDictionaryAccessor(intent_parser_constants.UNIT_TEST_SPREADSHEET_ID, sbh)
        strateos_accessor = StrateosAccessor()
        intent_parser_server = IntentParserServer(sbh, sbol_dictionary, strateos_accessor,
                                       bind_ip='localhost',
                                       bind_port=8081)
         
        self.doc_content = None
        with open(os.path.join(self.dataDir,self.spellcheckFile), 'r') as fin:
            self.doc_content = json.loads(fin.read())

        if self.doc_content is None:
            self.fail('Failed to read in test document! Path: ' + os.path.join(self.dataDir,self.spellcheckFile))

        self.ips.initialize_server()
        self.ips.start(background=True) 
        
        self.ips.google_accessor = Mock()
        self.ips.google_accessor.get_document = Mock(return_value=self.doc_content)
        self.ips.send_response = Mock()

    def test_add_sbh_no_results(self):
        """
        Integration test for Add to SynbioHub feature
        """
        expected_results = 0
        term = 'proteomics'
        self.add_sbh_test_func(term, expected_results)

    def test_add_sbh_with_results(self):
        """
        Integration test for Add to SynbioHub feature
        """
        expected_results = intent_parser_constants.SPARQL_LIMIT
        term = 'MG1655'
        self.add_sbh_test_func(term, expected_results)

    def add_sbh_test_func(self, term, expected_results):
        """
        Integration test for Add to SynbioHub feature
        """
        data = {'term' : term, 'offset' : 0}
        self.json_body = {'data' : data}
        self.ips.get_json_body = Mock(return_value=self.json_body)

        self.ips.process_search_syn_bio_hub([],[])

        results_count = self.ips.sparql_similar_count_cache[term]
        results_count = int(results_count)

        actions = json.loads(self.ips.send_response.call_args[0][1])
        self.assertTrue(len(self.ips.send_response.call_args) == 2)
        self.assertTrue(len(self.ips.send_response.call_args[0]) == 5)
        self.assertTrue(len(actions['results']['search_results']) == expected_results)
        self.assertTrue(actions['results']['operationSucceeded'])
        
        for line in actions['results']['table_html'].split('\n'):
            if 'Showing' in line:
                self.assertTrue(line.strip() == 'Showing 0 - 5 of %d' % results_count)
        
        # Test value that's larger than results
        data['offset'] = results_count + 10
        self.ips.process_search_syn_bio_hub([],[])
        
        actions = json.loads(self.ips.send_response.call_args[0][1])
        self.assertTrue(len(self.ips.send_response.call_args) == 2)
        self.assertTrue(len(self.ips.send_response.call_args[0]) == 5)
        self.assertTrue(len(actions['results']['search_results']) == expected_results)
        self.assertTrue(actions['results']['operationSucceeded'])
        
        for line in actions['results']['table_html'].split('\n'):
            if 'Showing' in line:
                self.assertTrue(line.strip() == 'Showing %d - %d of %s' % (max(0,results_count - self.ips.sparql_limit), max(5,results_count), results_count))
                
        # Simulate "last"
        data['offset'] = results_count - self.ips.sparql_limit
        self.ips.process_search_syn_bio_hub([],[])
        
        actions = json.loads(self.ips.send_response.call_args[0][1])
        self.assertTrue(len(self.ips.send_response.call_args) == 2)
        self.assertTrue(len(self.ips.send_response.call_args[0]) == 5)
        self.assertTrue(len(actions['results']['search_results']) == expected_results)
        self.assertTrue(actions['results']['operationSucceeded'])
        
        for line in actions['results']['table_html'].split('\n'):
            if 'Showing' in line:
                self.assertTrue(line.strip() == 'Showing %d - %d of %s' % (max(0,results_count - self.ips.sparql_limit), max(5,results_count), results_count))
                
        # Previous
        data['offset'] = data['offset'] - self.ips.sparql_limit
        self.ips.process_search_syn_bio_hub([],[])
        
        actions = json.loads(self.ips.send_response.call_args[0][1])
        self.assertTrue(len(self.ips.send_response.call_args) == 2)
        self.assertTrue(len(self.ips.send_response.call_args[0]) == 5)
        self.assertTrue(len(actions['results']['search_results']) == expected_results)
        self.assertTrue(actions['results']['operationSucceeded'])
        
        for line in actions['results']['table_html'].split('\n'):
            if 'Showing' in line:
                self.assertTrue(line.strip() == 'Showing %d - %d of %s' % (max(0,results_count - 2 * self.ips.sparql_limit), max(5,results_count -  1 * self.ips.sparql_limit), results_count))
                
        # Previous
        data['offset'] = data['offset'] - self.ips.sparql_limit
        self.ips.process_search_syn_bio_hub([],[])
        
        actions = json.loads(self.ips.send_response.call_args[0][1])
        self.assertTrue(len(self.ips.send_response.call_args) == 2)
        self.assertTrue(len(self.ips.send_response.call_args[0]) == 5)
        self.assertTrue(len(actions['results']['search_results']) == expected_results)
        self.assertTrue(actions['results']['operationSucceeded'])
        
        for line in actions['results']['table_html'].split('\n'):
            if 'Showing' in line:
                self.assertTrue(line.strip() == 'Showing %d - %d of %s' % (max(0,results_count - 3 * self.ips.sparql_limit), max(5,results_count -  2 * self.ips.sparql_limit), results_count))
                
        # Next
        data['offset'] = data['offset'] + self.ips.sparql_limit
        self.ips.process_search_syn_bio_hub([],[])
        
        actions = json.loads(self.ips.send_response.call_args[0][1])
        self.assertTrue(len(self.ips.send_response.call_args) == 2)
        self.assertTrue(len(self.ips.send_response.call_args[0]) == 5)
        self.assertTrue(len(actions['results']['search_results']) == expected_results)
        self.assertTrue(actions['results']['operationSucceeded'])
        
        for line in actions['results']['table_html'].split('\n'):
            if 'Showing' in line:
                self.assertTrue(line.strip() == 'Showing %d - %d of %s' % (max(0,results_count - 2 * self.ips.sparql_limit), max(5,results_count -  1 * self.ips.sparql_limit), results_count))
                
        # First
        data['offset'] = 0
        self.ips.process_search_syn_bio_hub([],[])
        
        actions = json.loads(self.ips.send_response.call_args[0][1])
        self.assertTrue(len(self.ips.send_response.call_args) == 2)
        self.assertTrue(len(self.ips.send_response.call_args[0]) == 5)
        self.assertTrue(len(actions['results']['search_results']) == expected_results)
        self.assertTrue(actions['results']['operationSucceeded'])
        
        for line in actions['results']['table_html'].split('\n'):
            if 'Showing' in line:
                self.assertTrue(line.strip() == 'Showing 0 - 5 of %d' % results_count)


    def test_count_matches_results(self):
        """
        We run two SPARQL queries, one to get the count of results, and one to get a set limited to a value.
        We should ensure that the count query matches the result set query, otherwise badness can ensue.
        """

        # This is easiest is we find something with a result set that is less than the query limit
        # For this, I found L-arabinose works well
        term = 'L-arabinose'
        data = {'term' : term, 'offset' : 0}
        self.json_body = {'data' : data}
        self.ips.get_json_body = Mock(return_value=self.json_body)

        self.ips.process_search_syn_bio_hub([],[])

        results_count = self.ips.sparql_similar_count_cache[term]
        results_count = int(results_count)

        actions = json.loads(self.ips.send_response.call_args[0][1])
        self.assertTrue(results_count < intent_parser_constants.SPARQL_LIMIT)
        self.assertTrue(len(actions['results']['search_results']) == results_count)

    def tearDown(self):
        """
        Perform teardown.
        """
        self.ips.stop()
    
        
if __name__ == "__main__":
    unittest.main()
