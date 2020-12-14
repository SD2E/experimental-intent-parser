from http import HTTPStatus
from intent_parser.server.http_message import HttpMessage
from intent_parser.server.intent_parser_processor import IntentParserProcessor
from unittest.mock import Mock, patch
import intent_parser.constants.ip_app_script_constants as addon_constants
import intent_parser.utils.intent_parser_view as intent_parser_view
import json
import unittest


class IntentParserProcessorTest(unittest.TestCase):
    """
    Test IntentParserServer response for different requests made to the server.
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()