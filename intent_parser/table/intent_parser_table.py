from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.intent_parser_exceptions import TableException

class IntentParserTable(object):
    """
    
    """

    def __init__(self, table):
        self._table = table

    def number_of_rows(self):
        return self._table['rows']
    
    def number_of_cells(self, row):
        return len(row['tableCells'])
            
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
        return cells[cell_index]
    

        
        