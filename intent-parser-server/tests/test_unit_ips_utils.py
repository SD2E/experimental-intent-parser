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


    def test_find_text(self):
        """
        Basic check, ensure that spellcheck runs and the results are as expected
        """
        # Basic sanity checks
        
        paragraphs = [{'elements': [{'startIndex': 5696, 'endIndex': 5710, 'textRun': {'content': 'M9_glucose_CAA', 'textStyle': {'underline': True, 'foregroundColor': {'color': {'rgbColor': {'red': 0.06666667, 'green': 0.33333334, 'blue': 0.8}}}, 'link': {'url': 'https://hub.sd2e.org/user/sd2e/design/M9_glucose_CAA/1'}}}}, {'startIndex': 5710, 'endIndex': 5712, 'textRun': {'content': ' \n', 'textStyle': {}}}], 'paragraphStyle': {'namedStyleType': 'NORMAL_TEXT', 'lineSpacing': 100, 'direction': 'LEFT_TO_RIGHT', 'spacingMode': 'COLLAPSE_LISTS', 'avoidWidowAndOrphan': False}}]
        abs_start_offset = 5693
        text = 'M9'
        partial_match_min_size = 3
        partial_match_thresh = 0.75
        
        results = intent_parser_utils.find_text(text, abs_start_offset, paragraphs, partial_match_min_size, partial_match_thresh)
        
        self.assertTrue(len(results) == 0)

    def tearDown(self):
        """
        Perform teardown.
        """
        pass
        


if __name__ == '__main__':
    print('Run unit tests')

    unittest.main(argv=[sys.argv[0]])
