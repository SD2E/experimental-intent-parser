from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class DriveAPI(object):
    '''
    A list of APIs to access Google Drive
    '''


    def __init__(self, creds):
        self._service = build('drive', 'v3', credentials=creds)
    
    def get_documents_from_drive(self, drive_id):
        results = self._service.files().list(
            q="'%s' in parents and mimeType='application/vnd.google-apps.document'" % (drive_id,),
            spaces='drive',
            pageSize=1000,
            fields='nextPageToken, files(id, name)').execute()
        documents = results.get('files', [])
        return documents
    
    def get_folders_from_drive(self, drive_id):
        results = service.files().list(
            q="'%s' in parents and mimeType='application/vnd.google-apps.folder'" % (drive_id,),
            spaces='drive',
            pageSize=1000,
            fields='nextPageToken, files(id, name)').execute()
        directories = results.get('files', [])
        return directories
    
    def recursive_list_doc(self, drive_id):
        doc_list = self._recursive_doc(drive_id, [])
        return doc_list
        
    def _recursive_doc(self, drive_id, doc_list): 
        folder_list = self.get_folders_from_drive(drive_id)
        if not folder_list:
            doc_ids = self.get_documents_from_drive(drive_id)
            doc_list.extend(doc_ids)  
            return doc_list
        
        doc_ids = self.get_documents_from_drive(drive_id)
        doc_list.extend(doc_ids)  
        
        for dir in folder_list:
            self._recursive_doc(dir['id'], doc_list)