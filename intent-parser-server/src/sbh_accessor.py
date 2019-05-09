import sbol
import threading
import time

class SBHAccessor:
    def __init__(self, *, sbh_url):
        self.lock = threading.Lock()
        self.sbh = sbol.PartShop(sbh_url)
        self.sbh_username = None
        self.sbh_password = None

        self.housekeeping_thread = \
            threading.Thread(target=self.housekeeping)
        self.housekeeping_thread.start()
        

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


    def housekeeping(self):
        while True:
            time.sleep(3600 * 6)
            
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
