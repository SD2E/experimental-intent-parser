import intent_parser_utils as ip_util
import unittest


class IntentParserUtilTest(unittest.TestCase):


    def test_doc_id_with_google_prefix(self):
        id = ip_util.get_google_doc_id('https://docs.google.com/document/d/1PzDr_u9H9NUUiW_TVoQwLkfaGXkbvkRkEBhlCzZ5hHU')
        self.assertEquals(id, '1PzDr_u9H9NUUiW_TVoQwLkfaGXkbvkRkEBhlCzZ5hHU')
    
    def test_doc_id_with_google_prepostfix(self):
        id = ip_util.get_google_doc_id('https://docs.google.com/document/d/1PzDr_u9H9NUUiW_TVoQwLkfaGXkbvkRkEBhlCzZ5hHU/edit')
        self.assertEquals(id, '1PzDr_u9H9NUUiW_TVoQwLkfaGXkbvkRkEBhlCzZ5hHU')

       
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()