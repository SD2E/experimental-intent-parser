from intent_parser.table import table_utils

class IntentParserTable(object):
    """
    Intent Parser's representation of a table. 
    """
    def __init__(self):
        self._rows = [] 
        self._caption_index = None  
        self._header_index = None

    def add_row(self, row):
        self._rows.append(row)
    
    def caption(self):
        if self._caption_index is None:
            return ''
        row = self.get_row(self._caption_index)
        for col_index in range(len(row)):
            cell = self.get_cell(self._caption_index, col_index)
            if table_utils.is_table_caption(cell.get_text()):
                return table_utils.extract_table_caption(cell.get_text())
        return ''
    
    def caption_row_index(self):
        return self._caption_index
    
    def data_row_index(self):
        header_index = self.header_row_index()
        if header_index is None:
            return None
        if header_index+1 >= len(self._rows):
            return None 
        return header_index + 1 
    
    def get_cell(self, row_index, col_index):  
        row = self.get_row(row_index)
        if col_index < 0 or col_index >= len(row):
            raise IndexError('Cannot access cell (%s, %s)' % (row_index, col_index))
        return self._rows[row_index][col_index] 
    
    def header_row_index(self):
        if self._header_index is None:
            return None 
        return self._header_index
    
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
    
    def set_caption_row_index(self, index):
        self._caption_index = index
        
    def set_header_row_index(self, index):
        self._header_index = index
    
        
        