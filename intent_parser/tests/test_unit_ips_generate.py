from intent_parser.accessor.google_accessor import GoogleAccessor
from intent_parser.server.intent_parser_server import IntentParserServer
from unittest.mock import Mock
import json
import os
import unittest

@unittest.skip("Skip for refactoring")
class IpsGenerateTest(unittest.TestCase):

    authn_file = 'authn.json'

    spellcheckFile = 'doc_1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA.json'

    tablesFile = 'test_tables.json'

    items_json = 'item-map-sd2dict.json'

    first_table_file = 'uw_biofab_request.json'

    second_table_file = 'ginkgo_request.json'

    dataDir = 'data'

    parent_list = {'kind': 'drive#parentList', 'etag': '"_sqIxUq0fTLFIA17mBQDotbHWsg/XLPCLomfatsiNQOKMCWBdA5SI80"', \
                   'selfLink': 'https://www.googleapis.com/drive/v2/files/1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA/parents?alt=json', \
                   'items': [{'kind': 'drive#parentReference', 'id': '17PNAh4ER_Q9rXBeiXwT2v_WRn3cvnJoR', \
                              'selfLink': 'https://www.googleapis.com/drive/v2/files/1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA/parents/17PNAh4ER_Q9rXBeiXwT2v_WRn3cvnJoR', \
                              'parentLink': 'https://www.googleapis.com/drive/v2/files/17PNAh4ER_Q9rXBeiXwT2v_WRn3cvnJoR', 'isRoot': False}]}

    parent_meta = {'kind': 'drive#file', 'id': '17PNAh4ER_Q9rXBeiXwT2v_WRn3cvnJoR', 'etag': '"_sqIxUq0fTLFIA17mBQDotbHWsg/MTU2NTcyNTU4MDIxMg"', \
                   'selfLink': 'https://www.googleapis.com/drive/v2/files/17PNAh4ER_Q9rXBeiXwT2v_WRn3cvnJoR', \
                   'alternateLink': 'https://drive.google.com/drive/folders/17PNAh4ER_Q9rXBeiXwT2v_WRn3cvnJoR', \
                   'embedLink': 'https://drive.google.com/embeddedfolderview?id=17PNAh4ER_Q9rXBeiXwT2v_WRn3cvnJoR', \
                   'iconLink': 'https://drive-thirdparty.googleusercontent.com/16/type/application/vnd.google-apps.folder', \
                   'title': 'Novel Chassis', 'mimeType': 'application/vnd.google-apps.folder', \
                   'labels': {'starred': False, 'hidden': False, 'trashed': False, 'restricted': False, 'viewed': True}, \
                   'copyRequiresWriterPermission': False, 'createdDate': '2019-08-13T19:46:20.212Z', 'modifiedDate': '2019-08-13T19:46:20.212Z', \
                   'modifiedByMeDate': '2019-08-13T19:46:20.212Z', 'lastViewedByMeDate': '2019-08-13T19:48:03.464Z', \
                   'markedViewedByMeDate': '1970-01-01T00:00:00.000Z', 'version': '4', \
                   'parents': [{'kind': 'drive#parentReference', 'id': '1UAvrsvMnCqabfuUAkUTw7ICW5rHfiMfM', \
                                'selfLink': 'https://www.googleapis.com/drive/v2/files/17PNAh4ER_Q9rXBeiXwT2v_WRn3cvnJoR/parents/1UAvrsvMnCqabfuUAkUTw7ICW5rHfiMfM', \
                                'parentLink': 'https://www.googleapis.com/drive/v2/files/1UAvrsvMnCqabfuUAkUTw7ICW5rHfiMfM', 'isRoot': False}], \
                   'userPermission': {'kind': 'drive#permission', 'etag': '"_sqIxUq0fTLFIA17mBQDotbHWsg/C0CILnP96utUTMOd8wW49Xi8oig"', 'id': 'me', \
                                      'selfLink': 'https://www.googleapis.com/drive/v2/files/17PNAh4ER_Q9rXBeiXwT2v_WRn3cvnJoR/permissions/me', 'role': 'owner', 'type': 'user'}, \
                   'quotaBytesUsed': '0', 'ownerNames': ['Nick Walczak'], \
                   'owners': [{'kind': 'drive#user', 'displayName': 'Nick Walczak', \
                               'picture': {'url': 'https://lh4.googleusercontent.com/-GDclgQlGijc/AAAAAAAAAAI/AAAAAAAABEE/UG6F2Nce1jU/s64/photo.jpg'}, \
                               'isAuthenticatedUser': True, 'permissionId': '04236438886952901009', 'emailAddress': 'walczak.nich@gmail.com'}], \
                   'lastModifyingUserName': 'Nick Walczak', \
                   'lastModifyingUser': {'kind': 'drive#user', 'displayName': 'Nick Walczak', \
                                         'picture': {'url': 'https://lh4.googleusercontent.com/-GDclgQlGijc/AAAAAAAAAAI/AAAAAAAABEE/UG6F2Nce1jU/s64/photo.jpg'}, \
                                         'isAuthenticatedUser': True, 'permissionId': '04236438886952901009', 'emailAddress': 'walczak.nich@gmail.com'}, \
                   'capabilities': {'canCopy': False, 'canEdit': True}, 'editable': True, 'copyable': False, 'writersCanShare': True, 'shared': False, \
                   'explicitlyTrashed': False, 'appDataContents': False, 'spaces': ['drive']}

    def setUp(self):
        """
        Configure an instance of IntentParserServer for generation testing.
        """
        self.doc_content = None
        with open(os.path.join(self.dataDir,self.spellcheckFile), 'r') as fin:
            self.doc_content = json.loads(fin.read())

        if self.doc_content is None:
            self.fail('Failed to read in test document! Path: ' + os.path.join(self.dataDir,self.spellcheckFile))

        # Clear all dictionary information
        if os.path.exists(IntentParserServer.DICT_PATH):
            for file in os.listdir(IntentParserServer.DICT_PATH):
                os.remove(os.path.join(IntentParserServer.DICT_PATH, file))
            os.rmdir(IntentParserServer.DICT_PATH)

        with open(os.path.join(self.dataDir,self.authn_file), 'r') as fin:
            self.authn = json.loads(fin.read())['authn']

        self.doc_id = '1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA'
        self.user = 'bbnTest'
        self.user_email = 'test@bbn.com'
        self.json_body = {'documentId' : self.doc_id, 'user' : self.user, 'userEmail' : self.user_email}

        self.google_accessor = GoogleAccessor.create()
        self.template_spreadsheet_id = '1r3CIyv75vV7A7ghkB0od-TM_16qSYd-byAbQ1DhRgB0'
        self.spreadsheet_id = self.google_accessor.copy_file(file_id = self.template_spreadsheet_id,
                                                     new_title='Intent Parser Server Test Sheet')
        
        self.sbh_collection_uri = 'https://hub-staging.sd2e.org/user/sd2e/src/intent_parser_collection/1'
       
        curr_path = os.path.dirname(os.path.realpath(__file__)) 
        with open(os.path.join(curr_path, 'sbh_creds.json'), 'r') as file:
            creds = json.load(file)
            self.sbh_username = creds['username']
            self.sbh_password = creds['password']
            
        self.ips = IntentParserServer(bind_port=8081, 
                 bind_ip='0.0.0.0',
                 sbh_collection_uri=self.sbh_collection_uri,
                 spreadsheet_id=self.spreadsheet_id,
                 sbh_username=self.sbh_username, 
                 sbh_password=self.sbh_password)
        self.ips.initialize_server()
        self.ips.start(background=True)
        
        self.ips.client_state_lock = Mock()
        self.ips.client_state_map = {}
        self.ips.google_accessor = Mock()
        self.ips.google_accessor.get_document = Mock(return_value=self.doc_content)
        self.ips.send_response = Mock()
        self.ips.get_json_body = Mock(return_value=self.json_body)
        self.ips.analyze_processing_map = {}
        self.ips.analyze_processing_map_lock = Mock()
        self.ips.analyze_processing_lock = Mock()

        # Load example measurement table JSON data.  Contains 9 tables, 2 of which are measurement tables.
        with open(os.path.join(self.dataDir,self.tablesFile), 'r') as fin:
            self.table_data = json.loads(fin.read())

        self.ips.item_map_lock = Mock()
        with open(os.path.join(self.dataDir, self.items_json), 'r') as fin:
            self.ips.item_map = json.load(fin)

        self.httpMessage = Mock()
        self.httpMessage.get_resource = Mock(return_value='/document_report?1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA')

        self.ips.google_accessor.get_document_parents = Mock(return_value = self.parent_list)
        self.ips.google_accessor.get_document_metadata = Mock(return_value = self.parent_meta)
        self.maxDiff = None

    def test_generate_report_basic(self):
        """
        Basic check, ensure that spellcheck runs and the results are as expected
        """
        self.ips.process_generate_structured_request(self.httpMessage, [])
        gen_results = json.loads(self.ips.send_response.call_args[0][1])
        self.assertTrue(gen_results['mapped_names'] is not None)

    def test_generate_request_basic(self):
        """
        Basic check, ensure that spellcheck runs and the results are as expected
        """
        self.ips.process_generate_structured_request(self.httpMessage, [])

        # Basic sanity checks
        gen_results = json.loads(self.ips.send_response.call_args[0][1])

        self.assertTrue(gen_results['name'] == 'Nick Copy of CP Experimental Request - NovelChassisYeastStates_TimeSeries')
        self.assertTrue(gen_results['challenge_problem'] == 'INTENT_PARSER_TEST')
        # check number of required fields that should appear when calling generate request
        self.assertEquals(len(gen_results['runs'][0]['measurements']), 0) 

        # Test for when map_experiment_reference fails
        self.ips.datacatalog_config['mongodb']['authn'] = ''
        self.ips.process_generate_structured_request(self.httpMessage, [])

        # Basic sanity checks
        gen_results = json.loads(self.ips.send_response.call_args[0][1])

        self.assertTrue(gen_results['name'] == 'Nick Copy of CP Experimental Request - NovelChassisYeastStates_TimeSeries')
        self.assertTrue(gen_results['challenge_problem'] == 'NOVEL_CHASSIS')
        self.assertEquals(len(gen_results['runs'][0]['measurements']), 0)

    def test_generate_request_specific(self):
        
        with open(os.path.join(self.dataDir,self.first_table_file), 'r') as fin:
            first_table_gt = json.loads(fin.read())

        with open(os.path.join(self.dataDir,self.second_table_file), 'r') as fin:
            second_table_gt = json.loads(fin.read())

        # First test picks up second table
        self.ips.get_element_type =  Mock(return_value=self.table_data)

        self.ips.process_generate_structured_request(self.httpMessage, [])

        gen_results = json.loads(self.ips.send_response.call_args[0][1])

        self.assertTrue(gen_results['name'] == 'Nick Copy of CP Experimental Request - NovelChassisYeastStates_TimeSeries')
        self.assertTrue(gen_results['challenge_problem'] == 'INTENT_PARSER_TEST')
        self.assertTrue(len(gen_results['runs'][0]['measurements']) == 4)
        
        self.assertEquals(gen_results, first_table_gt)   

        self.ips.process_validate_structured_request(self.httpMessage, [])

        validate_results = json.loads(self.ips.send_response.call_args[0][1])

        self.assertTrue('Validation Passed' in validate_results['actions'][0]['html'])

        # Second test picks up first table
        self.ips.get_element_type =  Mock(return_value=self.table_data[0:len(self.table_data) - 4])

        self.ips.process_generate_structured_request(self.httpMessage, [])

        gen_results = json.loads(self.ips.send_response.call_args[0][1])

        self.assertTrue(gen_results['name'] == 'Nick Copy of CP Experimental Request - NovelChassisYeastStates_TimeSeries')
        self.assertTrue(gen_results['challenge_problem'] == 'INTENT_PARSER_TEST')
        self.assertTrue(len(gen_results['runs'][0]['measurements']) == 4)
        self.assertEquals(gen_results, second_table_gt)   

        self.ips.process_validate_structured_request(self.httpMessage, [])

        validate_results = json.loads(self.ips.send_response.call_args[0][1])

        self.assertTrue('Validation Passed' in validate_results['actions'][0]['html'])
        self.assertTrue('Warning: IPTG does not have a SynbioHub URI specified' in validate_results['actions'][0]['html'])
        self.assertTrue('Warning: Kanamycin Sulfate does not have a SynbioHub URI specified' in validate_results['actions'][0]['html'])

    def tearDown(self):
        """
        Perform teardown.
        """
        self.ips.stop()

if __name__ == "__main__":
    unittest.main()
