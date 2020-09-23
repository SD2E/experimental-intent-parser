from flashtext import KeywordProcessor
import intent_parser.utils.intent_parser_utils as intent_parser_utils
import logging
import os
import threading

class AnalyzeDocument(object):

    logger = logging.getLogger('intent_parser_analyze_document')

    def __init__(self, ignore_terms={}):
        self._document_id = None
        self._keyword_processor = None
        self._current_progress = None
        self._matched_terms = []
        self._ignore_terms = ignore_terms
        self.analyze_processing_map = {} # document id is the key, thread running each document is the value
        self.analyze_processing_map_lock = threading.Lock()  # Used to lock the map
        self.analyze_processing_lock = {}  # Used to indicate if the processing thread has finished, mapped to each doc_id

    def _analyze_text(self, paragraph):
        keywords_found = self._keyword_processor.extract_keywords(paragraph.get_text(), span_info=True)
        for match in keywords_found:
            matched_text = MatchingText(paragraph, match[0], match[1], match[2])
            self._matched_terms.append(matched_text)

    def analyze_document(self, ip_document):
        paragraphs = ip_document.get_paragraphs()
        num_of_paragraphs = len(paragraphs)
        for index in range(len(paragraphs)):
            self._analyze_text(paragraphs[index])
            self._current_progress = float(((index+1) * 100)/num_of_paragraphs)

    def get_matched_terms(self, common_name):
        removed_terms = []
        for keyword_index in reversed(range(0, len(self._matched_terms))):
            matching_keyword = self._matched_terms[keyword_index]
            if matching_keyword.get_matched_term() == common_name:
                removed_term = self._matched_terms.pop(keyword_index)
                removed_terms.append(removed_term)
        return reversed(removed_terms)

    def get_analyze_result(self):
        if len(self._matched_terms) > 0:
            return self._matched_terms.pop(0)
        return None

    def get_current_progress(self):
        return self._current_progress

    def is_analyzing_document(self, document_id):
        return self._document_id == document_id

    def intialize_analysis(self, document_id, experiment_variables):
        self.analyze_processing_map[document_id] = 0
        self._document_id = document_id
        self._current_progress = 0
        self._keyword_processor = KeywordProcessor()
        for exper_var in experiment_variables.values():
            self._keyword_processor.add_keyword(exper_var.get_common_name())

    def load_never_link_terms(self):
        curr_path = os.path.dirname(os.path.realpath(__file__))
        ignore_terms = intent_parser_utils.load_json_file(os.path.join(curr_path, 'ignore_analyzed_terms.json'))

class MatchingText(object):

    def __init__(self, paragraph, text, start_position, end_position):
        self._paragraph = paragraph
        self._text = text
        self._start_position = start_position
        self._end_position = end_position

    def get_start_position(self):
        return self._start_position

    def get_end_position(self):
        return self._end_position-1

    def get_matched_term(self):
        return self._text

    def get_paragraph(self):
        return self._paragraph