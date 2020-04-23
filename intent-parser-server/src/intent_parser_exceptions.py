
class Error(Exception):
    pass

class ConnectionException(Exception):
    def __init__(self, http_status, content=""):
        self.http_status = http_status
        self.code = http_status.value
        self.message = http_status.name
        self.content = content

class TableException(Error):
    '''
    Report errors when parsing tables from running Intent Parser's p
    '''
       
    def __init__(self, message):
        self.message = message
    
    def get_message(self):
        ''' 
        Message reporting the error. 
        '''
        return self.message

class DictionaryMaintainerException(Error):
    """
    Report errors related to getting information from SBOL Dictionary Maintainer
    """
    
    def __init__(self, message):
        self.message = message
        
    def get_message(self):
        return self.message