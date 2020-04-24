from googleapiclient.discovery import build

class DocumentAPI:

    def __init__(self, creds):
        self._service = build('docs', 'v1', credentials=creds)
        
    def get_document(self, doc_id):
        '''
        If request is successful, get document from a given Google Doc id
        '''
        document = self._service.documents().get(documentId=doc_id).execute()
        return document
