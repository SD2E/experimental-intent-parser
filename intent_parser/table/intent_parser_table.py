from intent_parser.table.intent_parser_table_type import TableType
import intent_parser.table.cell_parser as cell_parser

class IntentParserTable(object):
    """
    Intent Parser's representation of a table. 
    """
    def __init__(self):
        self._rows = [] 
        self._caption_index = None  
        self._header_index = None
        self._table_start_index = None
        self._table_end_index = None
        self._table_type = TableType.UNKNOWN

    def add_row(self, row):
        self._rows.append(row)
    
    def caption(self):
        """
        Process table caption.
        Returns:
            An integer value representing the table index. If no caption exist, then None is returned.
        """
        if self._caption_index is not None:
            row = self.get_row(self._caption_index)
            for col_index in range(len(row)):
                cell = self.get_cell(self._caption_index, col_index)
                if cell_parser.PARSER.is_table_caption(cell.get_matched_term()):
                    return cell_parser.PARSER.process_table_caption_index(cell.get_matched_term())
        return None
    
    def caption_row_index(self):
        """
        Retrieves the row index where the caption appears in this table.
        Returns:
            An integer.
        """
        return self._caption_index
    
    def data_row_start_index(self):
        header_index = self.header_row_index()
        if header_index is None:
            return None
        if header_index+1 >= len(self._rows):
            return None 
        return header_index + 1 
    
    def get_cell(self, row_index, col_index):
        """Get a particular cell from the table.

        Args:
            row_index: an integer value to represent the index of a row in the table.
            col_index: an integer value to represent the index of a column in the table.
            Note that table is zero-indexed for rows and columns.
        Returns:
            A IntentParserCell object.
        """
        row = self.get_row(row_index)
        if col_index < 0 or col_index >= len(row):
            raise IndexError('Cannot access cell (%s, %s)' % (row_index, col_index))
        return self._rows[row_index][col_index]

    def get_table_start_index(self):
        return self._table_start_index

    def get_table_end_index(self):
        return self._table_end_index

    def get_table_type(self):
        return self._table_type
    
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

    def set_table_start_index(self, index):
        self._table_start_index = index

    def set_table_end_index(self, index):
        self._table_end_index = index

    def set_table_type(self, table_type):
        self._table_type = table_type
