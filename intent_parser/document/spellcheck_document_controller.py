from datetime import timedelta
from flashtext import KeywordProcessor
from intent_parser.table.cell_parser import CellParser
from intent_parser.intent_parser_exceptions import IntentParserException
from spellchecker import SpellChecker
import intent_parser.utils.intent_parser_utils as ip_utils
import logging
import os
import threading
import time

class SpellcheckDocumentController(object):

    LOGGER = logging.getLogger('spellcheck_document_controller')
    SYNC_PERIOD = timedelta(minutes=30)
    SPELLCHECK_TERMS_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                         'spellcheck_terms.json')

    def __init__(self):
        self._spellcheck_not_misspelled_terms = {} # map user_id to list of non misspelled terms
        self.spellcheck_documents = {} # map doc_id to a _SpellcheckDocument
        self._started = False
        self._spellcheck_lock = threading.Lock()
        self._spellcheck_thread = threading.Thread(target=self._periodically_write_user_spellcheck_terms)

    def add_to_spellcheck_terms(self, user_id, term):
        self._spellcheck_lock.acquire()
        if user_id not in self._spellcheck_not_misspelled_terms:
            self._spellcheck_not_misspelled_terms[user_id] = [term]
        else:
            user_spellcheck_terms = self._spellcheck_not_misspelled_terms[user_id]
            if term not in user_spellcheck_terms:
                user_spellcheck_terms.append(term)
        self._spellcheck_lock.release()

    def get_first_spellchecker_result(self, document_id):
        if document_id not in self.spellcheck_documents:
            return None

        spellchecker_document = self.spellcheck_documents[document_id]
        results = spellchecker_document.get_result()
        if len(results) == 0:
            self.spellcheck_documents.pop(document_id)
            return None

        return results[0]

    def process_spellchecker(self, document_id, ip_document, user_id, doc_location):
        if not self._started:
            raise IntentParserException(
                'Spellchecker was not initialized to load non misspelled terms from file.')
        spellchecker_document = self._get_or_create_spellchecker(document_id, ip_document, user_id)
        spellchecker_document.spellcheck(doc_location)

    def remove_spellcheck_result(self, document_id, paragraph_index, matching_term, start_offset, end_offset):
        if document_id not in self.spellcheck_documents:
            return

        spellcheck_document = self.spellcheck_documents[document_id]
        spellcheck_document.remove_first_occurrence(paragraph_index, matching_term, start_offset, end_offset)

    def remove_spellcheck_result_with_term(self, document_id, matching_term):
        if document_id not in self.spellcheck_documents:
            return

        spellcheck_document = self.spellcheck_documents[document_id]
        return spellcheck_document.remove_all(matching_term)

    def start_spellcheck_controller(self):
        self.LOGGER.info('Fetching spellcheck terms from file.')

        self._spellcheck_lock.acquire()
        spellcheck_terms = ip_utils.load_json_file(self.SPELLCHECK_TERMS_FILE)
        self._spellcheck_not_misspelled_terms = spellcheck_terms
        self._spellcheck_lock.release()
        self._started = True
        self._spellcheck_thread.start()

    def stop_synchronizing_spellcheck_terms(self):
        self._spellcheck_lock.acquire()
        self._write_spellcheck_terms()
        self._spellcheck_lock.release()

        self._started = False
        self._spellcheck_thread.join()

    def _get_or_create_spellchecker(self, document_id, ip_document, user_id):
        spellcheck_document = None
        self._spellcheck_lock.acquire()
        if document_id in self.spellcheck_documents:
            spellcheck_document = self.spellcheck_documents[document_id]
        else:
            if user_id in self._spellcheck_not_misspelled_terms:
                acceptable_terms = self._spellcheck_not_misspelled_terms[user_id]
                spellcheck_document = _SpellcheckDocument(document_id, ip_document, not_misspelled_terms=acceptable_terms)
            else:
                spellcheck_document = _SpellcheckDocument(document_id, ip_document)

            self.spellcheck_documents[document_id] = spellcheck_document

        self._spellcheck_lock.release()
        return spellcheck_document

    def _periodically_write_user_spellcheck_terms(self):
        while True:
            time.sleep(self.SYNC_PERIOD.total_seconds())
            self._write_spellcheck_terms()

    def _write_spellcheck_terms(self):
        self.LOGGER.info('Writing spellcheck terms to file.')
        ip_utils.write_json_to_file(self._spellcheck_not_misspelled_terms,
                                    self.SPELLCHECK_TERMS_FILE)

class SpellcheckResult(object):
    def __init__(self, paragraph_index, paragraph_text, matching_term, start_offset, end_offset):
        self.paragraph_index = paragraph_index
        self.paragraph_text = paragraph_text
        self.matching_term = matching_term
        self.start_offset = start_offset
        self.end_offset = end_offset

    def get_paragraph_index(self):
        return self.paragraph_index

    def get_paragraph_text(self):
        return self.paragraph_text

    def get_matching_term(self):
        return self.matching_term

    def get_start_offset(self):
        return self.start_offset

    def get_end_offset(self):
        return self.end_offset

class _SpellcheckDocument(object):
    def __init__(self, document_id, ip_document, not_misspelled_terms=[]):
        self.document_id = document_id
        self.ip_document = ip_document
        self.not_misspelled_terms = not_misspelled_terms
        self.result = []

    def get_result(self):
        return self.result

    def remove_all(self, term):
        removed_item = []
        for index in reversed(range(len(self.result))):
            spellcheck_result = self.result[index]
            if spellcheck_result.get_matching_term() == term:
                self.result.pop(index)
                removed_item.append(spellcheck_result)
            elif term in spellcheck_result.get_paragraph_text():
                self.result.pop(index)
                removed_item.append(spellcheck_result)
        return removed_item

    def remove_first_occurrence(self, paragraph_index, matching_term, start_offset, end_offset):
        for index in reversed(range(len(self.result))):
            spellcheck_result = self.result[index]
            if (spellcheck_result.get_paragraph_index() == paragraph_index
                    and spellcheck_result.get_matching_term() == matching_term
                    and spellcheck_result.get_start_offset() == start_offset
                    and spellcheck_result.get_end_offset() == end_offset):
                self.result.pop(index)
                return True
            elif matching_term in spellcheck_result.get_paragraph_text():
                self.result.pop(index)
                return True
        return False

    def spellcheck(self, doc_location):
        spellchecker = SpellChecker()
        spellchecker.word_frequency.load_words(self.not_misspelled_terms)
        for ip_paragraph in self.ip_document.get_paragraphs():
            if ip_paragraph.get_paragraph_index() < doc_location.get_paragraph_index():
                continue
            text = ip_paragraph.get_text().strip()
            if not text:
                continue
            cell_parser = CellParser()
            words = [word for word in text.split() if cell_parser.is_name(word)]
            misspelled_words = list(spellchecker.unknown(words))
            if not misspelled_words:
                continue
            self._processed_misspelled_words(misspelled_words, ip_paragraph, doc_location)

    def _processed_misspelled_words(self, unidentified_words, ip_paragraph, doc_location):
        keyword_processor = KeywordProcessor()
        keyword_processor.add_keywords_from_list(unidentified_words)
        match_results = keyword_processor.extract_keywords(ip_paragraph.get_text().strip(), span_info=True)
        for match, start, end in match_results:
            if doc_location.get_paragraph_index() == ip_paragraph.get_paragraph_index():
                if start < doc_location.get_start_offset():
                    continue
            spellcheck_result = SpellcheckResult(ip_paragraph.get_paragraph_index(),
                                                 ip_paragraph.get_text(),
                                                 match,
                                                 start,
                                                 end-1)

            self.result.append(spellcheck_result)
