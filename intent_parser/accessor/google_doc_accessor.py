from googleapiclient.discovery import build
import logging

class GoogleDocAccessor(object):
    """
    A list of APIs to access Google Doc.
    Refer to https://developers.google.com/docs/api/reference/rest to get information on how this class is set up.
    """
    logger = logging.getLogger('intent_parser_google_doc_accessor')

    def __init__(self, credentials):
        self._docs_service = build('docs', 'v1', credentials=credentials)

    def get_document(self, document_id):
        return self._docs_service.documents().get(documentId=document_id).execute()
