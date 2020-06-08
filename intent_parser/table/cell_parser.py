from intent_parser.intent_parser_exceptions import TableException
import collections
import re

class CellParser(object):
    """
    Parses the contents of a cell
    """
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
    
    def __init__(self):
        self._cell_tokenizer = _CellContentTokenizer() 
        self._lab_tokenizer = _LabTableTokenizer()
        self._table_tokenizer = _TableCaptionTokenizer()
        self._cell_parser = _Parser()
        
    def _is_lab_table(self, cell):
        tokens = self._lab_tokenizer.tokenize(cell.get_text())
        return len(tokens) > 0 and self._get_token_type(tokens[0]) == 'KEYWORD'
        
    def is_name(self, cell):
        """
        Check if the content of a cell is alpha-numeric.
        """
        tokens = self._cell_tokenizer.tokenize(cell.get_text())
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        if cell_type == 'NAME':
            return True
        return False 
    
    def is_number(self, cell):
        """
        Check if the content of a cell only has numbers.
        """ 
        for token in self._cell_tokenizer.tokenize(cell.get_text()):
            if self._get_token_type(token) == 'NAME':
                return False 
        return True 

    def is_table_caption(self, cell):
        tokens = self._table_tokenizer.tokenize(cell.get_text())
        return len(tokens) > 0 and self._get_token_type(tokens[0]) == 'KEYWORD'

    def is_valued_cell(self, cell):
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
        tokens = self._cell_tokenizer.tokenize(cell.get_text(), keep_space=False, keep_skip=False)
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        return cell_type == 'VALUES_UNIT' or cell_type == 'VALUE_UNIT_PAIRS'

    def parse_content_item(self, cell, fluid_units={}, timepoint_units={}):
        content = {} 
        tokens = self._cell_tokenizer.tokenize(cell.get_text(), keep_skip=False) 
        if len(tokens) < 1:
            raise TableException('Invalid value: %s does not contain a name' % cell.get_text())
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        label, value, unit, timepoint_value, timepoint_unit = (None, None, None, None, None)
        if cell_type == 'NAME_VALUE_UNIT_TIMEPOINT':
            label, value, unit, timepoint_value, timepoint_unit = self._get_name_values_unit_timepoint(tokens)
        elif cell_type == 'NAME_VALUE_UNIT':
            label, value, unit = self._get_name_values_unit(tokens)
        elif cell_type == 'NAME':
            label = self._get_name(tokens) 
        else:
            raise TableException('Unable to parse %s' % cell.get_text())
        
        uri_dictionary = cell.get_text_with_url()
        uri = 'NO PROGRAM DICTIONARY ENTRY' 
        if label in uri_dictionary and uri_dictionary[label]:
            uri = uri_dictionary[label]
        name = {'label': label, 'sbh_uri' : uri}  
        
        content['name'] = name
        
        if value:
            content['value'] = value
        
        if unit:
            if (fluid_units and unit in fluid_units) or (timepoint_units and unit in timepoint_units):
                content['unit'] = unit
            else:
                raise TableException('%s is not a valid fluid or timepoint unit.' % unit)
        if timepoint_value and timepoint_unit:
            if timepoint_unit in timepoint_units:
                content['timepoints'] = [{'value': float(timepoint_value), 'unit': timepoint_unit}] 
            else:
                raise TableException('%s is not a valid timepoint unit.' % timepoint_unit)
        return content
    
    def process_values_unit(self, cell, units={}, unit_type=None):
        """
        Parses the content of a cell to identify its value and unit. 
    
        Args: 
            cell: the content of a cell
            units: a list of units that the cell can be assigned to as its unit type.
            unit_type: an optional variable to specify what type of cell this function is parsing. Default to None. 
        
        Return:
            a list of dictionaries for representing values and units. 
        Raises:
            A TableException is thrown for a cell that has no unit. 
        """
        result = []
        tokens = self._cell_tokenizer.tokenize(cell.get_text(), keep_space=False, keep_skip=False) 
        if not self.is_valued_cell(cell): 
            raise TableException('%s does not contain a unit' % cell)
        if len(tokens) < 1:
            raise TableException('Invalid value: %s does not contain a numerical value' % cell.get_text())
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        
        if cell_type == 'VALUES_UNIT':
            values, unit = self._get_values_unit(tokens)
            if units and unit in units:
                for value in values:
                    result.append({'value': float(value), 'unit': unit})
        elif cell_type == 'VALUE_UNIT_PAIRS':
            for value,unit in self._get_values_unit_pairs(tokens, units, unit_type):
                result.append({'value': float(value), 'unit': unit})
        return result
            
    def _determine_unit(self, unit, units, abbrev_units):
        """
        Identify the unit assigned to an array of tokens.
        
        Args:
            unit: a unit
            units: A list of supported units.
            abbrev_units: A list of abbreviated units. 
            
        Returns:
            A unit
        Raises:
            TableException for invalid units
        """
        determined_unit = unit 
        if unit in abbrev_units:
            determined_unit = abbrev_units[unit].lower()
        
        if determined_unit not in units:
            raise TableException('%s is an invalid unit' % unit)
        return determined_unit

    def _get_values_unit_pairs(self, tokens, units, unit_type=None):
        index = 0
        while index < len(tokens) - 1:
            value = self._get_token_value(tokens[index])
            abbrev_units = self._abbreviated_unit_dict[unit_type] if unit_type is not None else {}
            unit = self._determine_unit(self._get_token_value(tokens[index+1]), 
                                        units, abbrev_units)
            index = index+2
            yield value, unit
        if index == len(tokens) - 1:
            yield self._get_token_value(tokens[index]), unit 
    
    def _get_values_unit(self, tokens):
        unit = self._get_token_value(tokens[-1])
        values = [self._get_token_value(token) for token in tokens[0:-1]]
        return values, unit 
    
    def _get_name_values_unit_timepoint(self, tokens):
        timepoint_unit = self._get_token_value(tokens[-1])
        timepoint_value = self._get_token_value(tokens[-2])
        unit = self._get_token_value(tokens[-4])
        value = self._get_token_value(tokens[-5])
        name = ' '.join([self._get_token_value(token) for token in tokens[0:-5]])
        return name, value, unit, timepoint_value, timepoint_unit
    
    def _get_name_values_unit(self, tokens):
        unit = self._get_token_value(tokens[-1])
        value = self._get_token_value(tokens[-2])
        name = ' '.join([self._get_token_value(token) for token in tokens[0:-2]])
        return name, value, unit
    
    def _get_name(self, tokens):
        name = ' '.join([self._get_token_value(token) for token in tokens])
        return name  
        
    
    def _get_token_type(self, token):
        return token[0]

    def _get_token_value(self, token):
        return token[1]
    
    def process_names(self, cell, check_name_in_url=False):
        result = []
        links = cell.get_text_with_url()
        for name in self.extract_name_value(cell):
            if check_name_in_url:
                if name in links and links[name] is not None:
                    result.append(links[name])
                else:
                    result.append(name)
            else:
                result.append(name)
        return result
    
    def extract_name_value(self, cell):
        """
        Parse text to get a list of NAME strings.
    
        Args:
            text: a string
    
        Returns:
            A list of strings identified as a NAME.
        """
        cell_str = []
        result = []
        tokens = self._cell_tokenizer.tokenize(cell.get_text())
        if self._get_token_type(tokens[-1]) == 'SKIP':
            tokens = tokens[:-1]
        for token in tokens:
            if self._get_token_type(token) == 'SKIP':
                if len(cell_str) > 0:
                    cell_str.append(self._get_token_value(token))
            elif self._get_token_type(token) == 'SEPARATOR':
                result.append(''.join(cell_str))
                cell_str = []
            else:
                cell_str.append(self._get_token_value(token))
        # if last item or cell does not contain SEPARATOR
        if len(cell_str) > 0 :
            result.append(''.join(cell_str))
        return result

class _Tokenizer(object):
    
    _Token = collections.namedtuple('Token', ['type', 'value'])
    
    def __init__(self, specification):
        self.token_specification = specification
        
    def tokenize(self, text, keep_skip=True, keep_space=True):
        tokens = []
        ignore_tokens = self._ignore_tokens(keep_skip, keep_space)
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in self.token_specification)
        for mo in re.finditer(tok_regex, text):
            kind = mo.lastgroup
            value = mo.group()
            if kind not in ignore_tokens: 
                tokens.append(self._Token(kind, value))
            if value.startswith('\u000b') :
                value = value.replace('\u000b', '')
        return tokens

    def _ignore_tokens(self, keep_skip, keep_space):
        ignore_tokens = []
        if not keep_skip:
            ignore_tokens.append('SKIP')
        if not keep_space:
            ignore_tokens.append('SEPARATOR')
        return ignore_tokens

class _CellContentTokenizer(_Tokenizer): 
    
    token_specification = [
            ('NUMBER',   r'\d+(\.\d*)?([eE]([-+])?\d+)?'),
            ('NAME',       r'[^\t \d,:@][^ \t,@]*'),
            ('SKIP',     r'([ \t]|\u000b)+'),
            ('SEPARATOR',     r'[,@]')]
    
    def __init__(self):
        super().__init__(self.token_specification)

class _LabTableTokenizer(_Tokenizer): 
    
    token_specification = [
            ('KEYWORD', r'Lab|lab'),
            ('NUMBER',   r'\d+(\.\d*)?([eE]([-+])?\d+)?'),
            ('NAME',       r'[^\t \d,:][^ \t,]*'),
            ('SKIP',     r'([ \t]|\u000b)+'),
            ('SEPARATOR',     r'[,]')]
    
    def __init__(self):
        super().__init__(self.token_specification)


class _TableCaptionTokenizer(_Tokenizer): 
    
    token_specification = [
            ('KEYWORD', r'Table|table'),
            ('NUMBER',   r'\d+(\.\d*)?([eE]([-+])?\d+)?'),
            ('NAME',       r'[^\t \d,:][^ \t,]*'),
            ('SKIP',     r'([ \t]|\u000b)+'),
            ('SEPARATOR',     r'[,]')]
    
    def __init__(self):
        super().__init__(self.token_specification)
 
class _TokenMatcher(object):
    def __init__(self, token_type, value='[^\(]+', qualifier='', group=None):
        self._type = token_type
        self._value = value
        self._qualifier = qualifier
        self._group = group
            
    def __str__(self):
        if self._group:
            return '(\(%s,(?P<%s>%s)\))%s' % (self._type, self._group, self._value, self._qualifier)
        return '(\(%s,%s\))%s' % (self._type, self._value, self._qualifier)

class _AnyMatcher(_TokenMatcher):
    def __init__(self, token_type='[^,]+', value='[^\(]+', qualifier=''):
        super().__init__(token_type, value, qualifier)
            
class _EndMatcher(_TokenMatcher):
    def __init__(self):
        super().__init__(token_type='END')
            
    def __str__(self):
        return '\(%s\)' % (self._type)
   
def _make_regex(token_matchers, qualifier=''):
    return r'(%s)%s\(END_OF_MATCH\)' % (''.join([str(token_matcher) for token_matcher in token_matchers]), qualifier) 
            
class _Parser(_Tokenizer):
    token_specification = [
            ('NAME_VALUE_UNIT_TIMEPOINT', _make_regex([_TokenMatcher('NAME', qualifier='+'),
                                                       _TokenMatcher('NUMBER'),
                                                       _TokenMatcher('NAME'),
                                                       _TokenMatcher('SEPARATOR'),
                                                       _TokenMatcher('NUMBER'),
                                                       _TokenMatcher('NAME')])
            ),
            ('NAME_VALUE_UNIT',  _make_regex([_TokenMatcher('NAME', qualifier='+'),
                                              _TokenMatcher('NUMBER'),
                                              _TokenMatcher('NAME')])
            ),
            ('VALUES_UNIT',  _make_regex([_TokenMatcher('NUMBER', qualifier='+'),
                                         _TokenMatcher('NAME')])
            ),
            ('VALUE_UNIT_PAIRS',  _make_regex([_TokenMatcher('NUMBER'),
                                               _TokenMatcher('NAME')], qualifier='+')
            ),
            ('NAME', _make_regex([_TokenMatcher('(NAME|SEPARATOR|SKIP)', qualifier='+')])),
            ('NUMBER', _make_regex([_TokenMatcher('NUMBER', qualifier='+')])),
            # Fall through if none match
            ('NOT_DEFINED', _make_regex([_AnyMatcher()], qualifier='+'))
        ]
    
    def __init__(self):
        super().__init__(self.token_specification)
        
    def tokenize(self, text):
        tokens = []
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in self.token_specification)
        for mo in re.finditer(tok_regex, text):
            kind = mo.lastgroup
            tokens.append(kind)
        return tokens
    
    def parse(self, tokens):
        token_str = '%s(END_OF_MATCH)' % (''.join(['(%s,%s)' % token for token in tokens])) 
        return self.tokenize(token_str) 


PARSER = CellParser()
 
        