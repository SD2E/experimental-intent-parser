from google_accessor import GoogleAccessor
import unittest

class GoogleAccessorTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.google_accessor = GoogleAccessor.create()

    def test_spreadsheet_deletion(self):
        spreadsheet_id = self.google_accessor.create_new_spreadsheet(name='Spreadsheet To Delete')
        self.assertTrue(spreadsheet_id)
        self.assertTrue(self.google_accessor.delete_file(spreadsheet_id))
    
    def test_create_spreadsheet_from_given_folder(self):
        folder_id = '1693MJT1Up54_aDUp1s3mPH_DRw1_GS5G'
        spreadsheet_id = self.google_accessor.create_new_spreadsheet('Spreadsheet To Delete', folder_id)
        self.assertTrue(spreadsheet_id)
        self.assertTrue(self.google_accessor.delete_file(spreadsheet_id))

if __name__ == "__main__":
    unittest.main()