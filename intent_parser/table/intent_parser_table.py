from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.intent_parser_exceptions import TableException

class IntentParserTable(object):
    """
    
    """

    def __init__(self, table_parser):
        self._rows = {}
        self._cols = {}
        self._table_parser = table_parser

    def add_row(self, length):
        next_row_index = len(self._row)
        for col_index in range(length):
            self._add_cell(next_row_index, col_index)
        
    def _add_cell(self, row_index, col_index):
        if row_index not in self._rows:
            self._rows[row_index] = []
        if col_index not in self._cols:
            self._cols[col_index] = []
        
        cell = IntentParserCell() 
        self._rows[row_index].append(cell)
        self._cols[col_index].append(cell)
        
    def edit_cell(self, row_index, col_index, content):  
        if row_index not in self._rows or col_index not in self._cols:
            raise IndexError('Cannot access cell (%s, %s)' % row_index, col_index)
        cell = self._rows[row_index][col_index]
        for paragraph, link in self._table_parser.parse_cell(content):
            cell.add_paragraph(paragraph, link)

    def number_of_rows(self):
        return len(self._rows)
    
    def row_cells(self, row):
        return len(self._rows[row]) 
            
    def get_row_by_index(self, row_index):
        rows = self._table['tableRows']
        if row_index < 0 or row_index >= len(rows):
            raise TableException('Index out of bound')
        return rows[row_index]
        
    def get_cell_from_row(self, row, cell_index):
        """
        Get cell from a given row
        """
        cells = row['tableCells']
        if cell_index < 0 or cell_index > len(cells):
            raise TableException('Index out of bound')
        cell = cells[cell_index]
        converted_cell = IntentParserCell(cell)
        return converted_cell
    

        
        