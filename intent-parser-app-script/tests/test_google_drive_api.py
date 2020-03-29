from google_drive_accessor import GoogleDriveAccessor
from google_drive_accessor_v2 import GoogleDriveAccessorV2
import ip_addon_script
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
        
    def test_print_doc_revisions(self):
        file_id = '1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA'
        list_of_revisions = self.drive_api.list_revision(file_id)
        print(list_of_revisions)
    
    def test_download_doc(self):
        file_id = '1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA'
        response = self.drive_api.download_file(file_id)
        
        with open('temp2.pdf', 'wb') as output:
            output.write(response)
            
    def test_download_file_with_revision(self):
        file_id = '1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA'
        response = self.drive_api.download_file_with_revision('temp_file', file_id, '1976', 'html')
    
    def test_export_doc(self):
        file_id = '1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA'
        response = self.drive_api.export_file(file_id)
       
    def test_drivev2_list_revisions(self):
        file_id = '1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA'
        drive_v2 = GoogleDriveAccessorV2(self.creds)
        result = drive_v2.list_file_revision(file_id)
        export_options = result[0]['exportLinks']
        html_export_url = export_options['text/html']
        
        print(html_export_url)
        
if __name__ == "__main__":
    unittest.main()