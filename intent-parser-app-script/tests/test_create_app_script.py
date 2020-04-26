from google_app_script_accessor import GoogleAppScriptAccessor 
import ip_addon_script
import os
import script_util
import unittest

class CreateAppScriptTest(unittest.TestCase):
    '''
    Test procedure for creating a Google app script
    '''

    def setUp(self):
        creds = ip_addon_script.authenticate_credentials()
        self.app_api = GoogleAppScriptAccessor(creds)
        response = self.app_api.create_project('UnitTest_ScriptProj', '1DQedT0t8k4zF26kA1sjcFPDbPXv6nQLlJxgarM-60ew')
        self.script_id = response['scriptId']
        
        self.proj_metadata = self.app_api.get_project_metadata(self.script_id)
        self.new_proj_metadata = self.app_api.set_project_metadata(self.script_id, self.proj_metadata, {
            "domain": 'gmail.com',
            "email": 'bbn.intentparser@gmail.com',
            "name": 'bbn intentparser'})
        self.current_version = self.app_api.get_head_version(self.script_id)
        self.new_version = self.app_api.create_version(self.script_id, self.current_version + 1, 'Test create project')
        
        f1 = self.new_proj_metadata['files'][0]
        f2 = self.new_proj_metadata['files'][1]
        
        if f1['type'] == 'JSON' and f2['type'] == 'SERVER_JS':
            self.new_appscript_data = f1
            self.new_code_data = f2
        elif f1['type'] == 'SERVER_JS' and f2['type'] == 'JSON':
            self.new_appscript_data = f2
            self.new_code_data = f1
             
    def tearDown(self):
        pass

    def test_metadata_size(self):
        self.assertEquals(len(self.proj_metadata), len(self.new_proj_metadata))
        
    def test_proj_id(self):
        self.assertTrue(self.script_id == self.proj_metadata['scriptId'] == self.new_proj_metadata['scriptId'])

    def test_proj_file_size(self):
        self.assertEquals(len(self.new_proj_metadata['files']), 2)
        
    def test_appscript_file(self):
        curr_path = os.path.dirname(os.path.realpath(__file__))
        src_dir = curr_path + '/../src/'
        
        filename = self.new_appscript_data['name']
        self.assertEquals('appsscript', filename)
        exp_data = script_util.load_json_file(src_dir + filename)
        self.assertEquals(self.new_appscript_data['source'], exp_data['source'])
        
    def test_code_file(self): 
        curr_path = os.path.dirname(os.path.realpath(__file__))
        src_dir = curr_path + '/../src/'
       
        filename = self.new_code_data['name']
        self.assertEquals('Code', filename)
        exp_data = script_util.load_js_file(src_dir + filename)
        self.assertEquals(self.new_code_data['source'], exp_data)
        
    def test_version(self):
        self.assertEquals(0, self.current_version)
        self.assertEquals(1, self.new_version['versionNumber'])
        self.assertEquals(self.new_version['versionNumber'], self.app_api.get_head_version(self.script_id))


if __name__ == "__main__":
    unittest.main()