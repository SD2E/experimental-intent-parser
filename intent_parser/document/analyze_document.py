import threading

class AnalyzeDocument(object):

    def __init__(self, http_message):
        self.analyze_processing_map_lock = threading.Lock()
        self.analyze_processing_map = {}
        self.analyze_thread = threading.Thread(target=self._initiate_document_analysis,
                                               args=(http_message,)  # without comma you'd get a... TypeError
        )

    def start_document_analysis(self):
        self._initiate_document_analysis()
        self.analyze_thread.start()

    def stop_document_analysis(self):
        self.analyze_thread.join()

    def _initiate_document_analysis(self, http_message):
        pass