from intent_parser.intent_parser_exceptions import TableException 
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.utils.intent_parser_utils as intent_parser_utils
import collections
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

def parse_cell(cell):
    content = cell['content']
    for paragraph_index in range(len(content)):
        paragraph = content[paragraph_index]['paragraph']
        url = None
        
        if 'link' in paragraph and 'url' in paragraph['link']:
            url = paragraph['link']['url']
            
        list_of_contents = []
        for element in paragraph['elements']: 
            result = element['textRun']['content']
            list_of_contents.append(result)
        flatten_content = ''.join(list_of_contents)
        yield flatten_content, url

def detect_lab_table(table):
    """
    Determine if the given table is a lab table, defining the lab to run measurements.
    """
    rows = table['tableRows']
    num_rows = len(rows)
    has_lab = False
    num_cols = 1
    for row_index in range(len(rows)):
        curr_row = rows[row_index]
        cells = curr_row['tableCells']
        if len(cells) != 1:
            num_cols = len(cells)
        for cell_index in range(len(cells)):
            cell_content = cells[cell_index]['content'][0]['paragraph']
            value = intent_parser_utils.get_paragraph_text(cell_content)
            canonicalize_value = value.lower()
            if canonicalize_value.startswith('lab'):
                has_lab = True
    return num_rows > 0 and num_cols == 1 and has_lab 


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
        cellTxt = intent_parser_utils.get_paragraph_text(cell['content'][0]['paragraph']).strip()
        found_replicates |= cellTxt == intent_parser_constants.COL_HEADER_REPLICATE 
        found_strain |= cellTxt == intent_parser_constants.COL_HEADER_STRAIN 
        found_measurement_type |= cellTxt == intent_parser_constants.COL_HEADER_MEASUREMENT_TYPE
        found_file_type |= cellTxt == intent_parser_constants.COL_HEADER_FILE_TYPE 

    return found_replicates and found_strain and found_measurement_type and found_file_type

def detect_parameter_table(table):
    has_parameter_field = False
    has_parameter_value = False 
    rows = table['tableRows']
    headerRow = rows[0]
    for cell in headerRow['tableCells']:
        cellTxt = intent_parser_utils.get_paragraph_text(cell['content'][0]['paragraph']).strip()
        if cellTxt == intent_parser_constants.COL_HEADER_PARAMETER:
            has_parameter_field = True
        elif cellTxt == intent_parser_constants.COL_HEADER_PARAMETER_VALUE:
            has_parameter_value = True
    return has_parameter_field and has_parameter_value

def is_number(cell):
    """
    Check if the cell only contains numbers.
    """ 
    tokens = _tokenize(cell)
    if len(tokens) < 0:
        return False
    if len(tokens) == 1:
        return _get_token_type(tokens[0]) == 'NUMBER'
    for token in tokens:
        if _get_token_type(token) == 'NAME':
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

def extract_table_caption(cell):
    tokens = _tokenize(cell, keep_space=False)
    caption = []
    for token in tokens:
        if _get_token_type(token) == 'SEPARATOR' and _get_token_value(token) == ':':
            break
        caption.append(token)
    return ''.join([_get_token_value(token) for token in caption]).strip() 
    

def extract_str_after_prefix(cell, seperator_type=':'):
    """
    Parses a given cell with a specified prefix.
    
    Args:
        cell: a string representing a cell's content.
        seperator_type: a character that separates the string's prefix and postfix
    Returns:
        A prefix and postfix.
    Raises:
        ValueException if the cell does not have enough content to perform the desired task.
        TableException if the prefix cannot be found from the given cell.
    """
    tokens = _tokenize(cell, keep_space=False, 
                       name_specification='[^\t \d,:][^ \t,:]*', 
                       seperator_specification='[,:]')
    prefix = []
    postfix = []
    encountered_seperator = False 
    for token in tokens:
        if _get_token_type(token) == 'SEPARATOR' and _get_token_value(token) == seperator_type:
            encountered_seperator = True
            continue
        
        if encountered_seperator:
            postfix.append(token)
        else:
            prefix.append(token)
    appended_prefix = ''.join([_get_token_value(token) for token in prefix])
    appended_postfix = ''.join([_get_token_value(token) for token in postfix])
    return appended_prefix, appended_postfix 
               
        
def extract_number_value(cell):
    """
    Parse cell containing a number or a list of numbers.
    
    Args:
        cell: the content of a cell.
        
    Returns:
        A list of strings that identified as a NUMBER.
    """
    cell_values = []
    tokens = _tokenize(cell)
    for token in tokens:
        if _get_token_type(token) == 'NUMBER':
            cell_values.append(_get_token_value(token))
    return cell_values

def extract_name_value(cell):
    """
    Parse cell containing a string or a list of strings.
    
    Args:
        cell: the content of a cell.
    
    Returns:
        A list of strings identified as a NAME.
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

def parse_and_append_named_value_unit(cell_txt, unit_type, unit_list):
    """
    Parses the content of a cell to get a name, followed by a value, followed by a unit.
    Args:
        cell_txt: content of cell
        unit_type: type of unit for specifying the value
        unit_list: list of units
        
    Raises:
        TableException: 
        ValueError: Invalid value for a cell 
    """
    tokens = _tokenize(cell_txt) 
    index = 0
    tokens = [token for token in tokens if _get_token_type(token) not in ['SEPARATOR', 'SKIP']]
    abbrev_units = _abbreviated_unit_dict[unit_type] if unit_type is not None else {}
    unit = _determine_unit(tokens, _canonicalize_units(unit_list), abbrev_units)
    
    if len(tokens) % 3 > 0:
        raise ValueError('Cannot parse named value unit for cell %s.' % cell_txt)
    
    while index < len(tokens):
        if _get_token_type(tokens[index]) != 'NAME':
            raise ValueError('No name specified. Invalid named value unit cell.')
        if _get_token_type(tokens[index+1]) != 'NUMBER':
            raise ValueError('No value specified. Invalid named value unit cell.')
        if _get_token_type(tokens[index+2]) != 'NAME':
            raise ValueError('No unit specified. Invalid named value unit cell.')
        
        name = _get_token_value(tokens[index]) 
        value = _get_token_value(tokens[index+1]) 
        unit = _get_token_value(tokens[index+2]) 
        
        yield name, value, unit

def parse_and_append_value_unit(cell_txt, cell_type, unit_list):
    """
    Parses a string to determine numerical values and units. 
    
    Args:
        cell_txt: a string that can contain a list of value followed by a unit by using commas as a separator. 
        cell_type: the type of units that this cell_txt is describing. (ex: fluid, temperature, or timepoints)
        unit_list: a list of strings that the function will use for referring to units.
    
    Returns:
        A list of dictionaries. The dictionary key represents a numerical value. 
        The dictionary value represents a unit corresponding to the value.
    Raises:
         TableException: For cells with no unit
    """
    result = []
    for value,unit in transform_cell(cell_txt, unit_list, cell_type=cell_type):
        temp_dict = {'value' : float(value), 'unit' : unit}
        result.append(temp_dict)
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
        cell_type: an optional variable to specify what type of cell this function is parsing. Default to None. 
        
    Return:
        Yield two variables. 
        The first variable represents the cell's content.
        The second variable represents an identified unit for the cell.
    
    Raises:
        A TableException is thrown for a cell that has no unit. 
    """
    tokens = _tokenize(cell) 
    if not _is_valued_cells(tokens):
        raise TableException('%s does not contain a unit' % cell)
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

def _tokenize(cell, keep_space=True, 
              name_specification='[^\t \d,:][^ \t,]*', 
              seperator_specification='[,]'):
    """
    Identify NUMBER and NAME pattern from a cell by classifying the pattern into tokens. 
    
    Args: 
        cell: Content of a cell
        keep_space: A flag to include identifying white space tokens in the result. Default to True
        
    Returns:
        A list of tokens for the content of a cell.
        A token with type NUMBER has a integer value parsed from a cell.
        A token with type NAME has a string value parsed from a cell. 
    """
    tokens = []
    token_specification = [
        ('NUMBER',   r'\d+(\.\d*)?([eE]([-+])?\d+)?'),
        ('NAME',       r'%s' % name_specification),
        ('SKIP',     r'[ \t]+'),
        ('SEPARATOR',     r'%s' % seperator_specification)
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

def is_valued_cells(cell_txt):
    """
    Check if a string follows a valued-cell pattern. 
    A valued-cell pattern can be a list of integer values propagated with units. 
    Alternatively, the valued-cell pattern can be a list of integer values ending with unit.
    
    Args:
        cell_txt: a string 
    
    Returns:
        True if tokens follows a valued-cell pattern.
        Otherwise, False is returned.
    """
    tokens = _tokenize(cell_txt)
    return _is_valued_cells(tokens)

def _is_valued_cells(tokens):
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
    Raises:
        TableException for invalid units
    """
    if _get_token_type(tokens[-1]) != 'NAME':
        raise TableException('%s does not contain a unit' % _get_token_value(tokens[-1]))
    unit = _get_token_value(tokens[-1]).lower()
    if unit in abbrev_units:
        unit = abbrev_units[unit].lower()
    
    if unit not in units:
        raise TableException('%s is an invalid unit' % unit)
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

   
        