"""
Exceptions supported by Intent Parser
"""
 
class Error(Exception):
    pass

class ConnectionException(Exception):
    # TODO: this class must be deleted. Use RequestErrorExceptin to handle this.
    def __init__(self, http_status, content=""):
        self.http_status = http_status
        self.content = content

class RequestErrorException(Exception):
    def __init__(self, http_status, errors=[], warnings=[]):
        self.http_status = http_status
        self.errors = errors
        self.warnings = warnings

    def get_http_status(self):
        return self.http_status

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

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