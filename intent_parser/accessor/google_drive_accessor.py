from googleapiclient.discovery import build
from googleapiclient import errors
import json
import logging

class GoogleDriveAccessor(object):
    """
    A list of APIs to access Google Drive. 
    Refer to https://developers.google.com/drive/api/v3/reference/drives to get information on how this class is set up.
    """
    logger = logging.getLogger('intent_parser_google_drive_accessor')
    
    def __init__(self, creds):
        self._service = build('drive', 'v3', credentials=creds)

    
    def get_documents_from_folder(self, folder_id):
        """
        Get all Google Docs from a Google Drive folder.
        
        Args:
            folder_id: Google Drive folder id
        
        Returns:
             A list of dictionary with document id and name. 
             Note that Google Drive will return all documents that were deleted from the given folder as well as the existing documents.
        """
        results = self._service.files().list(
            q="'%s' in parents and mimeType='application/vnd.google-apps.document'" % (folder_id),
            spaces='drive',
            pageSize=1000,
            fields='nextPageToken, files(id, name)').execute()
        docs_dict = results.get('files', [])
        return docs_dict
        
    
    def get_subfolders_from_folder(self, folder_id):
        """
        Get subfolders found in a Google Drive folder.
        Args:
            folder_id: a Google Drive folder id
        
        Returns:
            A list of dictionary with folders id and name
        """
        results = self._service.files().list(
            q="'%s' in parents and mimeType='application/vnd.google-apps.folder'" % (folder_id,),
            spaces='drive',
            pageSize=1000,
            fields='nextPageToken, files(id, name)').execute()
        folder_dict = results.get('files', [])
        return folder_dict

    def get_recursive_folders(self, folder_id):
        """
        Get current folder and all subfolder ids found in a Google Drive folder.
        
        Args:
            folder_id: A Google Drive folder id
        Returns a list of Google Drive folder ids
        """
        return self._recursive_folders(folder_id, [])
        
    def _recursive_folders(self, folder_id, folder_list):
        results = self._service.files().list(
            q="'%s' in parents and mimeType='application/vnd.google-apps.folder'" % (folder_id,),
            spaces='drive',
            pageSize=1000,
            fields='nextPageToken, files(id, name)').execute()
        
        folder_dict = results.get('files', [])
        if not folder_dict :
            folder_list.append(folder_id)
            return folder_list
        
        for folder in folder_dict:
            f_id = folder['id']
            res = self._recursive_folders(f_id, folder_list)
            folder_list.extend(res)
        return folder_list
    
    def get_all_docs(self, folder_id):
        """
        Retrieve all Google Docs within a parent Drive folder.
        
        Args:
            folder_id: id of a google drive folder
            
        Returns:
            A list of Google Doc ids
        """
        doc_list = []
        folder_list = [folder_id]
        
        while len(folder_list) > 0:
            folder_id = folder_list.pop()
            try:
                doc_dictionary = self.get_documents_from_folder(folder_id)
                doc_list.extend([doc['id'] for doc in doc_dictionary])
                folder_dictionary = self.get_subfolders_from_folder(folder_id)
                folder_list.extend([folder['id'] for folder in folder_dictionary])
            except errors.HttpError as err:
                error_code = json.loads(err.content)['error']['code']
                error_message = json.loads(err.content)['error']['errors'][0]['message']
                self.logger.warning('Google Drive failed with http code %s for folder %s. Reason: %s' %(error_code, folder_id, error_message))
        return doc_list    
            
    def list_revision(self, file_id):  
        results = self._service.revisions().list(
            fileId=file_id
            ).execute()
            
        return results
    
            