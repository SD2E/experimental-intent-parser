import collections
import constants
import re


_Token = collections.namedtuple('Token', ['type', 'value'])
_temperature_units = {'c' : 'celsius', 
                      'f' : 'fahrenheit'}
_fluid_units = {'fold' : 'X'}
_abbreviated_unit_dict = {'temperature' : _temperature_units,
                          'fluid' : _fluid_units}


def detect_lab_table(table):
    """
    Determine if the given table is a lab table, defining the lab to run measurements.
    """
    rows = table['tableRows']
    numRows = len(rows)
    labRow = rows[0]
    numCols = len(labRow['tableCells'])
    lab = get_paragraph_text(labRow['tableCells'][0]['content'][0]['paragraph'])
    return numRows == 1 and numCols == 1 and 'lab' in lab.lower()


def detect_new_measurement_table(table):
    """
    Scan the header row to see if it contains what we expect in a new-style measurements table.
    """
    found_replicates = False
    found_strain = False
    found_measurement_type = False
    found_file_type = False

    rows = table['tableRows']
    headerRow = rows[0]
    for cell in headerRow['tableCells']:
        cellTxt = get_paragraph_text(cell['content'][0]['paragraph']).strip()
        found_replicates |= cellTxt == constants.COL_HEADER_REPLICATE 
        found_strain |= cellTxt == constants.COL_HEADER_STRAIN 
        found_measurement_type |= cellTxt == constants.COL_HEADER_MEASUREMENT_TYPE
        found_file_type |= cellTxt == constants.COL_HEADER_FILE_TYPE 

    return found_replicates and found_strain and found_measurement_type and found_file_type


def get_paragraph_text(paragraph):
    elements = paragraph['elements']
    paragraph_text = '';

    for element_index in range( len(elements) ):
        element = elements[ element_index ]

        if 'textRun' not in element:
            continue
        text_run = element['textRun']
        paragraph_text += text_run['content']

    return paragraph_text
    
def is_number(cell):
    tokens = _tokenize(cell)
    if len(tokens) > 0:
        return False
    return tokens[0][0] == 'NUMBER'

def extract_number_value(cell):
    """
    Retrieve the content of a cell containing a list of numbers.
    
    Args:
        cell: the content of a cell.
        
    Returns:
        An array of strings that are identified as a number.
    """
    cell_values = []
    tokens = _tokenize(cell)
    for token in tokens:
        if token[0] == 'NUMBER':
            cell_values.append(token[1])
    return cell_values

def extract_name_value(cell):
    """
    Retrieve the content of a cell containing a list of strings.
    
    Args:
        cell: the content of a cell.
    
    Returns:
        An array of strings that are identified as a name.
    """
    cell_str = []
    tokens = _tokenize(cell)
    for token in tokens:
        if token[0] == 'NAME':
            cell_str.append(token[1])
    return cell_str

def transform_cell(cell, units, cell_type=None):
    """
    Parses the content of a cell to identify its value and unit. 
    
    Args: 
        cell: the content of a cell
        units: a list of units that the cell can be assigned to as its unit type.
        cell_type: an optional variable to specify what type of cell this function is parsing.
        
    Return:
        Yield two variable values found from a cell's content. 
        The first variable represents the cell's content.
        The second variable represents an identified unit for the cell.
    """
    tokens = _tokenize(cell) 
    if not _is_valued_cells(tokens):
        yield cell, 'unspecified'
    else:
        index = 0
        
        abbrev_units = _abbreviated_unit_dict[cell_type] if cell_type is not None else {}
        unit = _determine_unit(tokens, _canonicalize_units(units), abbrev_units)
        while index < len(tokens) - 1:
            value = tokens[index][1]
            if tokens[index+1][0] == 'NAME':
                index = index+2
            # throw an exception if token mismatch unit
            else:
                index = index+1
            yield value, unit
            
        if index == len(tokens) - 1:
            yield tokens[index][1], unit 

def _tokenize(cell):
    """
    Tokenize the content from a given cell into numbers and names. 
    
    Args: 
        cell: Content of a cell
        
    Returns:
        A tokenized representation for the content of a cell.
        A token with type NUMBER has a integer value parsed from a cell.
        A token with type NAME has a string value parsed from a cell. 
    """
    tokens = []
    token_specification = [
        ('NUMBER',   r'\d+(\.\d*)?'),
        ('NAME',       r'[A-Za-z][A-Za-z0-9_]*'),
        ('SKIP',     r'[ \t]+'),
        ('SEPARATOR',     r'[,]')
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    for mo in re.finditer(tok_regex, cell):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'SKIP' or kind == 'SEPARATOR':
            continue
        tokens.append(_Token(kind, value))
    return tokens
     
def _is_valued_cells(tokens):
    """
    Check if an array of tokens follows a valued-cell pattern. 
    A valued-cell pattern can be a list of integer values propagated with units. 
    Alternatively, the valued-cell pattern can be a list of integer values ending with unit.
    
    Args:
        tokens: a representation of a valued-cell pattern
    
    Returns:
        True if tokens follows a valued-cell pattern.
        Otherwise, False is returned.
    """
    if len(tokens) < 2:
        return False
    next = 'NUMBER'
    for token in tokens:
        if next == 'NUMBER' and token[0] != 'NUMBER':
            return False
        if next == 'EITHER'and token[0] not in ['NUMBER', 'NAME']:
            return False
        if token[0] == 'NUMBER':
            next = 'EITHER' 
        else:
            next = 'NUMBER'
            
    return True

def _determine_unit(tokens, units, abbrev_units):
    """
    Identify the unit assigned to an array of tokens.
    
    Args:
        tokens: An array of tokens. 
        units: A list of units that an array of tokens can map to.
        abbrev_units: A list of abbreviated units. 
        
    Returns:
        An identified unit corresponding to tokens. 
        unspecified is returned if no unit were identified. 
    """
    if tokens[-1][0] == 'NAME':
        unit = tokens[-1][1].lower()
        if unit in abbrev_units:
            unit = abbrev_units[unit].lower()
        if unit in units:
            return units[unit]
    return 'unspecified'

def _canonicalize_units(units):
    """
    Standardized units to a lower case representation. 
    
    Args: 
        units: A list of strings
        
    Returns:
        A dictionary that maps a lower case unit to its corresponding unit.
    """
    unit_dict = {}
    for unit in units:
        unit_dict[unit.lower()] = unit 
    return unit_dict

    
if __name__ == '__main__':
    statements = '1 c, 2 c, 3 c'
    tokens = _tokenize(statements)
    print(_is_valued_cells(tokens))
    for value, unit in transform_cell(statements, ['celsius', 'nM'], cell_type='temperature'):
        print(value + ' ' + unit)
    for token in _tokenize(statements):
        print(token)
        