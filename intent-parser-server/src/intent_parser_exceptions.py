
class Error(Exception):
    pass
    
class TableException(Error):
    '''
    Class for catch exceptions related to parsing a table. 
    '''
       
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message    
    
    def get_message(self):
        ''' 
        Message reporting the error. 
        '''
        return self.message

    def get_expression(self):
        ''' 
        The expression causing the error. 
        '''
        return self.expression