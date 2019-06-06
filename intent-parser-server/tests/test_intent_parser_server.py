import unittest
import warnings
import json
import getopt
import sys
import os
import time
import urllib.request

from intent_parser_server import IntentParserServer
from google_accessor import GoogleAccessor


class TestIntentParserServer(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # The Google API appears to create resource warnings when run
        # from unit test similar to the following:
        #
        # site-packages/googleapiclient/_helpers.py:130:
        #  ResourceWarning: unclosed <ssl.SSLSocket fd=6,
        #                            family=AddressFamily.AF_INET6,
        #                            type=SocketKind.SOCK_STREAM,
        #                            proto=6,
        #                            laddr=('192.168.0.1', 49988, 0, 0),
        #                            raddr=('192.168.0.2', 443, 0, 0)>
        #
        # There is some discussion of similar warnings here:
        #
        #  https://github.com/kennethreitz/requests/issues/3912
        #
        # I am just going ignore these warnings
        #
        warnings.filterwarnings('ignore', message='unclosed <ssl.SSLSocket',
                                category=ResourceWarning)

        self.google_accessor = GoogleAccessor.create()
        f = open('test-doc.json', 'r')
        doc_content = json.loads(f.read())
        f.close()

        self.bind_ip = 'localhost'
        self.bind_port = 8081
        self.template_doc_id = '10HqgtfVCtYhk3kxIvQcwljIUonSNlSiLBC8UFmlwm1s'
        self.template_spreadsheet_id = '1oLJTTydL_5YPyk-wY-dspjIw_bPZ3oCiWiK0xtG8t3g'

        self.server_url = 'http://' + self.bind_ip + ':' + str(self.bind_port)

        self.doc_id = self.google_accessor.copy_file(file_id=self.template_doc_id,
                                                     new_title='Intent Parser Server Test Doc')

        self.spreadsheet_id = self.google_accessor.copy_file(file_id=self.template_spreadsheet_id,
                                                     new_title='Intent Parser Server Test Sheet')

        self.doc = self.google_accessor.get_document(document_id=self.doc_id)

        sbh_collection_uri = 'https://hub-staging.sd2e.org/user/sd2e/' + \
            'intent_parser/intent_parser_collection/1'

        self.intent_parser = IntentParserServer(sbh_collection_uri=sbh_collection_uri,
                                                sbh_username=TestIntentParserServer.sbh_username,
                                                sbh_password=TestIntentParserServer.sbh_password,
                                                spreadsheet_id=self.spreadsheet_id,
                                                bind_ip='localhost',
                                                bind_port=8081)
        self.intent_parser.serverRunLoop(background=True)


    def test_analyze_doc(self):
        payload = {'documentId':  self.template_doc_id}
        payload_bytes = json.dumps(payload).encode()

        # Send a request to analyze the document
        response = urllib.request.urlopen(self.server_url + '/analyzeDocument',
                                          data=payload_bytes,
                                          timeout=60)
        result = json.loads(response.read())
        assert 'actions' in result
        actions = result['actions']
        assert len(actions) > 0

        # Confirm the server found a term to highlight
        highlight_action = None
        for action in actions:
            if action['action'] == 'highlightText':
                highlight_action = action

        assert highlight_action is not None

        # Simulate a click of the "no" button
        payload['data'] = {'buttonId': 'process_analyze_no'}
        payload_bytes = json.dumps(payload).encode()

        response = urllib.request.urlopen(self.server_url + '/buttonClick',
                                          data=payload_bytes,
                                          timeout=60)
        result = json.loads(response.read())
        assert 'actions' in result
        actions = result['actions']
        assert len(actions) > 0

        # Confirm the server found a term to highlight
        # but did not create an html link
        highlight_action = None
        link_action = None
        for action in actions:
            if action['action'] == 'highlightText':
                highlight_action = action
            elif action['action'] == 'linkText':
                link_action = action

        assert highlight_action is not None
        assert link_action is None

        # Simulate a click of the "yes" button
        payload['data'] = {'buttonId': 'process_analyze_yes'}
        payload_bytes = json.dumps(payload).encode()

        response = urllib.request.urlopen(self.server_url + '/buttonClick',
                                          data=payload_bytes,
                                          timeout=60)
        result = json.loads(response.read())
        assert 'actions' in result
        actions = result['actions']
        assert len(actions) > 0

        # Confirm the server found another term to highlight
        # and created an html link
        highlight_action = None
        link_action = None
        for action in actions:
            if action['action'] == 'highlightText':
                highlight_action = action
            elif action['action'] == 'linkText':
                link_action = action

        assert highlight_action is not None
        assert link_action is not None

    @classmethod
    def tearDownClass(self):
        print('\nstart teardown')
        if self.intent_parser is not None:
            self.intent_parser.stop()

        if self.doc is not None:
            self.google_accessor.delete_file(file_id=self.doc_id)

        if self.doc is not None:
            self.google_accessor.delete_file(file_id=self.spreadsheet_id)

        print('done')

def usage():
    print('')
    print('test_intent_parser_server.py: [options]')
    print('')
    print('    -h --help            - show this message')
    print('    -p --pasword         - SynBioHub password')
    print('    -u --username        - SynBioHub username')
    print('')

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "u:p:h",
                                   ["username=",
                                    "password="])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2);

    for opt,arg in opts:
        if opt in ('-u', '--username'):
            TestIntentParserServer.sbh_username = arg

        elif opt in ('-p', '--password'):
            TestIntentParserServer.sbh_password = arg

        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)

    print('Run unit tests')

    unittest.main(argv=[sys.argv[0]])
