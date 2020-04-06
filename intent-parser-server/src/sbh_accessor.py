import sbol
import tenacity
import threading
import traceback

class SBHAccessor:
    def __init__(self, *, sbh_url):
        self.shutdownThread = False
        self.event = threading.Event()
        self.lock = threading.Lock()
        self.sbh = sbol.PartShop(sbh_url)
        self.sbh_username = None
        self.sbh_password = None

        self.housekeeping_thread = \
            threading.Thread(target=self.housekeeping)
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

        except Exception as e:
            self.lock.release()
            raise e

        self.lock.release()
        return fret

    def spoof(self, sbh_spoofing_prefix):
        self.lock.acquire()

        try:
            fret = self.sbh.spoof(sbh_spoofing_prefix)

        except Exception as e:
            self.lock.release()
            raise e

        self.lock.release()
        return fret

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

        except Exception as e:
            self.lock.release()
            raise e

        self.lock.release()
        return fret


    def exists(self, document_url):
        self.lock.acquire()

        try:
            fret = self.sbh.exists(document_url)

        except Exception as e:
            self.lock.release()
            raise e

        self.lock.release()
        return fret

    def submit(self, document, collection, flags):
        self.lock.acquire()

        try:
            fret = self.sbh.submit(document, collection,
                                   flags)

        except Exception as e:
            self.lock.release()
            raise e

        self.lock.release()
        return fret

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
                if self.sbh_username is not None and \
                   self.sbh_password is not None:

                    self.sbh.login(self.sbh_username,
                                   self.sbh_password)

            except Exception as ex:
                print(''.join(traceback.format_exception(etype=type(ex),
                                                         value=ex,
                                                         tb=ex.__traceback__)))

            self.lock.release()
