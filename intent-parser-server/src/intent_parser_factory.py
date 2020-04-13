from intent_parser import IntentParser


class IntentParserFactory(object):
    '''
    Creator for Intent Parser
    '''


    def __init__(self, datacatalog_config, sbh, sbol_dictionary):
        self.datacatalog_config = datacatalog_config 
        self.sbh = sbh 
        self.sbol_dictionary = sbol_dictionary
        
    def create_intent_parser(self, document_id):
        return IntentParser(document_id, self.datacatalog_config, self.sbh, self.sbol_dictionary)
        