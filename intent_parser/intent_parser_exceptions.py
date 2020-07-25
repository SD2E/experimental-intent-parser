"""
Exceptions supported by Intent Parser
"""
 
class Error(Exception):
    pass

class ConnectionException(Exception):
    def __init__(self, http_status, content=""):
        self.http_status = http_status
        self.content = content

class IntentParserException(Error):

    def __init__(self, message):
        self.message = message

    def get_message(self):
        return self.message

class TableException(Error):
    """
    Report errors when parsing tables for Intent Parser.
    """
       
    def __init__(self, message):
        self.message = message
    
    def get_message(self):
        """
        Message reporting the error.
        """
        return self.message

class DictionaryMaintainerException(Error):
    """
    Report errors related to getting information from SBOL Dictionary Maintainer.
    """
    
    def __init__(self, message):
        self.message = message
        
    def get_message(self):
        return self.message