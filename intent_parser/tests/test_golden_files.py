from intent_parser.accessor.google_accessor import GoogleAccessor
from intent_parser.intent_parser_factory import IntentParserFactory
from intent_parser.accessor.sbol_dictionary_accessor import SBOLDictionaryAccessor
from datetime import datetime
from unittest.mock import patch
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.utils.intent_parser_utils as intent_parser_utils
import git
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
    def setUpClass(self):
        curr_path = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(curr_path, 'data')
        self.mock_data_dir = os.path.join(self.data_dir, 'mock_data')
        
        cp_request_dir = os.path.join(curr_path, 'data', 'cp-request')
#         git_accessor = git.cmd.Git(cp_request_dir)
#         git_accessor.pull()
        self.structured_request_dir = os.path.join(cp_request_dir, 'input', 'structured_requests')
        
        with open(os.path.join(self.data_dir, 'authn.json'), 'r') as file:
            self.authn = json.load(file)['authn']
             
        self.google_accessor = GoogleAccessor.create()
        self.maxDiff = None  
    
    @patch('intent_parser.intent_parser_sbh.IntentParserSBH')
    def setUp(self, mock_intent_parser_sbh):
        self.mock_intent_parser_sbh = mock_intent_parser_sbh
        
        sbol_dictionary = SBOLDictionaryAccessor(intent_parser_constants.SD2_SPREADSHEET_ID, self.mock_intent_parser_sbh) 
        datacatalog_config = { "mongodb" : { "database" : "catalog_staging", "authn" : self.authn} }
        self.intentparser_factory = IntentParserFactory(datacatalog_config, self.mock_intent_parser_sbh, sbol_dictionary)
        self.uploaded_file_id = ''
        
    def test_intent_parsers_test_document(self):
        file = '1TMNRf0CB_7wCQEq7Rq4_gfpcnRke7B-Px4c3ZFr7a4o_expected.json'
        file_path = os.path.join(self.mock_data_dir, file)
        self._compare_structured_requests(file_path)
    
    def test_nick_NovelChassisYeastStates_TimeSeries_document(self):
        file = '1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA_expected.json'
        file_path = os.path.join(self.mock_data_dir, file)
        self._compare_structured_requests(file_path) 
    
    def test_CEN_PK_Inducible_CRISPR_4_Day_Obstacle_Course(self):  
        file = 'CEN-PK-Inducible-CRISPR-4-Day-Obstacle-Course.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
     
    def test_CP_Experimental_Request_NovelChassis_OR_circuit_GrowthCurve(self):  
        file = 'CP Experimental Request - NovelChassis_OR_circuit_GrowthCurve.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path) 
         
    def test_ER_NovelChassis_mCherryControlStrains_GBW_Cycle0_24hour(self):  
        file = 'ER-NovelChassis-mCherryControlStrains-GBW-Cycle0-24hour.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path) 
         
    def test_ER_NovelChassis_mCherryControlStrains_GBW_Cycle0_8hour(self):  
        file = 'ER-NovelChassis-mCherryControlStrains-GBW-Cycle0-8hour.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path) 
         
    def test_NovelChassis_Ginkgo_Strain_Inducer_Characterization(self):  
        file = 'NovelChassis_Ginkgo_Strain_GrowthCurve.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)   
         
    def test_CP_Plan_Requirements_UCSB_B_subtilis_PositiveFeedbackAmplifier_24hour(self):  
        file = 'Plan-Requirements-UCSB-B-subtilis-PositiveFeedbackAmplifier-24hour.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)  
         
    def test_CP_Plan_Requirements_UCSB_B_subtilis_PositiveFeedbackAmplifier_8hour_resubmission(self):  
        file = 'Plan-Requirements-UCSB-B-subtilis-PositiveFeedbackAmplifier-8hour-resubmission.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
         
    def test_YeastSTATES_CRISPR_Growth_Curves_Request_422936(self):  
        file = 'YeastSTATES CRISPR Growth Curves Request (422936).json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
         
    def test_YeastSTATES_CRISPR_Growth_Curves_with_Plate_Reader_Optimization_Request(self):  
        file = 'YeastSTATES CRISPR Growth Curves with Plate Reader Optimization Request.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
         
    def test_YeastSTATES_Beta_Estradiol_OR_Gate_Plant_TF_Growth_Curves_Request_30C(self):  
        file = 'YeastSTATES-Beta-Estradiol-OR-Gate-Plant-TF-Growth-Curves-30C.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
         
    def test_YeastSTATES_Beta_Estradiol_OR_Gate_Plant_TF_Growth_Curves(self):  
        file = 'YeastSTATES-Beta-Estradiol-OR-Gate-Plant-TF-Growth-Curves.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
         
    def test_YeastSTATES_CRISPR_Growth_Curves_35C(self):  
        file = 'YeastSTATES-CRISPR-Growth-Curves-35C.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
     
    def test_YeastSTATES_CRISPR_Long_Duration_Time_Series_20191208(self):  
        file = 'YeastSTATES-CRISPR-Long-Duration-Time-Series-20191208.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
     
    def test_YeastSTATES_CRISPR_Short_Duration_Time_Series_20191208(self):  
        file = 'YeastSTATES-CRISPR-Short-Duration-Time-Series-20191208.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
     
    def test_YeastSTATES_CRISPR_Short_Duration_Time_Series_35C(self):  
        file = 'YeastSTATES-CRISPR-Short-Duration-Time-Series-35C.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
         
    def test_YeastSTATES_Doxycycline_OR_Gate_Plant_TF_Growth_Curves_30C(self):  
        file = 'YeastSTATES-Doxycycline-OR-Gate-Plant-TF-Growth-Curves-30C.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
         
    def test_YeastSTATES_Doxycycline_OR_Gate_Plant_TF_Growth_Curves(self):  
        file = 'YeastSTATES-Doxycycline-OR-Gate-Plant-TF-Growth-Curves.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
         
    def test_YeastSTATES_OR_Gate_CRISPR_Growth_Curves_30C(self):  
        file = 'YeastSTATES-OR-Gate-CRISPR-Growth-Curves-30C.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
         
    def test_YeastSTATES_OR_Gate_CRISPR_Growth_Curves(self):  
        file = 'YeastSTATES-OR-Gate-CRISPR-Growth-Curves.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
         
    def test_YeastSTATES_OR_Gate_CRISPR_Obstacle_Course(self):  
        file = 'YeastSTATES-OR-Gate-CRISPR-Obstacle-Course.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
         
    def test_YeastSTATES_OR_Gate_Plant_TF_Obstacle_Course(self):  
        file = 'YeastSTATES-OR-Gate-Plant-TF-Obstacle-Course.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
         
    def test_y4d_crispr_growth_curves(self):  
        file = 'y4d_crispr_growth_curves.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
     
    def test_Microbe_LiveDeadClassification(self):  
        file = 'Microbe-LiveDeadClassification.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
     
    def test_NovelChassis_OR_Circuit_Cycle1_ObstacleCourse(self):  
        file = 'NovelChassis-OR-Circuit-Cycle1-ObstacleCourse.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
         
    def test_YeastSTATES_CRISPR_Short_Duration_Time_Series_20191213(self):  
        file = 'YeastSTATES-CRISPR-Short-Duration-Time-Series-20191213.json'
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
            
    def test_YeastSTATES_Beta_Estradiol_OR_Gate_Plant_TF_Dose_Response(self):  
        file = 'YeastSTATES-Beta-Estradiol-OR-Gate-Plant-TF-Dose-Response.json' 
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)

    def test_YeastSTATES_OR_Gate_CRISPR_Dose_Response(self):  
        file = 'YeastSTATES-OR-Gate-CRISPR-Dose-Response.json' 
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)

    def test_YeastSTATES_Doxycycline_OR_Gate_Plant_TF_Dose_Response(self):  
        file = 'YeastSTATES-Doxycycline-OR-Gate-Plant-TF-Dose-Response.json' 
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
    
    def test_YeastSTATES_Beta_Estradiol_OR_Gate_Plant_TF_Dose_Response_30C(self):  
        file = 'YeastSTATES-Beta-Estradiol-OR-Gate-Plant-TF-Dose-Response-30C.json' 
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
        
    def test_YeastSTATES_Doxycycline_OR_Gate_Plant_TF_Dose_Response_30C(self):  
        file = 'YeastSTATES-Doxycycline-OR-Gate-Plant-TF-Dose-Response-30C.json' 
        file_path = os.path.join(self.structured_request_dir, file)
        self._compare_structured_requests(file_path)
    
    def test_YeastSTATES_OR_Gate_CRISPR_Dose_Response_30C(self):  
        file = 'YeastSTATES-OR-Gate-CRISPR-Dose-Response-30C.json' 
        file_path = os.path.join(self.structured_request_dir, file)
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
        self._compare_runs(golden_structured_request['runs'], generated_structured_request['runs'])
        if 'parameters' in golden_structured_request:
            self.assertEqual(golden_structured_request['parameters'], generated_structured_request['parameters'])
    
    def _compare_runs(self, golden, generated):
        # remove fields from golden files that intent parser does not currently support
        for run_index in range(len(golden)):
            run = golden[run_index]
            list_of_measurements = run['measurements']
            for measurement_index in range(len(list_of_measurements)) :
                measurement = list_of_measurements[measurement_index]
                if 'batch' in measurement:
                    del measurement['batch']
                if 'controls' in measurement:
                    del measurement['controls']
        self.assertEqual(golden, generated)
            
    def tearDown(self):
        if self.uploaded_file_id:
            self.google_accessor.delete_file(self.uploaded_file_id)
            print('%s delete doc %s' % (datetime.now().strftime("%d/%m/%Y %H:%M:%S"), self.uploaded_file_id))
           
    @classmethod
    def tearDownClass(self):
        pass 
        
if __name__ == "__main__":
    unittest.main()