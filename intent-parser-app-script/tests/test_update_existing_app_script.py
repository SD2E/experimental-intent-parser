from app_script_api import AppScriptAPI
import ip_addon_script
import os
import script_util
import unittest

class UpdateExistingAppScriptTest(unittest.TestCase):
    '''
    Test procedure for updating an existing Google app script
    '''

    def setUp(self):
        creds = ip_addon_script.authenticate_credentials()
        self.app_api = AppScriptAPI(creds)
        self.script_id = '1ljLzJHRqJ2FjsMUt1O3bQyfRWNecVqkEhVGry5OeC2mUOe00wlpPYV3p'
        self.current_version = self.app_api.get_head_version(self.script_id)
        self.current_proj_metadata = self.app_api.get_project_metadata(self.script_id, self.current_version)
        self.updated_proj_metadata = self.app_api.update_project_metadata(self.script_id, self.current_proj_metadata)
        self.updated_version = self.app_api.create_version(self.script_id, self.current_version + 1, 'test updated project')
        
        f1 = self.updated_proj_metadata['files'][0]
        f2 = self.updated_proj_metadata['files'][1]
        
        if f1['type'] == 'JSON' and f2['type'] == 'SERVER_JS':
            self.appscript_data = f1
            self.code_data = f2
        elif f1['type'] == 'SERVER_JS' and f2['type'] == 'JSON':
            self.appscript_data = f2
            self.code_data = f1
          
    def tearDown(self):
        pass
    
    def test_proj_metadata_size(self):
        self.assertEquals(2, len(self.current_proj_metadata))
        self.assertEquals(2, len(self.updated_proj_metadata))
        
    def test_proj_id(self):
        self.assertEquals(self.script_id, self.current_proj_metadata['scriptId'])
        self.assertEquals(self.script_id, self.updated_proj_metadata['scriptId'])
        
    def test_proj_file_size(self):
        self.assertEquals(2, len(self.current_proj_metadata['files']))
        self.assertEquals(2, len(self.updated_proj_metadata['files']))
        
    def test_appsscript_file(self): 
        curr_path = os.path.dirname(os.path.realpath(__file__))
        src_dir = curr_path + '/../src/'
        
        filename = self.appscript_data['name']
        self.assertEquals('appsscript', filename)
        exp_data = script_util.load_json_file(src_dir + filename)
        self.assertEquals(self.appscript_data['source'], exp_data['source'])
            
    def test_code_file(self): 
        curr_path = os.path.dirname(os.path.realpath(__file__))
        src_dir = curr_path + '/../src/'
       
        filename = self.code_data['name']
        self.assertEquals('Code', filename)
        exp_data = script_util.load_js_file(src_dir + filename)
        self.assertEquals(self.code_data['source'], exp_data) 
           
    def test_updated_version(self):
        head_version = self.app_api.get_head_version(self.script_id)
        updated_version = self.updated_version['versionNumber']
        self.assertEquals(head_version, updated_version) 
        
  
        
if __name__ == "__main__":
    unittest.main()