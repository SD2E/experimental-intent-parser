from datetime import timedelta
from flashtext import KeywordProcessor
from intent_parser.intent_parser_exceptions import IntentParserException
import intent_parser.utils.intent_parser_utils as ip_utils
import logging
import os
import threading
import time

class AnalyzeDocumentController(object):

    LOGGER = logging.getLogger('analyze_document_controller')
    SYNC_PERIOD = timedelta(minutes=30)
    ANALYZE_IGNORE_TERMS_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                             'analyze_ignore_terms.json')

    def __init__(self):
        self._ignore_terms = {}
        self.analyzed_documents = {}
        self._started = False
        self._analyze_processing_lock = threading.Lock()
        self._analyze_thread = threading.Thread(target=self._periodically_write_user_ingored_terms)

    def start_analyze_controller(self):
        self.LOGGER.info('Fetching ignored terms from file.')

        self._analyze_processing_lock.acquire()
        ignore_terms = ip_utils.load_json_file(self.ANALYZE_IGNORE_TERMS_FILE)
        self._ignore_terms = ignore_terms
        self._analyze_processing_lock.release()
        self._started = True
        self._analyze_thread.start()

    def stop_synchronizing_ignored_terms(self):
        self._analyze_processing_lock.acquire()
        self._write_ignored_terms()
        self._analyze_processing_lock.release()

        self._started = False
        self._analyze_thread.join()

    def _periodically_write_user_ingored_terms(self):
        while True:
            time.sleep(self.SYNC_PERIOD.total_seconds())
            self._write_ignored_terms()

    def _write_ignored_terms(self):
        self.LOGGER.info('Writing ignored terms to file.')
        ip_utils.write_json_to_file(self._ignore_terms, self.ANALYZE_IGNORE_TERMS_FILE)

    def get_all_analyzed_results(self, document_id):
        if document_id not in self.analyzed_documents:
            return None

        analyze_document = self.analyzed_documents[document_id]
        return analyze_document.get_result()

    def get_first_analyze_result(self, document_id):
        if document_id not in self.analyzed_documents:
            return None

        analyze_document = self.analyzed_documents[document_id]
        results = analyze_document.get_result()
        if len(results) == 0:
            self.analyzed_documents.pop(document_id)
            return None

        return results[0]

    def add_to_ignore_terms(self, user_id, term):
        self._analyze_processing_lock.acquire()
        if user_id not in self._ignore_terms:
            self._ignore_terms[user_id] = [term]
        else:
            user_ignored_terms = self._ignore_terms[user_id]
            if term not in user_ignored_terms:
                user_ignored_terms.append(term)
        self._analyze_processing_lock.release()

    def remove_analyze_result_with_term(self, document_id, matching_term):
        if document_id not in self.analyzed_documents:
            return
        analyze_document = self.analyzed_documents[document_id]
        return analyze_document.remove_all(matching_term)

    def remove_document(self, document_id):
        if document_id not in self.analyzed_documents:
            return
        self.analyzed_documents.pop(document_id)

    def remove_analyze_result(self, document_id, paragraph_index, matching_term, sbh_uri, start_offset, end_offset):
        if document_id not in self.analyzed_documents:
            return
        analyze_document = self.analyzed_documents[document_id]
        analyze_document.remove_first_occurrence(paragraph_index, matching_term, sbh_uri, start_offset, end_offset)

    def process_dictionary_terms(self, document_id, ip_document, user_id, doc_location, dictionary_terms={}):
        if not self._started:
            raise IntentParserException('AnalyzeDocumentController was not initialized to load ignored terms from file.')

        filtered_dictionary = self._filter_dictionary_terms(user_id, dictionary_terms)
        analyze_document = self._get_or_create_analyze_document(document_id, ip_document, filtered_dictionary)
        analyze_document.analyze(doc_location)

    def _get_or_create_analyze_document(self, document_id, ip_document, dictionary_terms={}):
        analyze_document = None
        self._analyze_processing_lock.acquire()
        if document_id in self.analyzed_documents:
            analyze_document = self.analyzed_documents[document_id]
        else:
            analyze_document = _AnalyzeDocument(document_id, ip_document, dictionary_terms)
            self.analyzed_documents[document_id] = analyze_document
        self._analyze_processing_lock.release()
        return analyze_document

    def _filter_dictionary_terms(self, user_id, dictionary_terms):
        self._analyze_processing_lock.acquire()
        copied_dictionary = dictionary_terms.copy()
        if user_id in self._ignore_terms:
            for term in self._ignore_terms[user_id]:
                if term in copied_dictionary:
                    copied_dictionary.pop(term)

        self._analyze_processing_lock.release()
        return copied_dictionary

class AnalyzeResult(object):
    def __init__(self, paragraph_index, matching_term, sbh_uri, start_offset, end_offset):
        self.paragraph_index = paragraph_index
        self.matching_term = matching_term
        self.sbh_uri = sbh_uri
        self.start_offset = start_offset
        self.end_offset = end_offset

    def get_paragraph_index(self):
        return self.paragraph_index

    def get_matching_term(self):
        return self.matching_term

    def get_sbh_uri(self):
        return self.sbh_uri

    def get_start_offset(self):
        return self.start_offset

    def get_end_offset(self):
        return self.end_offset

class _AnalyzeDocument(object):

    def __init__(self, document_id, ip_document, dictionary_terms):
        self.document_id = document_id
        self.ip_document = ip_document
        self.dictionary_terms = dictionary_terms
        self.keyword_processor = KeywordProcessor()
        self.keyword_processor.add_keywords_from_list(list(dictionary_terms.keys()))
        self.result = []

    def analyze(self, doc_location):
        for ip_paragraph in self.ip_document.get_paragraphs():
            if ip_paragraph.get_paragraph_index() < doc_location.get_paragraph_index():
                continue

            text = ip_paragraph.get_text()
            match_results = self.keyword_processor.extract_keywords(text, span_info=True)
            if not match_results:
                continue

            for match, start, end in match_results:
                if doc_location.get_paragraph_index() == ip_paragraph.get_paragraph_index():
                    if start < doc_location.get_start_offset():
                        continue
                sbh_uri = self.dictionary_terms[match]
                analyze_result = AnalyzeResult(ip_paragraph.get_paragraph_index(),
                                               match,
                                               sbh_uri,
                                               start,
                                               end-1)
                self.result.append(analyze_result)

    def remove_first_occurrence(self, paragraph_index, matching_term, sbh_uri, start_offset, end_offset):
        for index in reversed(range(len(self.result))):
            analyze_result = self.result[index]
            # if users want to manually enter in a sbh_uri then allow users  to remove current result
            # as long as the term and position where the term occurs in the document matches.
            if (analyze_result.get_paragraph_index() == paragraph_index
                    and analyze_result.get_matching_term() == matching_term
                    and analyze_result.get_start_offset() == start_offset
                    and analyze_result.get_end_offset() == end_offset):
                self.result.pop(index)
                return True
        return False

    def remove_all(self, term):
        removed_item = []
        for index in reversed(range(len(self.result))):
            analyze_result = self.result[index]
            if analyze_result.get_matching_term() == term:
                self.result.pop(index)
                removed_item.append(analyze_result)
        return removed_item

    def get_result(self):
        return self.result

