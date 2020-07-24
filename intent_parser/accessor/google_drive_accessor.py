from google.auth.transport.requests import AuthorizedSession, Request
from googleapiclient import errors
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO
import json
import logging

class GoogleDriveV3Accessor(object):

    logger = logging.getLogger('intent_parser_google_drive_accessor')

    def __init__(self, credentials):
        self._service = build('drive', 'v3', credentials=credentials)
        self._authed_session = AuthorizedSession(credentials)

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
                self.logger.warning('Google Drive failed with http code %s for folder %s. Reason: %s' % (
                error_code, folder_id, error_message))
        return doc_list

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

class GoogleDriveV2Accessor(object):
    """
    A list of APIs to access Google Drive. 
    Refer to https://developers.google.com/drive/api/v3/reference/drives to get information on how this class is set up.
    """
    logger = logging.getLogger('intent_parser_google_drive_accessor')

    def __init__(self, credentials):
        self._service = build('drive', 'v2', credentials=credentials)
        self._authed_session = AuthorizedSession(credentials)

    def get_document_metadata(self, document_id):
        return self._service.files().get(fileId=document_id).execute()

    def get_document_parents(self, document_id):
        return self._service.parents().list(fileId=document_id).execute()

    def get_document_revisions(self, document_id):
        """
        Returns the list of revisions for the given document_id
        """
        return self._service.revisions().list(fileId=document_id).execute()

    def get_head_revision(self, document_id):
        revisions = self.get_document_revisions(document_id=document_id)
        revision_ids = [int(revision['id']) for revision in revisions['items']]
        if len(revision_ids) < 1:
            raise ValueError('Revision not found.')

        return str(max(revision_ids))

    def get_file_with_revision(self, file_id, revision_id, mime_type):
        """Download a Google Doc base on a Doc's id and its revision.

        Args:
            fild_id: Google Doc ID
            revision_id: Google Doc revision ID
            mime_type: format to download the Google Doc in.
            Visit https://developers.google.com/drive/api/v3/ref-export-formats to get a list of file formats that Google can export to

        Returns:
            An HTML response of the requested Google Doc revision.
        """
        revisions = self.get_document_revisions(document_id=file_id)
        filter_by_revision = [revision for revision in revisions['items'] if revision['id'] == revision_id]

        if len(filter_by_revision) < 1:
            raise ValueError('Revision not found.')

        url = filter_by_revision[0]['exportLinks'][mime_type]
        response = self._authed_session.request('GET', url)
        return response

    def upload_revision(self, document_name, document, folder_id, original_format, title='Untitled',
                        target_format='*/*'):
        """Upload file to a Google Drive folder.

        Args:
            document_name: Name of the document
            document: content of the document to upload.
            folder_id: id of the Google Drive folder
            original_format: file format of the document content
            title: document title
            target_format: file format that that the uploaded file will transform into.

        Returns:
            A string to represent the uploaded file's id.
        """
        file_metadata = {
            'name': document_name,
            'title': title,
            'parents': [folder_id],
            'mimeType': target_format
        }
        fh = BytesIO(document)
        media = MediaIoBaseUpload(fh, mimetype=original_format, resumable=True)
        file = self._service.files().insert(body=file_metadata,
                                                  media_body=media,
                                                  convert=True,
                                                  fields='id').execute()
        print('File ID: ' + file.get('id'))
        return file.get('id')

    def delete_file(self, file_id: str):
        """Delete an existing file

        Args:
            file_id - the file to delete
        Returns:
            A boolean value. True if the file has been deleted successfully and False, otherwise.
        """
        response = self._service.files().delete(fileId=file_id).execute()
        return not response

    def move_file_to_folder(self, folder_id, file_id):
        return self._service.files().update(fileId=file_id,
                                                     addParents=folder_id,
                                                     removeParents='root').execute()
