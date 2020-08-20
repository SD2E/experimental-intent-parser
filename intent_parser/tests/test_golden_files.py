from intent_parser.accessor.google_accessor import GoogleAccessor
from intent_parser.intent_parser_factory import IntentParserFactory
from intent_parser.accessor.sbol_dictionary_accessor import SBOLDictionaryAccessor
from datetime import datetime
from unittest.mock import patch
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.utils.intent_parser_utils as intent_parser_utils
import os
import json 
import unittest

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
    def setUpClass(cls):
        pass
    
    @patch('intent_parser.intent_parser_sbh.IntentParserSBH')
    def setUp(self, mock_intent_parser_sbh):
        curr_path = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(curr_path, 'data')
        self.mock_data_dir = os.path.join(self.data_dir, 'mock_data')
        with open(os.path.join(self.data_dir, 'authn.json'), 'r') as file:
            self.authn = json.load(file)['authn']

        self.drive_accessor = GoogleAccessor().get_google_drive_accessor()
        self.maxDiff = None

        self.mock_intent_parser_sbh = mock_intent_parser_sbh
        self.sbol_dictionary = SBOLDictionaryAccessor(intent_parser_constants.SD2_SPREADSHEET_ID, self.mock_intent_parser_sbh)
        self.sbol_dictionary.initial_fetch()
        datacatalog_config = {"mongodb": {"database": "catalog_staging", "authn": self.authn}}
        self.intentparser_factory = IntentParserFactory(datacatalog_config, self.mock_intent_parser_sbh, self.sbol_dictionary)
        self.uploaded_file_id = ''

    def test_YeastSTATES_1_0_Growth_Curves_Request(self):
        file = 'YeastSTATES 1.0 Growth Curves Request.json'
        file_path = os.path.join(self.mock_data_dir, file)
        self._compare_structured_requests(file_path)

    def test_YeastSTATES_1_0_Time_Series_Round_1(self):
        file = 'YeastSTATES 1.0 Time Series Round 1.json'
        file_path = os.path.join(self.mock_data_dir, file)
        self._compare_structured_requests(file_path)

    def _compare_structured_requests(self, document):
        golden_structured_request = intent_parser_utils.load_json_file(document)
        golden_doc_url = golden_structured_request['experiment_reference_url']
        doc_id = intent_parser_utils.get_google_doc_id(golden_doc_url) 

        if 'doc_revision_id' not in golden_structured_request:
            self.fail('No document revision specified')

        doc_revision_id = golden_structured_request['doc_revision_id']
        
        upload_mimetype = intent_parser_constants.GOOGLE_DOC_MIMETYPE
        download_mimetype = intent_parser_constants.WORD_DOC_MIMETYPE

        response = self.drive_accessor.get_file_with_revision(doc_id, doc_revision_id, download_mimetype)

        drive_folder_test_dir = '1693MJT1Up54_aDUp1s3mPH_DRw1_GS5G'
        self.uploaded_file_id = self.drive_accessor.upload_revision(golden_structured_request['name'],
                                                                    response.content, drive_folder_test_dir,
                                                                    download_mimetype,
                                                                    title=golden_structured_request['name'],
                                                                    target_format=upload_mimetype)
        print('%s upload doc %s' % (datetime.now().strftime("%d/%m/%Y %H:%M:%S"), self.uploaded_file_id))
        
        intent_parser = self.intentparser_factory.create_intent_parser(self.uploaded_file_id)
        intent_parser.process_structure_request()
        generated_structured_request = intent_parser.get_structured_request()
        
        # Skip data that are modified from external resources:
        # experiment_reference, challenge_problem, doc_revision_id, and experiment_id.
        self.assertEqual('https://docs.google.com/document/d/%s' % self.uploaded_file_id, generated_structured_request['experiment_reference_url'])
        self.assertEqual(golden_structured_request['lab'], generated_structured_request['lab'])
        self.assertEqual(golden_structured_request['name'], generated_structured_request['name'])
        self._compare_runs(golden_structured_request['runs'], generated_structured_request['runs'])
        if 'parameters' in golden_structured_request:
            self.assertEqual(golden_structured_request['parameters'], generated_structured_request['parameters'])
    
    def _compare_runs(self, golden, generated):
        # remove fields from golden files that intent parser does not currently support
        for run_index in range(len(golden)):
            run = golden[run_index]
            list_of_measurements = run['measurements']
            for measurement_index in range(len(list_of_measurements)):
                measurement = list_of_measurements[measurement_index]

        self.assertEqual(golden, generated)
            
    def tearDown(self):
        if self.uploaded_file_id:
            self.drive_accessor.delete_file(self.uploaded_file_id)
            print('%s delete doc %s' % (datetime.now().strftime("%d/%m/%Y %H:%M:%S"), self.uploaded_file_id))
           
    @classmethod
    def tearDownClass(cls):
        pass

if __name__ == "__main__":
    unittest.main()
