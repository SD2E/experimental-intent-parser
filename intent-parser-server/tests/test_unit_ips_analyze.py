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


class TestIntentParserServer(unittest.TestCase):

    spellcheckFile = 'doc_1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA.json'

    searchResults = 'search_results.pickle'
    
    expected_search_size = 33

    proteomics_search_size = 19
    
    items_json = 'item-map-test.json'

    dataDir = 'data'

    def setUp(self):
        """
        Configure an instance of IntentParserServer for spellcheck testing.
        """

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
        self.ips.client_state_lock = Mock()
        self.ips.client_state_map = {}
        self.ips.google_accessor = Mock()
        self.ips.google_accessor.get_document = Mock(return_value=self.doc_content)
        self.ips.send_response = Mock()
        self.ips.get_json_body = Mock(return_value=self.json_body)
        
        self.ips.item_map_lock = Mock()
        with open(os.path.join(self.dataDir, self.items_json), 'r') as fin:
            self.ips.item_map = json.load(fin)

        self.ips.process_analyze_document([], [])

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

    def test_analyze_yes(self):
        """
        """
        numResults = len(self.ips.client_state_map[self.doc_id]['search_results'])
        while self.ips.client_state_map[self.doc_id]['search_result_index'] < numResults :
            result = self.ips.process_analyze_yes([], self.ips.client_state_map[self.doc_id])
            #self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'], idx)
            self.assertTrue(len(result) == 3)

        result = self.ips.process_analyze_yes([], self.ips.client_state_map[self.doc_id])
        self.assertTrue(len(result) == 1)
        
    def test_analyze_no(self):
        """
        """
        numResults = len(self.ips.client_state_map[self.doc_id]['search_results'])
        while self.ips.client_state_map[self.doc_id]['search_result_index'] < numResults :
            result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
            #self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'] == idx + 1)
            self.assertTrue(len(result) == 2 )

        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        self.assertTrue(len(result) == 0 )

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
        self.assertTrue(len(result) == 0)

    def test_analyze_link_all(self):
        """
        """
        # Skip first term, engineered
        #result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        #self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'] == 1)
        #self.assertTrue(len(result) == 2)

        result = self.ips.process_link_all([], self.ips.client_state_map[self.doc_id])
        # We should have a link action for each of the 16 instances of proteomics in the results.
        # Plus a highlight text and showSidebar for the last remaining engineered result
        self.assertTrue(len(result) == self.proteomics_search_size + 2)

    def get_idx_for_search(self, search_results, comp):
        """
        Given a list of results from a search_results list, return the corresponding indices
        """
        return [search_results[c] for c in comp]

    def test_find_overlaps(self):
        """
        """
        ####################################
        # Test cases with wrong paragraph indices, expected no overlaps
        search_results = [{"paragraph_index" : 0, "offset": 4, "end_offset" : 10},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16},
                          {"paragraph_index" : 2, "offset": 12, "end_offset" : 16},
                          {"paragraph_index" : 3, "offset": 12, "end_offset" : 16}]

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = self.ips.find_overlaps(start_idx, search_results)

            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            self.assertTrue(len(overlaps) == 1)
            self.assertTrue(max_idx == start_idx)
            self.assertTrue(overlaps[0] == search_results[start_idx])

        ####################################
        # Test for no overlaps
        search_results = [{"paragraph_index" : 0, "offset": 4, "end_offset" : 10},
                          {"paragraph_index" : 0, "offset": 12, "end_offset" : 16},
                          {"paragraph_index" : 1, "offset": 4, "end_offset" : 10},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30},
                          {"paragraph_index" : 0, "offset": 18, "end_offset" : 25},
                          {"paragraph_index" : 0, "offset": 26, "end_offset" : 30},
                          {"paragraph_index" : 0, "offset": 32, "end_offset" : 35},
                          {"paragraph_index" : 0, "offset": 38, "end_offset" : 40},
                          {"paragraph_index" : 2, "offset": 4, "end_offset" : 10},
                          {"paragraph_index" : 2, "offset": 12, "end_offset" : 16},
                          {"paragraph_index" : 2, "offset": 18, "end_offset" : 20},
                          {"paragraph_index" : 2, "offset": 22, "end_offset" : 30},
                          ]

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = self.ips.find_overlaps(start_idx, search_results)

            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            self.assertTrue(len(overlaps) == 1)
            self.assertTrue(max_idx == start_idx)
            self.assertTrue(overlaps[0] == search_results[start_idx])

        ####################################
        # Test for overlaps off the right end
        search_results = [{"paragraph_index" : 0, "offset":  4, "end_offset" : 10},
                          {"paragraph_index" : 0, "offset": 18, "end_offset" : 26},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30},
                          {"paragraph_index" : 0, "offset":  8, "end_offset" : 12},
                          {"paragraph_index" : 0, "offset": 24, "end_offset" : 35},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 0, 1 : 7}

        # Reverse of previous test
        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = self.ips.find_overlaps(start_idx, search_results)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            if start_idx in match_idxs:
                self.assertTrue(max_idx == match_max_idx[start_idx])
                for m in matches[start_idx]:
                    self.assertTrue(search_results[m] in overlaps)
            else:
                self.assertTrue(len(overlaps) == 1)
                self.assertTrue(overlaps[0] == search_results[start_idx])

        search_results = [{"paragraph_index" : 0, "offset":  8, "end_offset" : 12},
                          {"paragraph_index" : 0, "offset": 24, "end_offset" : 35},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30},
                          {"paragraph_index" : 0, "offset":  4, "end_offset" : 10},
                          {"paragraph_index" : 0, "offset": 18, "end_offset" : 26},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 6, 1 : 1}

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = self.ips.find_overlaps(start_idx, search_results)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            if start_idx in match_idxs:
                self.assertTrue(max_idx == match_max_idx[start_idx])
                for m in matches[start_idx]:
                    self.assertTrue(search_results[m] in overlaps)
            else:
                self.assertTrue(len(overlaps) == 1)
                self.assertTrue(overlaps[0] == search_results[start_idx])

        ####################################
        # Test for overlaps off the left end
        search_results = [{"paragraph_index" : 0, "offset":  4, "end_offset" : 10},
                          {"paragraph_index" : 0, "offset": 18, "end_offset" : 26},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30},
                          {"paragraph_index" : 0, "offset":  2, "end_offset" :  6},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 0, 1 : 7}

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = self.ips.find_overlaps(start_idx, search_results)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            if start_idx in match_idxs:
                self.assertTrue(max_idx == match_max_idx[start_idx])
                for m in matches[start_idx]:
                    self.assertTrue(search_results[m] in overlaps)
            else:
                self.assertTrue(len(overlaps) == 1)
                self.assertTrue(overlaps[0] == search_results[start_idx])

        # Reverse of previous test
        search_results = [{"paragraph_index" : 0, "offset":  2, "end_offset" :  6},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30},
                          {"paragraph_index" : 0, "offset":  4, "end_offset" : 10},
                          {"paragraph_index" : 0, "offset": 18, "end_offset" : 26},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 6, 1 : 1}

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = self.ips.find_overlaps(start_idx, search_results)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            if start_idx in match_idxs:
                self.assertTrue(max_idx == match_max_idx[start_idx])
                for m in matches[start_idx]:
                    self.assertTrue(search_results[m] in overlaps)
            else:
                self.assertTrue(len(overlaps) == 1)
                self.assertTrue(overlaps[0] == search_results[start_idx])

        ####################################
        # Test for overlaps query inside comp
        search_results = [{"paragraph_index" : 0, "offset":  3, "end_offset" :  5},
                          {"paragraph_index" : 0, "offset": 12, "end_offset" : 18},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30},
                          {"paragraph_index" : 0, "offset":  2, "end_offset" :  6},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 6, 1 : 7}

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = self.ips.find_overlaps(start_idx, search_results)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            if start_idx in match_idxs:
                self.assertTrue(max_idx == match_max_idx[start_idx])
                for m in matches[start_idx]:
                    self.assertTrue(search_results[m] in overlaps)
            else:
                self.assertTrue(len(overlaps) == 1)
                self.assertTrue(overlaps[0] == search_results[start_idx])

        # Reverse of previous test
        search_results = [{"paragraph_index" : 0, "offset":  2, "end_offset" :  6},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30},
                          {"paragraph_index" : 0, "offset":  3, "end_offset" :  5},
                          {"paragraph_index" : 0, "offset": 12, "end_offset" : 18},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 0, 1 : 1}

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = self.ips.find_overlaps(start_idx, search_results)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            if start_idx in match_idxs:
                self.assertTrue(max_idx == match_max_idx[start_idx])
                for m in matches[start_idx]:
                    self.assertTrue(search_results[m] in overlaps)
            else:
                self.assertTrue(len(overlaps) == 1)
                self.assertTrue(overlaps[0] == search_results[start_idx])

        ####################################
        # Test for overlaps comp inside query
        search_results = [{"paragraph_index" : 0, "offset":  0, "end_offset" :  8},
                          {"paragraph_index" : 0, "offset":  8, "end_offset" : 22},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30},
                          {"paragraph_index" : 0, "offset":  2, "end_offset" :  6},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 0, 1 : 1}

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = self.ips.find_overlaps(start_idx, search_results)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            if start_idx in match_idxs:
                self.assertTrue(max_idx == match_max_idx[start_idx])
                for m in matches[start_idx]:
                    self.assertTrue(search_results[m] in overlaps)
            else:
                self.assertTrue(len(overlaps) == 1)
                self.assertTrue(overlaps[0] == search_results[start_idx])

        # Reverse of previous test
        search_results = [{"paragraph_index" : 0, "offset":  2, "end_offset" :  6},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30},
                          {"paragraph_index" : 0, "offset":  0, "end_offset" :  8},
                          {"paragraph_index" : 0, "offset":  8, "end_offset" : 22},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 6, 1 : 7}

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = self.ips.find_overlaps(start_idx, search_results)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            if start_idx in match_idxs:
                self.assertTrue(max_idx == match_max_idx[start_idx])
                for m in matches[start_idx]:
                    self.assertTrue(search_results[m] in overlaps)
            else:
                self.assertTrue(len(overlaps) == 1)
                self.assertTrue(overlaps[0] == search_results[start_idx])

        ####################################
        # Test ignore idx
        search_results = [{"paragraph_index" : 0, "offset":  0, "end_offset" :  8},
                          {"paragraph_index" : 0, "offset":  8, "end_offset" : 22},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30},
                          {"paragraph_index" : 0, "offset":  2, "end_offset" :  6},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 0, 1 : 1}
        ignore_idx = [6,7]
        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = self.ips.find_overlaps(start_idx, search_results, ignore_idx)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            self.assertTrue(len(overlaps) == 1)
            self.assertTrue(overlaps[0] == search_results[start_idx])

        # Reverse of previous test
        search_results = [{"paragraph_index" : 0, "offset":  2, "end_offset" :  6},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30},
                          {"paragraph_index" : 0, "offset":  0, "end_offset" :  8},
                          {"paragraph_index" : 0, "offset":  8, "end_offset" : 22},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 6, 1 : 7}
        ignore_idx = [6,7]

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = self.ips.find_overlaps(start_idx, search_results, ignore_idx)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            self.assertTrue(len(overlaps) == 1)
            self.assertTrue(overlaps[0] == search_results[start_idx])

    def tearDown(self):
        """
        Perform teardown.
        """
        self.ips.stop()


if __name__ == '__main__':
    print('Run unit tests')

    unittest.main(argv=[sys.argv[0]])
