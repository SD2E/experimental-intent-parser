from googleapiclient.discovery import build

class GoogleDriveAccessorV2(object):
    """
    A list of APIs to access Google Drive. 
    Refer to https://developers.google.com/drive/api/v3/reference/drives to get information on how this class is set up.
    """

    def __init__(self, creds):
        self._service = build('drive', 'v2', credentials=creds)

            
    def list_file_revision(self, file_id):  
        results = self._service.revisions().list(
            fileId=file_id
            ).execute()
            
        return results['items']
            