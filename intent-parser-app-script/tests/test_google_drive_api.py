from google_drive_accessor import GoogleDriveAccessor
from google_drive_accessor_v2 import GoogleDriveAccessorV2
import ip_addon_script
import json
import unittest


class DriveAPITest(unittest.TestCase):

    def setUp(self):
        self.creds = ip_addon_script.authenticate_credentials()
        self.drive_api = GoogleDriveAccessor(self.creds)
        self.folder_id = '1693MJT1Up54_aDUp1s3mPH_DRw1_GS5G'

    def tearDown(self):
        pass

    def test_get_documents_from_folder(self):
        response = self.drive_api.get_documents_from_folder(folder_id)
        doc_list = [doc['id'] for doc in response]
        self.assertEquals(40, len(doc_list))
    
    def test_get_subfolders_from_folder(self):
        response = self.drive_api.get_subfolders_from_folder(self.folder_id)
        self.assertEquals(0, len(response))
        
    def test_recursive_list_docs(self):
        response = self.drive_api.recursive_list_doc(self.folder_id)
        self.assertEquals(40, len(response))   
        
    def test_recursive_list_folders(self):
        response = self.drive_api.get_recursive_folders(self.folder_id)
        self.assertEquals(1, len(response))
  
        
if __name__ == "__main__":
    unittest.main()