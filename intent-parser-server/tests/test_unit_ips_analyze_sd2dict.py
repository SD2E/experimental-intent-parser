import unittest
import warnings
import json
import getopt
import sys
import os
import time
import urllib.request
import pickle

from ips_test_utils import compare_search_results

from unittest.mock import Mock, patch, DEFAULT

try:
    from intent_parser_server import IntentParserServer
except Exception as e:
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../src'))
    from intent_parser_server import IntentParserServer

from google_accessor import GoogleAccessor

@unittest.skip('Skip IpsAnalyzeSd2dict ')
class IpsAnalyzeSd2dictTest(unittest.TestCase):

    spellcheckFile = 'doc_1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA.json'

    searchResults = 'search_results_sd2dict.pickle'
    
    expected_search_size = 39
    
    items_json = 'item-map-sd2dict.json'

    dataDir = 'data'

    def setUp(self):
        """
        Configure an instance of IntentParserServer for spellcheck testing.
        """

        # Clear all link preferences
        if os.path.exists(IntentParserServer.link_pref_path):
            for file in os.listdir(IntentParserServer.link_pref_path):
                os.remove(os.path.join(IntentParserServer.link_pref_path, file))
            os.rmdir(IntentParserServer.link_pref_path)

        self.doc_content = None
        with open(os.path.join(self.dataDir,self.spellcheckFile), 'r') as fin:
            self.doc_content = json.loads(fin.read())

        if self.doc_content is None:
            self.fail('Failed to read in test document! Path: ' + os.path.join(self.dataDir,self.spellcheckFile))

        self.doc_id = '1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA'
        self.user = 'bbnTest'
        self.user_email = 'test@bbn.com'
        self.json_body = {'documentId' : self.doc_id, 'user' : self.user, 'userEmail' : self.user_email}

        self.ips = IntentParserServer(init_server=False, init_sbh=False)
        self.ips.analyze_processing_map_lock = Mock()
        self.ips.client_state_lock = Mock()
        self.ips.client_state_map = {}
        self.ips.google_accessor = Mock()
        self.ips.google_accessor.get_document = Mock(return_value=self.doc_content)
        self.ips.send_response = Mock()
        self.ips.get_json_body = Mock(return_value=self.json_body)
        self.ips.analyze_processing_map = {}
        self.ips.analyze_processing_lock = {}
        
        self.ips.item_map_lock = Mock()
        with open(os.path.join(self.dataDir, self.items_json), 'r') as fin:
            self.ips.item_map = json.load(fin)

        self.ips.process_analyze_document([], [])
        pa_results = json.loads(self.ips.send_response.call_args[0][2])
        actions = pa_results['actions']
        self.assertTrue(actions[0]['action'] == 'showProgressbar')

        startTime = time.time()
        while actions[0]['action'] != 'highlightText' and (time.time() - startTime < 100):
            self.ips.process_analyze_document([], [])
            pa_results = json.loads(self.ips.send_response.call_args[0][2])
            actions = pa_results['actions']
            self.assertTrue(actions[0]['action'] == 'highlightText' or actions[0]['action'] == 'updateProgress')
            time.sleep(0.25)

        self.assertTrue(actions[0]['action'] == 'highlightText')
        self.assertTrue(actions[1]['action'] == 'showSidebar')

        # Code to generate GT search results, for when test doc is updated
        #with open(os.path.join(self.dataDir, self.searchResults), 'wb') as fout:
        #    pickle.dump(self.ips.client_state_map[self.doc_id]['search_results'], fout)

        self.search_gt = None
        with open(os.path.join(self.dataDir, self.searchResults), 'rb') as fin:
            self.search_gt = pickle.load(fin)

        if self.search_gt is None:
            self.fail('Failed to read in spelling results! Path: ' + os.join(self.dataDir, self.spellcheckResults))
            
        compare_search_results(self.search_gt, self.ips.client_state_map[self.doc_id]['search_results'])

    def return_value(self, value):
        return value

    def test_maximal_search(self):
        """
        Test that the maximal search is finding different results.
        """
        culled_results = self.ips.client_state_map[self.doc_id]['search_results']
        self.ips.cull_overlapping = Mock(side_effect=self.return_value)

        self.ips.process_analyze_document([], [])
        pa_results = json.loads(self.ips.send_response.call_args[0][2])
        actions = pa_results['actions']
        self.assertTrue(actions[0]['action'] == 'showProgressbar')

        startTime = time.time()
        while actions[0]['action'] != 'highlightText' and (time.time() - startTime < 100):
            self.ips.process_analyze_document([], [])
            pa_results = json.loads(self.ips.send_response.call_args[0][2])
            actions = pa_results['actions']
            self.assertTrue(actions[0]['action'] == 'highlightText' or actions[0]['action'] == 'updateProgress')
            time.sleep(0.25)

        self.assertTrue(actions[0]['action'] == 'highlightText')
        self.assertTrue(actions[1]['action'] == 'showSidebar')

        unculled_results = self.ips.client_state_map[self.doc_id]['search_results']

        self.assertFalse(compare_search_results(unculled_results, culled_results))

    def test_analyze_basic(self):
        """
        Basic check, ensure that spellcheck runs and the results are as expected
        """
        # Basic sanity checks
        self.assertTrue(self.ips.client_state_map[self.doc_id]['document_id'] == self.doc_id)
        self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'] is 1)
        self.assertTrue(len(self.ips.client_state_map[self.doc_id]['search_results']) is self.expected_search_size)
        
        self.assertTrue(compare_search_results(self.search_gt, self.ips.client_state_map[self.doc_id]['search_results']), 'Search result sets do not match!')

    def test_analyze_process(self):
        """
        Test that goes through the whole results in some fashion
        """
        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        result = self.ips.process_analyze_yes({'data' : {'buttonId' : 'test'}}, self.ips.client_state_map[self.doc_id])
        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        result = self.ips.process_analyze_yes({'data' : {'buttonId' : 'test'}}, self.ips.client_state_map[self.doc_id])
        result = self.ips.process_no_to_all([], self.ips.client_state_map[self.doc_id])
        result = self.ips.process_analyze_yes({'data' : {'buttonId' : 'test'}}, self.ips.client_state_map[self.doc_id])
        result = self.ips.process_link_all({'data' : {'buttonId' : 'test'}}, self.ips.client_state_map[self.doc_id])
        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        
    def test_analyze_yes(self):
        """
        """
        numResults = len(self.ips.client_state_map[self.doc_id]['search_results'])
        while self.ips.client_state_map[self.doc_id]['search_result_index'] < numResults :
            result = self.ips.process_analyze_yes({'data' : {'buttonId' : 'test'}}, self.ips.client_state_map[self.doc_id])
            #self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'], idx)
            self.assertTrue(len(result) == 3)

        result = self.ips.process_analyze_yes({'data' : {'buttonId' : 'test'}}, self.ips.client_state_map[self.doc_id])
        self.assertTrue(len(result) == 2)
        
    def test_analyze_no(self):
        """
        """
        numResults = len(self.ips.client_state_map[self.doc_id]['search_results'])
        while self.ips.client_state_map[self.doc_id]['search_result_index'] < numResults :
            result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
            #self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'] == idx + 1)
            self.assertTrue(len(result) == 2 )

        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        self.assertTrue(len(result) == 1 )

    def test_analyze_no_to_all(self):
        """
        """
        # Skip first term, engineered
        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'] == 2)
        self.assertTrue(len(result) == 2 )

        # Ignore the next term, proteomics
        result = self.ips.process_no_to_all([], self.ips.client_state_map[self.doc_id])
        # We should have one result left after ignoring the 16 instances of proteomics in the results.
        self.assertTrue(len(result) == 2)
        # We should have no results left after ignoring the last item
        numResults = len(self.ips.client_state_map[self.doc_id]['search_results'])
        while self.ips.client_state_map[self.doc_id]['search_result_index'] < numResults :
            result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
            #self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'] == idx + 1)
            self.assertTrue(len(result) == 2 )

        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        self.assertTrue(len(result) == 1)

    def test_analyze_never_link(self):
        """
        """
        # Skip first term, engineered
        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'] == 2)
        self.assertTrue(len(result) == 2 )

        numResultsOrig = len(self.ips.client_state_map[self.doc_id]['search_results'])
        currResult = self.ips.client_state_map[self.doc_id]['search_results'][self.ips.client_state_map[self.doc_id]['search_result_index'] - 1]
        matchCount = 0;
        for result in self.ips.client_state_map[self.doc_id]['search_results']:
            if result['term'] == currResult['term'] and result['text'] == currResult['text']:
                matchCount += 1

        # Ignore the next term, proteomics
        result = self.ips.process_never_link([], self.ips.client_state_map[self.doc_id])
        # We should have one result left after ignoring the 16 instances of proteomics in the results.
        self.assertTrue(len(result) == 2)
        # We should have no results left after ignoring the last item
        numResults = len(self.ips.client_state_map[self.doc_id]['search_results'])
        self.assertTrue(numResults + matchCount == numResultsOrig)

        while self.ips.client_state_map[self.doc_id]['search_result_index'] < numResults :
            result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
            #self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'] == idx + 1)
            self.assertTrue(len(result) == 2 )

        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        self.assertTrue(len(result) == 1)

        # Rerun analysis
        self.ips.process_analyze_document([], [])
        pa_results = json.loads(self.ips.send_response.call_args[0][2])
        actions = pa_results['actions']
        self.assertTrue(actions[0]['action'] == 'showProgressbar')

        startTime = time.time()
        while actions[0]['action'] != 'highlightText' and (time.time() - startTime < 100):
            self.ips.process_analyze_document([], [])
            pa_results = json.loads(self.ips.send_response.call_args[0][2])
            actions = pa_results['actions']
            self.assertTrue(actions[0]['action'] == 'highlightText' or actions[0]['action'] == 'updateProgress')
            time.sleep(0.25)

        # We shouldn't link proteomics anymore, so it should remove it from the search results
        numResults = len(self.ips.client_state_map[self.doc_id]['search_results'])
        # Search result is the same, because we are removing links that overlap other matches
        self.assertTrue(numResults == (self.expected_search_size - matchCount))

        link_pref_file = os.path.join(self.ips.link_pref_path, 'test@bbn.com.json')
        self.assertTrue(os.path.exists(link_pref_file))

    def test_analyze_link_all(self):
        """
        """
        # Skip first term, engineered
        #result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        #self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'] == 1)
        #self.assertTrue(len(result) == 2)
        
        numResults = len(self.ips.client_state_map[self.doc_id]['search_results'])
        while self.ips.client_state_map[self.doc_id]['search_result_index'] < (numResults - 1):
            search_idx = self.ips.client_state_map[self.doc_id]['search_result_index'] - 1
            term = self.ips.client_state_map[self.doc_id]['search_results'][search_idx]['term']
            term_results = [t for t in self.ips.client_state_map[self.doc_id]['search_results'] if t['term'] == term]
    
            result = self.ips.process_link_all({'data' : {'buttonId' : 'test'}}, self.ips.client_state_map[self.doc_id])
            # We should have a link action for each of the 16 instances of proteomics in the results.
            # Plus a highlight text and showSidebar for the last remaining engineered result
            self.assertTrue(len(result) == len(term_results) + 2)
            for idx in range(len(result) - 2):
                lr = result[idx]
                sr = term_results[idx]
                self.assertTrue(lr['action'] == 'linkText')
                self.assertTrue(lr['paragraph_index'] == sr['paragraph_index'])
                self.assertTrue(lr['offset'] == sr['offset'])
                self.assertTrue(lr['end_offset'] == sr['end_offset'])

    def tearDown(self):
        """
        Perform teardown.
        """
        self.ips.stop()


if __name__ == '__main__':
    print('Run unit tests')

    unittest.main(argv=[sys.argv[0]])
