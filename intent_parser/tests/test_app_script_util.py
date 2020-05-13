import intent_parser.utils.script_addon_utils as script_util
import os
import unittest

class AppScriptUtilTest(unittest.TestCase):
    """
    Test utility methods for app_script 
    """

    def setUp(self):
        pass 
     
    def tearDown(self):
        pass

    def test_get_function_name_from_js_file(self):
        curr_path = os.path.dirname(os.path.realpath(__file__))
        local_code_path = os.path.join(curr_path, 'data', 'Test.js')
        function_names = script_util.get_function_names_from_js_file(local_code_path)
        self.assertEqual(len(function_names['values']), 36)
        
   

if __name__ == "__main__":
    unittest.main()