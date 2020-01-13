import logging
import table_utils

class LabTable(object):
    '''
    Class for parsing Lab table
    '''
    
    _logger = logging.getLogger('intent_parser_server')

    def __init__(self):
        pass
       
    def parse_table(self, table):
        rows = table['tableRows']
        numRows = len(rows)
        labRow = rows[0]
        numCols = len(labRow['tableCells'])
        if numRows > 1 or numCols > 1:
            self._logger.info('WARNING: Lab table size differs from expectation! Expecting 1 row and 1 col, found %d rows and %d cols' % (numRows, numCols))
        
        # The lab text is expected to be in row 0, col 0 and have the form: Lab: <X>
        lab = table_utils.get_paragraph_text(labRow['tableCells'][0]['content'][0]['paragraph']).strip().split(sep=':')[1].strip()
        return lab