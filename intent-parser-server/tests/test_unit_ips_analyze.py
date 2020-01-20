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

from operator import itemgetter

from ips_test_utils import compare_search_results

from unittest.mock import Mock, patch, DEFAULT

from difflib import Match

try:
    from intent_parser_server import IntentParserServer
except Exception as e:
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../src'))
    from intent_parser_server import IntentParserServer

from google_accessor import GoogleAccessor


class IpsAnalyzeTest(unittest.TestCase):

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

    def test_maximal_search_ordering(self):
        """
        I found that with a certain order, some overlaps weren't being found.
        The issue is that, lets say indices 1&2 and 2&3 overlap.
        If 2 is the maximal, then it will get removed when it overlaps with 1, but then won't get considered as overlapping with 3, so 3 won't be removed.
        This test case covers that sitaution
        """

        # Hand-coded test case based on real data.  I found that the order of the results mattered for culling.
        unculled_input = [{'paragraph_index': 5, 'offset': 24, 'end_offset': 25, 'term': 'M9', 'uri': 'https://hub.sd2e.org/user/sd2e/design/M9/1', 'link': None, 'text': 'M9'},
 {'paragraph_index': 167, 'offset': 0, 'end_offset': 1, 'term': 'M9', 'uri': 'https://hub.sd2e.org/user/sd2e/design/M9/1', 'link': None, 'text': 'M9'},
 {'paragraph_index': 168, 'offset': 0, 'end_offset': 1, 'term': 'M9', 'uri': 'https://hub.sd2e.org/user/sd2e/design/M9/1', 'link': 'https://hub.sd2e.org/user/sd2e/design/teknova_M1902/1', 'text': 'M9'},
 {'paragraph_index': 5, 'offset': 24, 'end_offset': 37, 'term': 'M9 Media Salts', 'uri': 'https://hub.sd2e.org/user/sd2e/design/teknova_M1902/1', 'link': None, 'text': 'M9 media salts'},
 {'paragraph_index': 168, 'offset': 0, 'end_offset': 13, 'term': 'M9 Media Salts', 'uri': 'https://hub.sd2e.org/user/sd2e/design/teknova_M1902/1', 'link': 'https://hub.sd2e.org/user/sd2e/design/teknova_M1902/1', 'text': 'M9 media salts'},
 {'paragraph_index': 162, 'offset': 13, 'end_offset': 17, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'Media'},
 {'paragraph_index': 166, 'offset': 14, 'end_offset': 18, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'Media'},
 {'paragraph_index': 193, 'offset': 15, 'end_offset': 19, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'Media'},
 {'paragraph_index': 32, 'offset': 146, 'end_offset': 155, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 198, 'offset': 57, 'end_offset': 66, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 203, 'offset': 19, 'end_offset': 28, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 203, 'offset': 73, 'end_offset': 82, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 203, 'offset': 89, 'end_offset': 98, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 205, 'offset': 59, 'end_offset': 68, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 229, 'offset': 27, 'end_offset': 36, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 273, 'offset': 17, 'end_offset': 26, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 280, 'offset': 9, 'end_offset': 18, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 7, 'offset': 69, 'end_offset': 78, 'term': 'engineered', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/engineered/1', 'link': None, 'text': 'engineered'},
 {'paragraph_index': 12, 'offset': 0, 'end_offset': 9, 'term': 'engineered', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/engineered/1', 'link': None, 'text': 'engineered'},
 {'paragraph_index': 218, 'offset': 0, 'end_offset': 9, 'term': 'engineered', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/engineered/1', 'link': None, 'text': 'engineered'},
 {'paragraph_index': 5, 'offset': 27, 'end_offset': 31, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'media'},
 {'paragraph_index': 163, 'offset': 34, 'end_offset': 38, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'media'},
 {'paragraph_index': 164, 'offset': 31, 'end_offset': 35, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'media'},
 {'paragraph_index': 168, 'offset': 3, 'end_offset': 7, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': 'https://hub.sd2e.org/user/sd2e/design/teknova_M1902/1', 'text': 'media'},
 {'paragraph_index': 185, 'offset': 71, 'end_offset': 75, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'media'},
 {'paragraph_index': 186, 'offset': 37, 'end_offset': 41, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'media'},
 {'paragraph_index': 212, 'offset': 172, 'end_offset': 176, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'media'},
 {'paragraph_index': 5, 'offset': 39, 'end_offset': 45, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteom'},
 {'paragraph_index': 25, 'offset': 31, 'end_offset': 39, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteomic'},
 {'paragraph_index': 8, 'offset': 138, 'end_offset': 147, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteomics'},
 {'paragraph_index': 25, 'offset': 41, 'end_offset': 50, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteomics'},
 {'paragraph_index': 27, 'offset': 196, 'end_offset': 205, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteomics'},
 {'paragraph_index': 30, 'offset': 98, 'end_offset': 107, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteomics'},
 {'paragraph_index': 32, 'offset': 9, 'end_offset': 18, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'text': 'proteomics'},
 {'paragraph_index': 126, 'offset': 41, 'end_offset': 50, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteomics'},
 {'paragraph_index': 158, 'offset': 58, 'end_offset': 67, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteomics'},
 {'paragraph_index': 5, 'offset': 4, 'end_offset': 12, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'roteomics'}]

        culled_gt =  [{'paragraph_index': 5, 'offset': 4, 'end_offset': 12, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'roteomics'},
 {'paragraph_index': 5, 'offset': 24, 'end_offset': 37, 'term': 'M9 Media Salts', 'uri': 'https://hub.sd2e.org/user/sd2e/design/teknova_M1902/1', 'link': None, 'text': 'M9 media salts'},
 {'paragraph_index': 5, 'offset': 39, 'end_offset': 45, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteom'},
 {'paragraph_index': 7, 'offset': 69, 'end_offset': 78, 'term': 'engineered', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/engineered/1', 'link': None, 'text': 'engineered'},
 {'paragraph_index': 8, 'offset': 138, 'end_offset': 147, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteomics'},
 {'paragraph_index': 12, 'offset': 0, 'end_offset': 9, 'term': 'engineered', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/engineered/1', 'link': None, 'text': 'engineered'},
 {'paragraph_index': 25, 'offset': 31, 'end_offset': 39, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteomic'},
 {'paragraph_index': 25, 'offset': 41, 'end_offset': 50, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteomics'},
 {'paragraph_index': 27, 'offset': 196, 'end_offset': 205, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteomics'},
 {'paragraph_index': 30, 'offset': 98, 'end_offset': 107, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteomics'},
 {'paragraph_index': 32, 'offset': 9, 'end_offset': 18, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'text': 'proteomics'},
 {'paragraph_index': 32, 'offset': 146, 'end_offset': 155, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 126, 'offset': 41, 'end_offset': 50, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteomics'},
 {'paragraph_index': 158, 'offset': 58, 'end_offset': 67, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'proteomics'},
 {'paragraph_index': 162, 'offset': 13, 'end_offset': 17, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'Media'},
 {'paragraph_index': 163, 'offset': 34, 'end_offset': 38, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'media'},
 {'paragraph_index': 164, 'offset': 31, 'end_offset': 35, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'media'},
 {'paragraph_index': 166, 'offset': 14, 'end_offset': 18, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'Media'},
 {'paragraph_index': 167, 'offset': 0, 'end_offset': 1, 'term': 'M9', 'uri': 'https://hub.sd2e.org/user/sd2e/design/M9/1', 'link': None, 'text': 'M9'},
 {'paragraph_index': 168, 'offset': 0, 'end_offset': 13, 'term': 'M9 Media Salts', 'uri': 'https://hub.sd2e.org/user/sd2e/design/teknova_M1902/1', 'link': 'https://hub.sd2e.org/user/sd2e/design/teknova_M1902/1', 'text': 'M9 media salts'},
 {'paragraph_index': 185, 'offset': 71, 'end_offset': 75, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'media'},
 {'paragraph_index': 186, 'offset': 37, 'end_offset': 41, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'media'},
 {'paragraph_index': 193, 'offset': 15, 'end_offset': 19, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'Media'},
 {'paragraph_index': 198, 'offset': 57, 'end_offset': 66, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 203, 'offset': 19, 'end_offset': 28, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 203, 'offset': 73, 'end_offset': 82, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 203, 'offset': 89, 'end_offset': 98, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 205, 'offset': 59, 'end_offset': 68, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 212, 'offset': 172, 'end_offset': 176, 'term': 'Media', 'uri': 'https://hub.sd2e.org/user/sd2e/design/Media/1', 'link': None, 'text': 'media'},
 {'paragraph_index': 218, 'offset': 0, 'end_offset': 9, 'term': 'engineered', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/engineered/1', 'link': None, 'text': 'engineered'},
 {'paragraph_index': 229, 'offset': 27, 'end_offset': 36, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 273, 'offset': 17, 'end_offset': 26, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'},
 {'paragraph_index': 280, 'offset': 9, 'end_offset': 18, 'term': 'proteomics', 'uri': 'https://hub.sd2e.org/user/sd2e/intent_parser/proteomics/1', 'link': None, 'text': 'Proteomics'}]

        culled_result = self.ips.cull_overlapping(unculled_input)
        culled_result = sorted(culled_result,key=itemgetter('paragraph_index','offset'))
        self.assertTrue(compare_search_results(culled_result, culled_gt))

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

        # Ignore the next term, proteomics
        result = self.ips.process_never_link([], self.ips.client_state_map[self.doc_id])
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
        self.assertTrue(numResults == self.expected_search_size)

        link_pref_file = os.path.join(self.ips.link_pref_path, 'test@bbn.com.json')
        self.assertTrue(os.path.exists(link_pref_file))

    def test_analyze_link_all(self):
        """
        """
        # Skip first term, engineered
        #result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        #self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'] == 1)
        #self.assertTrue(len(result) == 2)

        result = self.ips.process_link_all({'data' : {'buttonId' : 'test'}}, self.ips.client_state_map[self.doc_id])
        # We should have a link action for each of the 16 instances of proteomics in the results.
        # Plus a highlight text and showSidebar for the last remaining engineered result
        self.assertTrue(len(result) == self.proteomics_search_size + 2)

    def tearDown(self):
        """
        Perform teardown.
        """
        self.ips.stop()


if __name__ == '__main__':
    print('Run unit tests')

    unittest.main(argv=[sys.argv[0]])
