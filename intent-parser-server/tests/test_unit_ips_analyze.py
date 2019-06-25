import unittest
import warnings
import json
import getopt
import sys
import os
import time
import urllib.request
import pickle

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
    
    expected_search_size = 22

    proteomics_search_size = 19
    
    items_json = 'item-map.json'

    dataDir = 'data'

    def get_currently_selected_text(self):
        """
        Given select start and end dicts from spelling results, retrieve the text from the test document.
        """
        spelling_index = self.ips.client_state_map[self.doc_id]['spelling_index']
        spelling_result = self.ips.client_state_map[self.doc_id]['spelling_results'][spelling_index]
        select_start = spelling_result['select_start']
        select_end = spelling_result['select_end']

        if not select_start['paragraph_index'] == select_end['paragraph_index']:
            self.fail('Selection starting and ending paragraphs differ! Not supported!')

        paragraphs = self.ips.get_paragraphs(self.doc_content)
        paragraph = paragraphs[select_start['paragraph_index']]
        para_text = self.ips.get_paragraph_text(paragraph)
        return para_text[select_start['cursor_index']:(select_end['cursor_index'] + 1)]

    def compare_search_results(self, r1, r2):
        """
        Compares two spellcheck search results to see if they are equal.
        r1 and r2 are lists of search results, where each result contains a term, selection start, and selection end.
        """
        if not len(r1) == len(r2):
            return False

        for idx in range(len(r1)):
            entry1 = r1[idx]
            entry2 = r2[idx]
            if not entry1['term'] == entry2['term']:
                return False
            if not entry1['paragraph_index'] == entry2['paragraph_index']:
                return False
            if not entry1['offset'] == entry2['offset']:
                return False
            if not entry1['end_offset'] == entry2['end_offset']:
                return False
            if not entry1['uri'] == entry2['uri']:
                return False
            if not entry1['link'] == entry2['link']:
                return False
            if not entry1['text'] == entry2['text']:
                return False
        return True

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
        with open(os.path.join(self.dataDir, self.items_json), 'rb') as fin:
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
            
        self.compare_search_results(self.search_gt, self.ips.client_state_map[self.doc_id]['search_results'])

    def test_analyze_basic(self):
        """
        Basic check, ensure that spellcheck runs and the results are as expected
        """
        # Basic sanity checks
        self.assertTrue(self.ips.client_state_map[self.doc_id]['document_id'] == self.doc_id)
        self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'] is 1)
        self.assertTrue(len(self.ips.client_state_map[self.doc_id]['search_results']) is self.expected_search_size)
        
        self.assertTrue(self.compare_search_results(self.search_gt, self.ips.client_state_map[self.doc_id]['search_results']), 'Search result sets do not match!')

    def test_analyze_yes(self):
        """
        """
        numResults = len(self.ips.client_state_map[self.doc_id]['search_results'])
        for idx in range(1, numResults - 1):
            result = self.ips.process_analyze_yes([], self.ips.client_state_map[self.doc_id])
            self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'], idx)
            self.assertTrue(len(result) == 3)

        result = self.ips.process_analyze_yes([], self.ips.client_state_map[self.doc_id])
        self.assertTrue(len(result) == 1)
        
    def test_analyze_no(self):
        """
        """
        numResults = len(self.ips.client_state_map[self.doc_id]['search_results'])
        for idx in range(1, numResults - 1):
            result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
            self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'], idx)
            self.assertTrue(len(result) == 2 )

        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        self.assertTrue(len(result) == 0 )

    def test_analyze_no_to_all(self):
        """
        """
        # Skip first term, engineered
        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'], 1)
        self.assertTrue(len(result) == 2 )

        # Ignore the next term, proteomics
        result = self.ips.process_no_to_all([], self.ips.client_state_map[self.doc_id])
        # We should have one result left after ignoring the 16 instances of proteomics in the results.
        self.assertTrue(len(result) == 2)
        # We should have no results left after ignoring the last item
        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        self.assertTrue(len(result) == 0 )

    def test_analyze_link_all(self):
        """
        """
        # Skip first term, engineered
        result = self.ips.process_analyze_no([], self.ips.client_state_map[self.doc_id])
        self.assertTrue(self.ips.client_state_map[self.doc_id]['search_result_index'], 1)
        self.assertTrue(len(result) == 2 )

        result = self.ips.process_link_all([], self.ips.client_state_map[self.doc_id])
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
