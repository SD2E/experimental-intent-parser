from google_accessor import GoogleAccessor
from unittest.mock import Mock
import getopt
import json
import os
import sys
import time
import unittest
import urllib.request
import warnings

try:
    from intent_parser_server import IntentParserServer
except Exception as e:
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../src'))
    from intent_parser_server import IntentParserServer

class IntegrationIpsTest(unittest.TestCase):

    data_dir = 'data'

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

        # If we don't have the necessary credentials, try reading them in from json
        if not hasattr(IntegrationIpsTest, 'sbh_username') or not hasattr(IntegrationIpsTest, 'sbh_password'):
            with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sbh_creds.json'), 'r') as fin:
                creds = json.load(fin)
                IntegrationIpsTest.sbh_username = creds['username']
                IntegrationIpsTest.sbh_password = creds['password']

        self.google_accessor = GoogleAccessor.create()
        #f = open('test-doc.json', 'r')
        #doc_content = json.loads(f.read())
        #f.close()

        self.bind_ip = 'localhost'
        self.bind_port = 8081
        self.template_doc_id = '10HqgtfVCtYhk3kxIvQcwljIUonSNlSiLBC8UFmlwm1s'
        self.template_spreadsheet_id = '1r3CIyv75vV7A7ghkB0od-TM_16qSYd-byAbQ1DhRgB0'

        self.template_doc_last_rev = '2019-01-30T17:45:49.339Z'
        self.template_sheet_last_rev = '2019-06-12T20:29:13.519Z'

        rev_results = self.google_accessor.get_document_revisions(document_id=self.template_doc_id)
        if not 'drive#revisionList' == rev_results['kind'] or len(rev_results['items']) < 1 :
            print('ERROR: Failed to retrieve revisions for document template!')
            raise Exception
        last_rev = rev_results['items'][0]['modifiedDate']
        if not last_rev == self.template_doc_last_rev:
            print('ERROR: template document has been modified! Expected last revision: %s, received %s!' % (self.template_doc_last_rev, last_rev))
            raise Exception

        rev_results = self.google_accessor.get_document_revisions(document_id=self.template_spreadsheet_id)
        if not 'drive#revisionList' == rev_results['kind'] or len(rev_results['items']) < 1 :
            print('ERROR: Failed to retrieve revisions for spreadsheet template!')
            raise Exception
        last_rev = rev_results['items'][0]['modifiedDate']
        if not last_rev == self.template_sheet_last_rev:
            print('ERROR: template spreadsheet has been modified! Expected last revision: %s, received %s!' % (self.template_sheet_last_rev, last_rev))
            raise Exception

        self.server_url = 'http://' + self.bind_ip + ':' + str(self.bind_port)

        self.doc_id = self.google_accessor.copy_file(file_id=self.template_doc_id,
                                                     new_title='Intent Parser Server Test Doc')

        self.spreadsheet_id = self.google_accessor.copy_file(file_id=self.template_spreadsheet_id,
                                                     new_title='Intent Parser Server Test Sheet')

        self.doc = self.google_accessor.get_document(document_id=self.doc_id)

        sbh_collection_uri = 'https://hub-staging.sd2e.org/user/sd2e/' + \
            'intent_parser/intent_parser_collection/1'

        self.intent_parser = IntentParserServer(sbh_collection_uri=sbh_collection_uri,
                                                sbh_username=IntegrationIpsTest.sbh_username,
                                                sbh_password=IntegrationIpsTest.sbh_password,
                                                spreadsheet_id=self.spreadsheet_id,
                                                item_map_cache=False,
                                                bind_ip='localhost',
                                                bind_port=8081)
        self.intent_parser.initialize_server()
        self.intent_parser.start(background=True) 
        
        self.maxDiff = None

    def test_analyze_doc(self):
        payload = {'documentId':  self.template_doc_id, 'user' : 'test@bbn.com', 'userEmail' : 'test@bbn.com'}
        payload_bytes = json.dumps(payload).encode()

        # Send a request to analyze the document
        response = urllib.request.urlopen(self.server_url + '/analyzeDocument',
                                          data=payload_bytes,
                                          timeout=60)
        result = json.loads(response.read().decode('utf-8'))
        self.assertTrue('actions' in result)
        actions = result['actions']


        # Confirm we got a progress part
        self.assertTrue(len(actions) == 1)
        actions[0]['action'] == 'showProgressbar'

        startTime = time.time()
        while actions[0]['action'] != 'highlightText' and (time.time() - startTime < 100):
            # Send a request to analyze the document
            response = urllib.request.urlopen(self.server_url + '/analyzeDocument', data=payload_bytes, timeout=60)
            result = json.loads(response.read().decode('utf-8'))
            self.assertTrue('actions' in result)
            actions = result['actions']
            self.assertTrue(len(actions) > 0)
            self.assertTrue(actions[0]['action'] == 'highlightText' or actions[0]['action'] == 'updateProgress', 'Action is: %s' % actions[0]['action'])
            print('time: %d' % (time.time() - startTime))
            #time.sleep(0.25)

        # Confirm the server found a term to highlight
        highlight_action = None
        for action in actions:
            if action['action'] == 'highlightText':
                highlight_action = action

        self.assertTrue(highlight_action is not None)

        # Simulate a click of the "no" button
        payload['data'] = {'buttonId': 'process_analyze_no'}
        payload_bytes = json.dumps(payload).encode()

        response = urllib.request.urlopen(self.server_url + '/buttonClick', data=payload_bytes, timeout=60)
        result = json.loads(response.read())
        self.assertTrue('actions' in result)
        actions = result['actions']
        self.assertTrue(len(actions) > 0)

        # Confirm the server found a term to highlight
        # but did not create an html link
        highlight_action = None
        link_action = None
        for action in actions:
            if action['action'] == 'highlightText':
                highlight_action = action
            elif action['action'] == 'linkText':
                link_action = action

        self.assertTrue(highlight_action is not None)
        self.assertTrue(link_action is None)

        # Simulate a click of the "yes" button
        payload['data'] = {'buttonId': 'process_analyze_yes'}
        payload_bytes = json.dumps(payload).encode()

        response = urllib.request.urlopen(self.server_url + '/buttonClick',data=payload_bytes, timeout=60)
        result = json.loads(response.read())
        self.assertTrue('actions' in result)
        actions = result['actions']
        self.assertTrue(len(actions) > 0)

        # Confirm the server found another term to highlight
        # and created an html link
        highlight_action = None
        link_action = None
        for action in actions:
            if action['action'] == 'highlightText':
                highlight_action = action
            elif action['action'] == 'linkText':
                link_action = action

        self.assertTrue(highlight_action is not None)
        self.assertTrue(link_action is not None)

    @classmethod
    def tearDownClass(self):
        print('\nstart teardown')
        if self.intent_parser is not None:
            self.intent_parser.stop()

        if self.doc is not None:
            self.google_accessor.delete_file(file_id=self.doc_id)

        if self.doc is not None:
            self.google_accessor.delete_file(file_id=self.spreadsheet_id)
        time.sleep(60)
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
            IntegrationIpsTest.sbh_username = arg

        elif opt in ('-p', '--password'):
            IntegrationIpsTest.sbh_password = arg

        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)

    if not hasattr(IntentParserServer, 'sbh_username'):
        print('ERROR: Missing required parameter -u/--username!')
        usage()
        sys.exit(0)

    if not hasattr(IntentParserServer, 'sbh_password'):
        print('ERROR: Missing required parameter -p/--password!')
        usage()
        sys.exit(0)

    print('Run unit tests')

    unittest.main(argv=[sys.argv[0]])
