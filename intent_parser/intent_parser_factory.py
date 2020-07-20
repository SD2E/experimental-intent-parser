from intent_parser.intent_parser import IntentParser
from intent_parser.lab_experiment import LabExperiment

class IntentParserFactory(object):
    """
    Creator for Intent Parser
    """

    def __init__(self, datacatalog_config, sbh, sbol_dictionary):
        self.datacatalog_config = datacatalog_config 
        self.sbh = sbh 
        self.sbol_dictionary = sbol_dictionary
       
    def create_lab_experiment(self, document_id, bookmarks={}, local_file_path=None): 
        lab_experiment = LabExperiment(document_id, bookmarks)
        if local_file_path:
            pass 
        else:  
            lab_experiment.load_from_google_doc()
        return lab_experiment
    
    def create_intent_parser(self, document_id, bookmarks={}, local_file_path=None):
        lab_experiment = self.create_lab_experiment(document_id, bookmarks, local_file_path)
        return IntentParser(lab_experiment, self.datacatalog_config, self.sbh, self.sbol_dictionary)

