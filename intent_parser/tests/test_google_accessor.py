from intent_parser.accessor.google_accessor import GoogleAccessor
import traceback
import unittest

class GoogleAccessorTest(unittest.TestCase):

    def setUp(self):
        self.spreadsheet_accessor = GoogleAccessor().get_google_spreadsheet_accessor()
        self.doc_accessor = GoogleAccessor().get_google_doc_accessor()
        self.drive_accessor = GoogleAccessor().get_google_drive_accessor()
        self.app_script_acccessor = GoogleAccessor().get_google_app_script_accessor()

    def tearDown(self):
        pass

    def test_spreadsheet_deletion(self):
        spreadsheet_id = self.spreadsheet_accessor.create_new_spreadsheet(name='Spreadsheet To Delete')
        self.assertTrue(spreadsheet_id)
        self.assertTrue(self.drive_accessor.delete_file(spreadsheet_id))
    
    def test_create_spreadsheet_from_given_folder(self):
        folder_id = '1693MJT1Up54_aDUp1s3mPH_DRw1_GS5G'
        spreadsheet_id = self.spreadsheet_accessor.create_new_spreadsheet('Spreadsheet To Delete')
        self.drive_accessor.move_file_to_folder(folder_id, spreadsheet_id)
        self.assertTrue(spreadsheet_id)
        self.assertTrue(self.drive_accessor.delete_file(spreadsheet_id))

    def test_get_doc_from_google_drive(self):
        document_id = '1zf9l0K4rj7I08ZRpxV2ZY54RMMQc15Rlg7ULviJ7SBQ'
        try:
            response = self.doc_accessor.get_document(document_id=document_id)
        except Exception as ex:
            err = ''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__))
            print(err)

    def test_app_script(self):
        pass


if __name__ == "__main__":
    unittest.main()