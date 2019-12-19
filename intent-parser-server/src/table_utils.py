import collections
import re
from git import index

_Token = collections.namedtuple('Token', ['type', 'value'])
_temperature_units = {'c' : 'celsius', 
                      'f' : 'fahrenheit'}
_fluid_units = {'fold' : 'X'}
_abbreviated_unit_dict = {'temperature' : _temperature_units,
                          'fluid' : _fluid_units}

def transform_cell(cell, units, cell_type=None):
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
    tokens = []
    token_specification = [
        ('NUMBER',   r'\d+(\.\d*)?'),
        ('NAME',       r'[A-Za-z]+'),
        ('ID',       r'[A-Za-z0-9_]+'),
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
    
    if tokens[-1][0] == 'NAME':
        unit = tokens[-1][1].lower()
        if unit in abbrev_units:
            unit = abbrev_units[unit]
        if unit in units:
            return units[unit]
    return 'unspecified'

def _canonicalize_units(units):
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
        