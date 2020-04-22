from datetime import datetime
from google_accessor import GoogleAccessor
from intent_parser import IntentParser
from intent_parser_factory import IntentParserFactory
from os import listdir
from os.path import isfile
from sbol_dictionary_accessor import SBOLDictionaryAccessor
from unittest.mock import Mock, patch
import intent_parser_constants
import git
import intent_parser_utils
import os
import json 
import time
import unittest
import intent_parser
import operator

class GoldenFileTest(unittest.TestCase):
    """
    Test a selection of Google docs by generating a structured request for each document and comparing the result to its expected result. 
    Each document are retrieved from  GoogleAccessor by using these document id and its revision id.
    The selected documents come from SD2 cp-request repository. 
    The document id and the revision id are recorded in cp-request/input/structured_request directory.
    Once the document has been retrieved, it is passed into intent parser to generate a structured request. 
    The structured request is then compared with the structured_request result for equivalency.
    """
    
    @classmethod
    def setUpClass(self):
        curr_path = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(curr_path, 'data')
        self.mock_data_dir = os.path.join(self.data_dir, 'mock_data')
        
        cp_request_dir = os.path.join(curr_path, 'data', 'cp-request')
        git_accessor = git.cmd.Git(cp_request_dir)
        git_accessor.pull()
        self.structured_request_dir = os.path.join(cp_request_dir, 'input', 'structured_requests')
        
        with open(os.path.join(self.data_dir, 'authn.json'), 'r') as file:
            self.authn = json.load(file)['authn']
             
        self.google_accessor = GoogleAccessor.create()
        self.maxDiff = None # Set flag for testing to diff between large strings  
    
    @patch('intent_parser_sbh.IntentParserSBH')
    def setUp(self, mock_intent_parser_sbh):
        self.mock_intent_parser_sbh = mock_intent_parser_sbh
        
        sbol_dictionary = SBOLDictionaryAccessor(intent_parser_constants.SD2_SPREADSHEET_ID, self.mock_intent_parser_sbh) 
        datacatalog_config = { "mongodb" : { "database" : "catalog_staging", "authn" : self.authn} }
        self.intentparser_factory = IntentParserFactory(datacatalog_config, self.mock_intent_parser_sbh, sbol_dictionary)
        self.uploaded_file_id = ''
        
    def test_intent_parsers_test_document(self):
        file = '1TMNRf0CB_7wCQEq7Rq4_gfpcnRke7B-Px4c3ZFr7a4o_expected.json'
        file_path = os.path.join(self.mock_data_dir, file)
        self._test_golden_file(file_path)
    
    def test_nick_NovelChassisYeastStates_TimeSeries_document(self):
        file = '1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA_expected.json'
        file_path = os.path.join(self.mock_data_dir, file)
        self._test_golden_file(file_path)      
            
    def _test_golden_file(self, document):
        golden_structured_request = intent_parser_utils.load_json_file(document)
        golden_doc_url = golden_structured_request['experiment_reference_url']
        doc_id = intent_parser_utils.get_google_doc_id(golden_doc_url) 

        if 'doc_revision_id' not in golden_structured_request:
            self.fail('No document revision specified')

        doc_revision_id = golden_structured_request['doc_revision_id']
        
        upload_mimetype = intent_parser_constants.GOOGLE_DOC_MIMETYPE
        download_mimetype = intent_parser_constants.WORD_DOC_MIMETYPE
        response = self.google_accessor.get_file_with_revision(doc_id, doc_revision_id, download_mimetype)

        drive_folder_test_dir = '1693MJT1Up54_aDUp1s3mPH_DRw1_GS5G'
        self.uploaded_file_id = self.google_accessor.upload_revision(golden_structured_request['name'], response.content, drive_folder_test_dir, download_mimetype, title=golden_structured_request['name'], target_format=upload_mimetype)
        print('%s upload doc %s' % (datetime.now().strftime("%d/%m/%Y %H:%M:%S"), self.uploaded_file_id))
        
        intent_parser = self.intentparser_factory.create_intent_parser(self.uploaded_file_id)
        intent_parser.process()
        generated_structured_request = intent_parser.get_structured_request()
        
        # Skip data that are modified from external resources:
        # experiment_reference, challenge_problem, doc_revision_id, and experiment_id.
        self.assertEqual('https://docs.google.com/document/d/%s' % self.uploaded_file_id, generated_structured_request['experiment_reference_url'])
        self.assertEqual(golden_structured_request['lab'], generated_structured_request['lab'])
        self.assertEqual(golden_structured_request['name'], generated_structured_request['name'])
        self.assertEqual(golden_structured_request['runs'], generated_structured_request['runs'])
        if 'parameters' in golden_structured_request:
            self.assertEqual(golden_structured_request['parameters'], generated_structured_request['parameters'])
    
    def tearDown(self):
        if self.uploaded_file_id:
            self.google_accessor.delete_file(self.uploaded_file_id)
            print('%s delete doc %s' % (datetime.now().strftime("%d/%m/%Y %H:%M:%S"), self.uploaded_file_id))
           
    @classmethod
    def tearDownClass(self):
        pass 
        
if __name__ == "__main__":
    unittest.main()