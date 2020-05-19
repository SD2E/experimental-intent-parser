from intent_parser.intent_parser_exceptions import TableException
from intent_parser.table.intent_parser_cell import IntentParserCell
class IntentParserTable(object):
    """
    
    """
    def __init__(self):
       self._rows = [] 

    def add_row(self, row):
        self._rows.append(row)
       
    def get_cell(self, row_index, col_index):  
        if row_index not in self._rows or col_index not in self._cols:
            raise IndexError('Cannot access cell (%s, %s)' % row_index, col_index)
        return self._rows[row_index][col_index] 
    
    def get_row(self, row_index):
        rows = self._table_parser['tableRows']
        if row_index < 0 or row_index >= len(rows):
            raise TableException('Index out of bound')
        return rows[row_index]
    
    def number_of_rows(self):
        return len(self._rows)  
    
    def remove_row(self, row_index):
        if row_index < 0 or row_index >= self.number_of_rows():
            raise IndexError('Cannot remove row at index %s' % row_index)
        self._rows.pop(row_index)
    
        
        