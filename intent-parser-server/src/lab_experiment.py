from google_accessor import GoogleAccessor
from http import HTTPStatus
from intent_parser_exceptions import ConnectionException
import intent_parser_utils

class LabExperiment(object):
    '''
    Processes information for a lab experiment from a:
        - Google Doc 
        - Microsoft Word Document 
    '''

    def __init__(self, document_id):
        self._document_id = document_id
    
    def load_from_google_doc(self):
        try:
            google_accessor = GoogleAccessor.create()
            document = google_accessor.get_document(document_id=self._document_id)
            self._head_revision = google_accessor.get_head_revision(self._document_id)
            self._links_info = self._get_links_from_doc(document)
            self._paragraphs = self._get_paragraph_from_doc(document)
            self._parents = google_accessor.get_document_parents(document_id=self._document_id)
            self._tables = intent_parser_utils.get_element_type(document, 'table')
            self._title = intent_parser_utils.get_element_type(document, 'title')
            return document
        except Exception:
            raise ConnectionException(HTTPStatus.NOT_FOUND,'Failed to access document ' + self._document_id)

    def load_metadata_from_google_doc(self):
        try:
            google_accessor = GoogleAccessor.create()
            self._metadata = google_accessor.get_document_metadata(document_id=self._document_id) 
            return self._metadata
        except Exception:
            raise ConnectionException(HTTPStatus.NOT_FOUND,'Failed to access document ' + self._document_id)
        
    def title(self):
        return self._title
    
    def tables(self):
        return self._tables
    
    def links_info(self):
        return self._links_info
    
    def paragraphs(self):
        return self._paragraphs
    
    def metadata(self):
        return self._metadata
    
    def parents(self):
        return self._parents
    
    def document_id(self):
        return self._document_id
    
    def head_revision(self):
        return self._head_revision
    
    def _get_paragraph_from_doc(self, doc):
        body = doc.get('body');
        doc_content = body.get('content')
        return intent_parser_utils.get_element_type(doc_content, 'paragraph')
    
    def _get_links_from_doc(self, doc):
        text_runs = intent_parser_utils.get_element_type(doc, 'textRun')
        text_styles = list(filter(lambda x: 'textStyle' in x,
                                text_runs))
        links = list(filter(lambda x: 'link' in x['textStyle'],
                                text_styles))
        return list(map(lambda x: (x['content'],
                                         x['textStyle']['link']),
                              links))