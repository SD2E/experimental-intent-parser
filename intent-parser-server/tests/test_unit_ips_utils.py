import unittest
import warnings
import json
import getopt
import sys
import os
import time
import urllib.request
import pickle

import intent_parser_utils

from intent_parser_utils import IPSMatch

from unittest.mock import Mock, patch, DEFAULT

try:
    from intent_parser_server import IntentParserServer
except Exception as e:
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../src'))
    from intent_parser_server import IntentParserServer

from google_accessor import GoogleAccessor

class TestIntentParserServer(unittest.TestCase):

    spellcheckFile = 'doc_1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA.json'

    items_json = 'item-map-sd2dict.json'

    dataDir = 'data'

    def setUp(self):
        """
        Configure an instance of IntentParserServer for spellcheck testing.
        """
        pass


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
        search_results = [{"paragraph_index" : 0, "offset": 4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 2, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 3, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'}]

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = intent_parser_utils.find_overlaps(start_idx, search_results)

            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            self.assertTrue(len(overlaps) == 1)
            self.assertTrue(max_idx == start_idx)
            self.assertTrue(overlaps[0] == search_results[start_idx])

        ####################################
        # Test for no overlaps
        search_results = [{"paragraph_index" : 0, "offset": 4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 18, "end_offset" : 25, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 26, "end_offset" : 30, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 32, "end_offset" : 35, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 38, "end_offset" : 40, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 2, "offset": 4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 2, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 2, "offset": 18, "end_offset" : 20, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 2, "offset": 22, "end_offset" : 30, 'term' : 'test', 'text' : 'text'},
                          ]

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = intent_parser_utils.find_overlaps(start_idx, search_results)

            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            self.assertTrue(len(overlaps) == 1)
            self.assertTrue(max_idx == start_idx)
            self.assertTrue(overlaps[0] == search_results[start_idx])

        ####################################
        # Test for overlaps off the right end
        search_results = [{"paragraph_index" : 0, "offset":  4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 18, "end_offset" : 26, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset":  8, "end_offset" : 12, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 24, "end_offset" : 35, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45, 'term' : 'test', 'text' : 'text'},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 0, 1 : 7}

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = intent_parser_utils.find_overlaps(start_idx, search_results)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            if start_idx in match_idxs:
                self.assertTrue(max_idx == match_max_idx[start_idx])
                for m in matches[start_idx]:
                    self.assertTrue(search_results[m] in overlaps)
            else:
                self.assertTrue(len(overlaps) == 1)
                self.assertTrue(overlaps[0] == search_results[start_idx])

        # Reverse of previous test
        search_results = [{"paragraph_index" : 0, "offset":  8, "end_offset" : 12, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 24, "end_offset" : 35, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset":  4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 18, "end_offset" : 26, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45, 'term' : 'test', 'text' : 'text'},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 6, 1 : 1}

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = intent_parser_utils.find_overlaps(start_idx, search_results)
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
        search_results = [{"paragraph_index" : 0, "offset":  4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 18, "end_offset" : 26, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset":  2, "end_offset" :  6, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45, 'term' : 'test', 'text' : 'text'},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 0, 1 : 7}

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = intent_parser_utils.find_overlaps(start_idx, search_results)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            if start_idx in match_idxs:
                self.assertTrue(max_idx == match_max_idx[start_idx])
                for m in matches[start_idx]:
                    self.assertTrue(search_results[m] in overlaps)
            else:
                self.assertTrue(len(overlaps) == 1)
                self.assertTrue(overlaps[0] == search_results[start_idx])

        # Reverse of previous test
        search_results = [{"paragraph_index" : 0, "offset":  2, "end_offset" :  6, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset":  4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 18, "end_offset" : 26, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45, 'term' : 'test', 'text' : 'text'},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 6, 1 : 1}

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = intent_parser_utils.find_overlaps(start_idx, search_results)
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
        search_results = [{"paragraph_index" : 0, "offset":  3, "end_offset" :  5, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 12, "end_offset" : 18, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset":  2, "end_offset" :  6, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45, 'term' : 'test', 'text' : 'text'},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 6, 1 : 7}

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = intent_parser_utils.find_overlaps(start_idx, search_results)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            if start_idx in match_idxs:
                self.assertTrue(max_idx == match_max_idx[start_idx])
                for m in matches[start_idx]:
                    self.assertTrue(search_results[m] in overlaps)
            else:
                self.assertTrue(len(overlaps) == 1)
                self.assertTrue(overlaps[0] == search_results[start_idx])

        # Reverse of previous test
        search_results = [{"paragraph_index" : 0, "offset":  2, "end_offset" :  6, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset":  3, "end_offset" :  5, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 12, "end_offset" : 18, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45, 'term' : 'test', 'text' : 'text'},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 0, 1 : 1}

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = intent_parser_utils.find_overlaps(start_idx, search_results)
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
        search_results = [{"paragraph_index" : 0, "offset":  0, "end_offset" :  8, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset":  8, "end_offset" : 22, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset":  2, "end_offset" :  6, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45, 'term' : 'test', 'text' : 'text'},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 0, 1 : 1}

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = intent_parser_utils.find_overlaps(start_idx, search_results)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            if start_idx in match_idxs:
                self.assertTrue(max_idx == match_max_idx[start_idx])
                for m in matches[start_idx]:
                    self.assertTrue(search_results[m] in overlaps)
            else:
                self.assertTrue(len(overlaps) == 1)
                self.assertTrue(overlaps[0] == search_results[start_idx])

        # Reverse of previous test
        search_results = [{"paragraph_index" : 0, "offset":  2, "end_offset" :  6, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset":  0, "end_offset" :  8, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset":  8, "end_offset" : 22, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45, 'term' : 'test', 'text' : 'text'},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 6, 1 : 7}

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = intent_parser_utils.find_overlaps(start_idx, search_results)
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
        search_results = [{"paragraph_index" : 0, "offset":  0, "end_offset" :  8, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset":  8, "end_offset" : 22, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset":  2, "end_offset" :  6, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45, 'term' : 'test', 'text' : 'text'},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 0, 1 : 1}
        ignore_idx = [6,7]
        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = intent_parser_utils.find_overlaps(start_idx, search_results, ignore_idx)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            self.assertTrue(len(overlaps) == 1)
            self.assertTrue(overlaps[0] == search_results[start_idx])

        # Reverse of previous test
        search_results = [{"paragraph_index" : 0, "offset":  2, "end_offset" :  6, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 10, "end_offset" : 20, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset":  4, "end_offset" : 10, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 12, "end_offset" : 16, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 18, "end_offset" : 25, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 1, "offset": 26, "end_offset" : 30, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset":  0, "end_offset" :  8, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset":  8, "end_offset" : 22, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 35, "end_offset" : 40, 'term' : 'test', 'text' : 'text'},
                          {"paragraph_index" : 0, "offset": 40, "end_offset" : 45, 'term' : 'test', 'text' : 'text'},
                          ]
        match_idxs = [0, 1]
        matches = {0 : [0,6], 1 : [1,7]}
        match_max_idx = {0 : 6, 1 : 7}
        ignore_idx = [6,7]

        for start_idx in range(len(search_results)):
            overlaps, max_idx, overlap_idx = intent_parser_utils.find_overlaps(start_idx, search_results, ignore_idx)
            self.assertTrue(overlaps == self.get_idx_for_search(search_results, overlap_idx))
            self.assertTrue(len(overlaps) == 1)
            self.assertTrue(overlaps[0] == search_results[start_idx])


    def test_find_text(self):
        """
        Basic check, ensure that spellcheck runs and the results are as expected
        """
        # Basic sanity checks
        partial_match_min_size = 3
        partial_match_thresh = 0.75

        #####
        # Refuse a match when the dict term has a match, but the larger term is too large
        text = 'M9'
        paragraphs = [{'elements': [{'startIndex': 5696, 'endIndex': 5710, 'textRun': {'content': 'M9_glucose_CAA', 'textStyle': {'underline': True, 'foregroundColor': {'color': {'rgbColor': {'red': 0.06666667, 'green': 0.33333334, 'blue': 0.8}}}, 'link': {'url': 'https://hub.sd2e.org/user/sd2e/design/M9_glucose_CAA/1'}}}}, {'startIndex': 5710, 'endIndex': 5712, 'textRun': {'content': ' \n', 'textStyle': {}}}], 'paragraphStyle': {'namedStyleType': 'NORMAL_TEXT', 'lineSpacing': 100, 'direction': 'LEFT_TO_RIGHT', 'spacingMode': 'COLLAPSE_LISTS', 'avoidWidowAndOrphan': False}}]
        abs_start_offset = 5693

        results = intent_parser_utils.find_text(text, abs_start_offset, paragraphs, partial_match_min_size, partial_match_thresh)

        self.assertTrue(len(results) == 0)

        #####
        # Refuse a match when the dict term and content are the same, the content is linked, and the link matches
        text = 'MG1655_LPV3_LacI_Sensor_pTac_AmeR_pAmeR_YFP'
        abs_start_offset = 0
        paragraphs = [{'elements': [{'startIndex': 196, 'endIndex': 229, 'textRun': {'content': 'MG1655_LPV3_LacI_Sensor_pTac_AmeR', 'textStyle': {'underline': True, 'foregroundColor': {'color': {'rgbColor': {'red': 0.06666667, 'green': 0.33333334, 'blue': 0.8}}}, 'fontSize': {'magnitude': 10, 'unit': 'PT'}, 'link': {'url': 'https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3_LacI_Sensor_pTac_AmeR/1'}}}}, {'startIndex': 229, 'endIndex': 230, 'textRun': {'content': '\n', 'textStyle': {'bold': True}}}], 'paragraphStyle': {'namedStyleType': 'NORMAL_TEXT', 'lineSpacing': 115, 'direction': 'LEFT_TO_RIGHT', 'avoidWidowAndOrphan': False}}]

        results = intent_parser_utils.find_text(text, abs_start_offset, paragraphs, partial_match_min_size, partial_match_thresh)

        self.assertTrue(len(results) == 0)

        #####
        # Make a match when the dict term and content are the same, the content is linked, but the link differs
        text = 'M9 Media Salts'
        abs_start_offset = 0
        paragraphs = [{'elements': [{'startIndex': 5147, 'endIndex': 5161, 'textRun': {'content': 'M9 media salts', 'textStyle': {'underline': True, 'foregroundColor': {'color': {'rgbColor': {'red': 0.06666667, 'green': 0.33333334, 'blue': 0.8}}}, 'fontSize': {'magnitude': 11.5, 'unit': 'PT'}, 'link': {'url': 'https://hub.sd2e.org/user/sd2e/design/teknova_M1902/1'}}}}, {'startIndex': 5161, 'endIndex': 5249, 'textRun': {'content': ' (6.78 g/L Na2HPO4, 3 g/L KH2PO4, 1 g/L NH4Cl, 0.5 g/L NaCl; Sigma- Aldrich, MO, M6030)\n', 'textStyle': {'fontSize': {'magnitude': 11.5, 'unit': 'PT'}}}}], 'paragraphStyle': {'namedStyleType': 'NORMAL_TEXT', 'direction': 'LEFT_TO_RIGHT', 'spacingMode': 'COLLAPSE_LISTS', 'indentFirstLine': {'magnitude': 18, 'unit': 'PT'}, 'indentStart': {'magnitude': 36, 'unit': 'PT'}}, 'bullet': {'listId': 'kix.ppm0fwxp8ech', 'textStyle': {'fontSize': {'magnitude': 11.5, 'unit': 'PT'}}}}]

        results = intent_parser_utils.find_text(text, abs_start_offset, paragraphs, partial_match_min_size, partial_match_thresh)

        self.assertTrue(len(results) == 1)
        
        text = 'MG1655'
        abs_start_offset = 0
        paragraphs = [{"elements": [
            {
              "startIndex": 3645,
              "endIndex": 3676,
              "textRun": {
                "content": "1- a control strain (Wild-type ",
                "textStyle": {}
              }
            },
            {
              "startIndex": 3676,
              "endIndex": 3682,
              "textRun": {
                "content": "MG1655",
                "textStyle": {}
              }
            },
            {
              "startIndex": 3682,
              "endIndex": 3684,
              "textRun": {
                "content": ")\n",
                "textStyle": {}
              }
            }
          ]}]

        #####
        # Refuse a match when the dict term has a match, but the larger term is too large
        text = 'pTac'
        abs_start_offset = 0
        paragraphs = [{'elements': [{'startIndex': 196, 'endIndex': 229, 'textRun': {'content': 'MG1655_LPV3_LacI_Sensor_pTac_AmeR', 'textStyle': {'underline': True, 'foregroundColor': {'color': {'rgbColor': {'red': 0.06666667, 'green': 0.33333334, 'blue': 0.8}}}, 'fontSize': {'magnitude': 10, 'unit': 'PT'}}}}, {'startIndex': 229, 'endIndex': 230, 'textRun': {'content': '\n', 'textStyle': {'bold': True}}}], 'paragraphStyle': {'namedStyleType': 'NORMAL_TEXT', 'lineSpacing': 115, 'direction': 'LEFT_TO_RIGHT', 'avoidWidowAndOrphan': False}}]

        results = intent_parser_utils.find_text(text, abs_start_offset, paragraphs, partial_match_min_size, partial_match_thresh)

        self.assertTrue(len(results) == 0)
        
        #####
        # Refuse a match when the dict term has a match, but it is too small
        text = 'YG_plasmid_002'
        abs_start_offset = 0
        paragraphs = [{'elements': [{'startIndex': 196, 'endIndex': 229, 'textRun': {'content': 'plasmid', 'textStyle': {'underline': True, 'foregroundColor': {'color': {'rgbColor': {'red': 0.06666667, 'green': 0.33333334, 'blue': 0.8}}}, 'fontSize': {'magnitude': 10, 'unit': 'PT'}}}}, {'startIndex': 229, 'endIndex': 230, 'textRun': {'content': '\n', 'textStyle': {'bold': True}}}], 'paragraphStyle': {'namedStyleType': 'NORMAL_TEXT', 'lineSpacing': 115, 'direction': 'LEFT_TO_RIGHT', 'avoidWidowAndOrphan': False}}]

        results = intent_parser_utils.find_text(text, abs_start_offset, paragraphs, partial_match_min_size, partial_match_thresh)

        self.assertTrue(len(results) == 0)

    def test_find_common_substrings(self):
        """
        Basic check, ensure that spellcheck runs and the results are as expected
        """

        ############
        content = 'm9 + glucose + caa:\n'
        term = 'm9'
        matches = intent_parser_utils.find_common_substrings(content.lower(), term.lower(), IntentParserServer.partial_match_min_size, IntentParserServer.partial_match_thresh)
        self.assertTrue(len(matches) == 1)
        self.assertTrue(matches[0].size == 2)
        self.assertTrue(matches[0].content_word_length == 2)

        ############
        content = '}, plate_{proteomics} \n'
        term = 'proteomics' 
        matches = intent_parser_utils.find_common_substrings(content.lower(), term.lower(), IntentParserServer.partial_match_min_size, IntentParserServer.partial_match_thresh)
        self.assertTrue(len(matches) == 1)
        self.assertTrue(matches[0].size == 10)
        self.assertTrue(matches[0].content_word_length == 10)
        
        ############
        content = 'Dna roteomics arabinose proteom arabinose\n'
        term = 'L-arabinose'
        matches = intent_parser_utils.find_common_substrings(content.lower(), term.lower(), IntentParserServer.partial_match_min_size, IntentParserServer.partial_match_thresh)

        gt_match = [IPSMatch(a=14, b=2, size=9, content_word_length=9), IPSMatch(a=32, b=2, size=9, content_word_length=9)]
        self.assertTrue(len(matches) == 2)
        self.assertTrue(gt_match == matches)

        ############
        content = 'Dna roteomics arabinose proteom arabinose\n'
        term = 'proteomics'
        matches = intent_parser_utils.find_common_substrings(content.lower(), term.lower(), IntentParserServer.partial_match_min_size, IntentParserServer.partial_match_thresh)

        gt_match = [IPSMatch(a=4, b=1, size=9, content_word_length=9), IPSMatch(a=24, b=0, size=7, content_word_length=7)]
        self.assertTrue(len(matches) == 2)
        self.assertTrue(gt_match == matches)
        
        ############
        content = 'Dna roteomics arabinose proteom arabinose\n'
        term = 'proteo'
        matches = intent_parser_utils.find_common_substrings(content.lower(), term.lower(), IntentParserServer.partial_match_min_size, IntentParserServer.partial_match_thresh)

        gt_match = [IPSMatch(a=4, b=1, size=5, content_word_length=9), IPSMatch(a=24, b=0, size=6, content_word_length=7)]
        self.assertTrue(len(matches) == 2)
        self.assertTrue(gt_match == matches)

        ############
        content = 'arabinose\n'
        term = 'L-arabinose'
        matches = intent_parser_utils.find_common_substrings(content.lower(), term.lower(), IntentParserServer.partial_match_min_size, IntentParserServer.partial_match_thresh)

        gt_match = [IPSMatch(a=0, b=2, size=9, content_word_length=9)]
        self.assertTrue(len(matches) == 1)
        self.assertTrue(gt_match == matches)

    def tearDown(self):
        """
        Perform teardown.
        """
        pass
        


if __name__ == '__main__':
    print('Run unit tests')

    unittest.main(argv=[sys.argv[0]])
