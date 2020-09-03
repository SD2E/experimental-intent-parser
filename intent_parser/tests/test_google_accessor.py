from intent_parser.accessor.google_accessor import GoogleAccessor
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

    def test_comment_box(self):
        text_to_comment_on = 'Expected data and analysis'
        document_id = '1zf9l0K4rj7I08ZRpxV2ZY54RMMQc15Rlg7ULviJ7SBQ'
        self.drive_accessor.insert_comment_box(document_id,
                                               comment_message='api without quoted text')

        self.drive_accessor.insert_comment_box(document_id,
                                               comment_message='api with quoted text',
                                               quoted_text=text_to_comment_on)

    def test_app_script(self):
        pass


if __name__ == "__main__":
    unittest.main()