from google_app_script_accessor import GoogleAppScriptAccessor 
import ip_addon_script
import os
import script_util
import unittest

class AppScriptUtilTest(unittest.TestCase):
    """
    Test utility methods for app_script 
    """

    def setUp(self):
        curr_path = os.path.dirname(os.path.realpath(__file__))
        self.src_dir = os.path.join(curr_path, '../src')
                     
    def tearDown(self):
        pass

    def test_get_function_name_from_js_file(self):
        file_name = os.path.join(self.src_dir, 'Code')
        function_names = script_util.get_function_names_from_js_file(file_name)
        self.assertEquals(len(function_names['values']), 36)
        
   

if __name__ == "__main__":
    unittest.main()