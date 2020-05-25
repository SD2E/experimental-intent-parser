from intent_parser.intent_parser_exceptions import TableException

class IntentParserTable(object):
    """
    
    """
    def __init__(self):
        self._rows = [] 

    def add_row(self, row):
        self._rows.append(row)
       
    def get_cell(self, row_index, col_index):  
        row = self.get_row(row_index)
        if col_index < 0 or col_index >= len(row):
            raise IndexError('Cannot access cell (%s, %s)' % (row_index, col_index))
        return self._rows[row_index][col_index] 
    
    def get_row(self, row_index):
        if row_index < 0 or row_index >= len(self._rows):
            raise IndexError('Index out of bound')
        return self._rows[row_index]
    
    def number_of_rows(self):
        return len(self._rows)  
    
    def remove_row(self, row_index):
        if row_index < 0 or row_index >= self.number_of_rows():
            raise IndexError('Cannot remove row at index %s' % row_index)
        self._rows.pop(row_index)
    
        
        