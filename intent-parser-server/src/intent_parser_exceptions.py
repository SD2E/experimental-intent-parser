
class Error(Exception):
    pass
    
class TableException(Error):
    
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message    