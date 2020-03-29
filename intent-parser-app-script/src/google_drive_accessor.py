from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io 
import requests
from flask.globals import request

class GoogleDriveAccessor(object):
    """
    A list of APIs to access Google Drive. 
    Refer to https://developers.google.com/drive/api/v3/reference/drives to get information on how this class is set up.
    """

    def __init__(self, creds):
        self._service = build('drive', 'v3', credentials=creds)

    
    def get_documents_from_folder(self, folder_id):
        """
        Get all Google Docs from a Google Drive folder.
        
        Args:
            folder_id: Google Drive folder id
        
        Returns:
             A list of Google Doc ids. 
             Note that Google Drive will return all documents that were deleted from the given folder as well as the existing documents.
        """
        results = self._service.files().list(
            q="'%s' in parents and mimeType='application/vnd.google-apps.document'" % (folder_id,),
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
            A dictionary with a list of folder's id and name
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
           
    def recursive_list_doc(self, folder_id):
        """
        Get all Google Docs from a Google Drive folder
        
        Returns:
            a list of Google Doc ids
        """
        doc_list = self._recursive_doc(folder_id, [])
        return doc_list 
        
    def _recursive_doc(self, folder_id, doc_list): 
        folder_list = self.get_subfolders_from_folder(folder_id)
        if not folder_list:
            doc_ids = self.get_documents_from_folder(folder_id)
            doc_list.extend(doc_ids)  
            return doc_list
        
        doc_ids = self.get_documents_from_folder(folder_id)
        doc_list.extend(doc_ids)  
        
        for folder in folder_list:
            doc_list = self._recursive_doc(folder['id'], doc_list)
        return doc_list
            
    def list_revision(self, file_id):  
        results = self._service.revisions().list(
            fileId=file_id
            ).execute()
            
        return results
    
    def download_file(self, file_id, file_name='temp'):
        request = self._service.files().export_media(fileId=file_id,
                                             mimeType='application/pdf')
#         fh = io.FileIO(file_name, 'wb')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))
            
        return fh.getvalue()
    
    def download_file_with_revision(self, file_name, file_id, revision_id, format_type):
        """
        Download a Google Doc base on a Doc's id and its revision.
        
        Args:
            fild_id: id of the Google Doc
            revision_id: revision id of the Google Doc
            format_type: format to download the Google Doc in. 
            Visit https://developers.google.com/drive/api/v3/ref-export-formats to get a list file formats that Google can export to
            
        
        """
        url = 'https://docs.google.com/feeds/download/documents/export/Export?id=%s&revision=%s&exportFormat=%s' % (file_id, revision_id, format_type)
        response = requests.get(url)
        open(file_name + format_type, 'wb').write(response.content)
            
        print(url)
    
    def export_file(self, file_id):
        request = self._service.files().export(fileId=file_id,
            mimeType='    text/html')
        
        return request
            