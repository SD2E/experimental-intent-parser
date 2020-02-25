from intent_parser_exceptions import TableException 
import collections
import constants
import re


_Token = collections.namedtuple('Token', ['type', 'value'])
_fluid_units = {'fold' : 'X',
                'mmol' : 'mM',
                'um' : 'micromole'}
_temperature_units = {'c' : 'celsius', 
                      'f' : 'fahrenheit'}
_timepoint_units = {'hours' : 'hour',
                    'hr' : 'hour',
                    'h' : 'hour'}
_abbreviated_unit_dict = {'fluid' : _fluid_units,
                          'temperature' : _temperature_units,
                          'timepoints' : _timepoint_units
                          }


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

def detect_parameter_table(table):
    has_parameter_field = False
    has_parameter_value = False 
    rows = table['tableRows']
    headerRow = rows[0]
    for cell in headerRow['tableCells']:
        cellTxt = get_paragraph_text(cell['content'][0]['paragraph']).strip()
        if cellTxt == constants.COL_HEADER_PARAMETER:
            has_parameter_field = True
        elif cellTxt == constants.COL_HEADER_PARAMETER_VALUE:
            has_parameter_value = True
    return has_parameter_field and has_parameter_value

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
    """
    Check if the cell only contains numbers.
    """ 
    tokens = _tokenize(cell)
    if len(tokens) < 0:
        return False
    if len(tokens) == 1:
        return tokens[0][0] == 'NUMBER'
    for tok in tokens:
        if tok[0] == 'NAME':
            return False
    
    return True

def is_name(cell):
    """
    Check if the cell only contains named strings.
    """
    tokens = _tokenize(cell)
    if len(tokens) < 0:
        return False
    if len(tokens) == 1:
        return _get_token_type(tokens[0]) == 'NAME'
    for token in tokens:
        if _get_token_type(token) == 'NUMBER':
            return False
    return True
        
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
        if _get_token_type(token) == 'NUMBER':
            cell_values.append(_get_token_value(token))
    return cell_values

def extract_name_value(cell):
    """
    Retrieve the content of a cell containing a list of strings.
    
    Args:
        cell: the content of a cell.
    
    Returns:
        A list of named values
    """
    cell_str = []
    result = []
    tokens = _tokenize(cell)
    if _get_token_type(tokens[-1]) == 'SKIP':
        tokens = tokens[:-1]
    for token in tokens:
        if _get_token_type(token) == 'SKIP':
            if len(cell_str) > 0:
                cell_str.append(_get_token_value(token))
        elif _get_token_type(token) == 'SEPARATOR':
            result.append(''.join(cell_str))
            cell_str = []
        else:
            cell_str.append(_get_token_value(token))
    # if last item or cell does not contain SEPARATOR
    if len(cell_str) > 0 :
        result.append(''.join(cell_str))
    
    return result

def transform_strateos_string(cell):
    """
    Parses a given string to generate strateos string patterns:
    1. number followed by a named value (ex: 1:microliter)
    2. named value
    
    Args:
        cell: Content of a cell
    
    Return:
    Array containing the result of the identified pattern for a cell.
    """
    
    tokens = _tokenize(cell, keep_space=False) 
    if _is_valued_cells(tokens):
        if len(tokens) == 2:
            if _get_token_type(tokens[0]) == 'NUMBER' and _get_token_type(tokens[1]) == 'NAME':
                return [_get_token_value(tokens[0]) + ':' + _get_token_value(tokens[1])]
    
    return extract_name_value(cell)

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
        raise TableException(cell, 'does not contain a unit') 
    else:
        index = 0
        tokens = [token for token in tokens if _get_token_type(token) not in ['SEPARATOR', 'SKIP']]
        abbrev_units = _abbreviated_unit_dict[cell_type] if cell_type is not None else {}
        unit = _determine_unit(tokens, _canonicalize_units(units), abbrev_units)
        while index < len(tokens) - 1:
            value = tokens[index][1]
            
            if _get_token_type(tokens[index+1]) == 'NAME':
                index = index+2
            else:
                index = index+1
            yield value, unit
            
        if index == len(tokens) - 1:
            yield _get_token_value(tokens[index]), unit 

def _get_token_type(token):
    return token[0]

def _get_token_value(token):
    return token[1]

def _tokenize(cell, keep_space=True):
    """
    Tokenize the content from a given cell into numbers and names. 
    
    Args: 
        cell: Content of a cell
        keep_space: A flag to include white space tokens in the result. Default to True
        
    Returns:
        A tokenized representation for the content of a cell.
        A token with type NUMBER has a integer value parsed from a cell.
        A token with type NAME has a string value parsed from a cell. 
    """
    tokens = []
    token_specification = [
        ('NUMBER',   r'\d+(\.\d*)?([eE]([-+])?\d+)?'),
        ('NAME',       r'[^\t \d,][^ \t,]*'),
        ('SKIP',     r'[ \t]+'),
        ('SEPARATOR',     r'[,]')
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    for mo in re.finditer(tok_regex, cell):
        kind = mo.lastgroup
        value = mo.group()
        if kind != 'SKIP' or keep_space: 
            tokens.append(_Token(kind, value))
        if value.startswith('\u000b') :
            value = value.replace('\u000b', '') 
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
    tokens = [token for token in tokens if _get_token_type(token) != 'SKIP']
    next_token = 'NUMBER'
    for token in tokens:
        if next_token == 'NUMBER' and _get_token_type(token) != 'NUMBER':
            return False
        if next_token == 'SEPARATOR' and _get_token_type(token) != 'SEPARATOR':
            return False
        if next_token == 'EITHER'and _get_token_type(token) not in ['NUMBER', 'NAME', 'SEPARATOR']:
            return False
        
        if _get_token_type(token) == 'NUMBER': 
            next_token = 'EITHER' 
        elif _get_token_type(token) == 'NAME':
            next_token = 'SEPARATOR'
        elif _get_token_type(token) == 'SEPARATOR':
            next_token = 'NUMBER'
        else:
            return False
            
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
    if _get_token_type(tokens[-1]) != 'NAME':
        raise TableException(_get_token_value(tokens[-1]), 'does not contain a unit')
    unit = _get_token_value(tokens[-1]).lower()
    if unit in abbrev_units:
        unit = abbrev_units[unit].lower()
    
    if unit not in units:
        raise TableException(unit, 'is an invalid unit')
    return units[unit]

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

   
        