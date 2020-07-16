from googleapiclient.discovery import build
import intent_parser.constants.google_doc_api_constants as doc_constants
import logging
import statistics

class GoogleDocAccessor(object):
    """
    A list of APIs to access Google Doc.
    Refer to https://developers.google.com/docs/api/reference/rest to get information on how this class is set up.
    """
    logger = logging.getLogger('intent_parser_google_doc_accessor')

    def __init__(self, credentials):
        self._docs_service = build('docs', 'v1', credentials=credentials, cache_discovery=False)

    def get_document(self, document_id):
        return self._docs_service.documents().get(documentId=document_id).execute()

    def create_table(self, document_id, number_of_row, number_of_col, additional_properties={}):
        table_properties = {doc_constants.NUMBER_OF_ROWS: number_of_row,
                            doc_constants.NUMBER_OF_COLUMNS: number_of_col}
        for key, value in additional_properties.items():
            table_properties[key] = value

        table_request = [{doc_constants.INSERT_TABLE: table_properties}]
        return self.execute_batch_request(table_request,
                                          document_id=document_id)

    def insert_text(self, text, start_pos, end_pos):
        template_cell_text_pos = int(statistics.median([start_pos, end_pos]))
        location_index = self.create_index(template_cell_text_pos)
        text_properties = {doc_constants.TEXT: text,
                           doc_constants.LOCATION: location_index}
        return {doc_constants.INSERT_TEXT: text_properties}

    def create_location(self, index, segment_id=''):
        return {doc_constants.SEGMENT_ID: segment_id,
                doc_constants.INDEX: index}

    def create_end_of_segment_location(self):
        return {doc_constants.END_OF_SEGMENT_LOCATION: {doc_constants.SEGMENT_ID: ''}}

    def create_index(self, index):
        return {doc_constants.INDEX: index}

    def create_range(self, start_index, end_index):
        range_properties = {doc_constants.START_INDEX: start_index,
                            doc_constants.END_INDEX: end_index}
        return {doc_constants.RANGE: range_properties}

    def delete_content(self, start_index, end_index):
        range = self.create_range(start_index, end_index)
        return {doc_constants.DELETE_CONTENT_RANGE: range}

    def delete_table_row(self, row_index, col_index, table_index, document_id):
        table_properties = {doc_constants.TABLE_START_LOCATION: self.create_index(table_index),
                            doc_constants.ROW_INDEX: row_index,
                            doc_constants.COLUMN_INDEX: col_index}
        row_properties = {doc_constants.TABLE_CELL_LOCATION: table_properties}
        return self.execute_batch_request([{doc_constants.DELETE_TABLE_ROW: row_properties}],
                                          document_id)

    def insert_table_row(self, row_index, col_index, table_index, document_id):
        table_properties = {doc_constants.TABLE_START_LOCATION: self.create_index(table_index),
                            doc_constants.ROW_INDEX: row_index,
                            doc_constants.COLUMN_INDEX: col_index}
        row_properties = {doc_constants.TABLE_CELL_LOCATION: table_properties,
                          doc_constants.INSERT_BELOW: True}
        return self.execute_batch_request([{doc_constants.INSERT_TABLE_ROW: row_properties}],
                                          document_id)

    def execute_batch_request(self, requests, document_id):
        return self._docs_service.documents().batchUpdate(documentId=document_id,
                                                          body={'requests': requests}).execute()
