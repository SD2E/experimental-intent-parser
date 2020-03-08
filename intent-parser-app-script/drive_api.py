from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class DriveAPI(object):
    '''
    A list of APIs to access Google Drive
    '''


    def __init__(self, creds):
        self._service = build('drive', 'v3', credentials=creds)

    
    def get_documents_from_folder(self, folder_id):
        '''
        Get all documents within a Google Drive folder.
        
        Args:
            folder_id: Google Drive folder id
        
        Returns:
             A list of ids for  all files located within a Google Drive folder
        ''' 
        results = self._service.files().list(
            q="'%s' in parents and mimeType='application/vnd.google-apps.document'" % (folder_id,),
            spaces='drive',
            pageSize=1000,
            fields='nextPageToken, files(id, name)').execute()
        docs_dict = results.get('files', [])
        doc_list = [doc['id'] for doc in docs_dict]
        return docs_dict
    
    def get_subfolders_from_folder(self, folder_id):
        results = self._service.files().list(
            q="'%s' in parents and mimeType='application/vnd.google-apps.folder'" % (folder_id,),
            spaces='drive',
            pageSize=1000,
            fields='nextPageToken, files(id, name)').execute()
        folder_dict = results.get('files', [])
        folder_list = [folder['id'] for folder in folder_dict]
        return folder_dict
    
    def recursive_list_doc(self, folder_id):
        doc_list = self._recursive_doc(folder_id, [])
        print('Found %s Google Docs' % len(doc_list))
        return doc_list 
        
    def _recursive_doc(self, folder_id, doc_list): 
        print('Processing folder: ' + folder_id)
        folder_list = self.get_subfolders_from_folder(folder_id)
        if not folder_list:
            doc_ids = self.get_documents_from_folder(folder_id)
            doc_list.extend(doc_ids)  
            return doc_list
        
        doc_ids = self.get_documents_from_folder(folder_id)
        doc_list.extend(doc_ids)  
        
        for dir in folder_list:
            self._recursive_doc(dir['id'], doc_list)