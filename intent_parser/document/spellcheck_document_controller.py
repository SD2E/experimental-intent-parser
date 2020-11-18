from datetime import timedelta
from flashtext import KeywordProcessor
from intent_parser.intent_parser_exceptions import IntentParserException
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
        self._spellcheck_terms = {}
        self.spellcheck_documents = {}
        self._started = False
        self._spellcheck_lock = threading.Lock()
        self._spellcheck_thread = threading.Thread(target=self._periodically_write_user_spellcheck_terms)

    def add_to_spellcheck_terms(self, user_id, term):
        self._spellcheck_lock.acquire()
        if user_id not in self._spellcheck_terms:
            self._spellcheck_terms[user_id] = [term]
        else:
            user_spellcheck_terms = self._spellcheck_terms[user_id]
            if term not in user_spellcheck_terms:
                user_spellcheck_terms.append(term)
        self._spellcheck_lock.release()

    def start_spellcheck_controller(self):
        self.LOGGER.info('Fetching spellcheck terms from file.')

        self._spellcheck_lock.acquire()
        spellcheck_terms = ip_utils.load_json_file(self.SPELLCHECK_TERMS_FILE)
        self._spellcheck_terms = spellcheck_terms
        self._spellcheck_lock.release()
        self._started = True
        self._spellcheck_thread.start()

    def stop_synchronizing_ignored_terms(self):
        self._spellcheck_lock.acquire()
        self._write_spellcheck_terms()
        self._spellcheck_lock.release()

        self._started = False
        self._spellcheck_thread.join()

    def _periodically_write_user_spellcheck_terms(self):
        while True:
            time.sleep(self.SYNC_PERIOD.total_seconds())
            self._write_spellcheck_terms()

    def _write_spellcheck_terms(self):
        self.LOGGER.info('Writing spellcheck terms to file.')
        ip_utils.write_json_to_file(self._spellcheck_terms,
                                    self.SPELLCHECK_TERMS_FILE)

