from sbol2 import SBOLError
from intent_parser.intent_parser_exceptions import IntentParserException
import logging
import sbol2 as sbol
import tenacity
import threading
import traceback

class SBHAccessor:
    _LOGGER = logging.getLogger('sbh_accessor')

    def __init__(self, sbh_url):
        self.shutdownThread = False
        self.event = threading.Event()
        self.lock = threading.Lock()
        self.sbh = sbol.PartShop(sbh_url)
        self.sbh_username = None
        self.sbh_password = None

        self.housekeeping_thread = threading.Thread(target=self.housekeeping)
        self.housekeeping_thread.start()

    # * Stop after trying 3 times
    # * Wait 3 seconds between retries
    # * Reraise the exception that caused the failure, rather than
    #   raising a tenacity.RetryError
    @tenacity.retry(stop=tenacity.stop_after_attempt(3),
                    wait=tenacity.wait_fixed(3),
                    reraise=True)
    def login(self, sbh_username, sbh_password):
        self.lock.acquire()
        try:
            fret = self.sbh.login(sbh_username, sbh_password)
            self.sbh_username = sbh_username
            self.sbh_password = sbh_password
            return fret
        except SBOLError as e:
            message = 'Failed logging into SynBioHub.'
            self._LOGGER.error(message)
            raise IntentParserException(message)
        finally:
            self.lock.release()

    def set_spoof_uri(self, spoof_uri):
        # Spoof URI can only be set when running on test server, not production server
        self.lock.acquire()
        try:
            self.sbh.spoof(spoof_uri)
        except SBOLError as e:
            message = 'Failed set spoof URI.'
            self._LOGGER.error(message)
            raise IntentParserException(message)
        finally:
            self.lock.release()

    # * Stop after trying 3 times
    # * Wait 3 seconds between retries
    # * Reraise the exception that caused the failure, rather than
    #   raising a tenacity.RetryError
    @tenacity.retry(stop=tenacity.stop_after_attempt(3),
                    wait=tenacity.wait_fixed(3),
                    reraise=True)
    def sparqlQuery(self, sparql_query):
        self.lock.acquire()
        try:
            fret = self.sbh.sparqlQuery(sparql_query)
            return fret
        except SBOLError as e:
            message = 'Failed to perform sparql query.'
            self._LOGGER.error(message)
            raise IntentParserException(message)
        finally:
            self.lock.release()

    def exists(self, document, targeted_uri, run_recursive=True):
        self.lock.acquire()
        try:
            # a github issue has been requested to support sbh.exists()
            # for now, sbh.pull is a temporary solution used to check the existence of a collection in sbh.
            self.sbh.pull(targeted_uri, document, run_recursive)
            return True
        except SBOLError:
            self._LOGGER.warning('URI %s does not exist in SynBioHub' % targeted_uri)
            return False
        finally:
            self.lock.release()

    def submit(self, document, collection, flags):
        self.lock.acquire()
        try:
            fret = self.sbh.submit(document,
                                   collection,
                                   flags)
            return fret
        except SBOLError as e:
            self._LOGGER.error(''.join(traceback.format_exception(etype=type(e),
                                                                  value=e,
                                                                  tb=e.__traceback__)))
            raise IntentParserException('Failed to submit to SynBioHub')
        finally:
            self.lock.release()

    def stop(self):
        self.shutdownThread = True
        self.event.set()

    def housekeeping(self):
        while True:
            self.event.wait(3600)
            if self.shutdownThread:
                return

            self.lock.acquire()
            try:
                if self.sbh_username is not None and self.sbh_password is not None:
                    self.sbh.login(self.sbh_username,
                                   self.sbh_password)
            except SBOLError as ex:
                self._LOGGER.error(''.join(traceback.format_exception(etype=type(ex),
                                                                      value=ex,
                                                                      tb=ex.__traceback__)))
            self.lock.release()
