from intent_parser.intent_parser_exceptions import TableException
import intent_parser.constants.intent_parser_constants as constants
import intent_parser.table.table_utils as table_utils
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
        self._table_header_tokenizer = _TableHeaderTokenizer()
        self._cell_parser = _Parser()

    def is_datetime_format(self, cell):
        pass

    def process_datetime_format(self, cell):
        pass
        
    def is_lab_table(self, cell):
        tokens = self._lab_tokenizer.tokenize(cell.get_text())
        return len(tokens) > 0 and self._get_token_type(tokens[0]) == 'KEYWORD'

    def has_lab_table_keyword(self, cell, keyword):
        tokens = self._lab_tokenizer.tokenize(cell.get_text())
        return len(tokens) > 0 and self._get_token_value(tokens[0]).lower() == keyword.lower()

    def process_lab_table_value(self, cell):
        tokens = self._lab_tokenizer.tokenize(cell.get_text(), keep_skip=False)
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        if cell_type == 'KEYWORD_SEPARATOR_NAME' or cell_type == 'KEYWORD_SEPARATOR_VALUE':
            return self._get_token_value(tokens[-1])
        return 'TBD'

    def process_lab_name(self, cell):
        tokens = self._lab_tokenizer.tokenize(cell.get_text(), keep_skip=False)
        if self._get_token_type(tokens[0]) != 'KEYWORD':
            return constants.TACC_SERVER
        return self._get_token_value(tokens[-1])

    def get_header_type(self, cell):
        cell_text = cell.get_text()
        tokens = self._table_header_tokenizer.tokenize(cell_text, keep_skip=False)
        if len(tokens) != 1:
            return 'UNKNOWN'
        return self._get_token_type(tokens[0])
        
           
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
        list_of_contents = []
        tokens = self._cell_tokenizer.tokenize(cell.get_text(), keep_skip=False) 
        if len(tokens) < 1:
            raise TableException('Invalid value: %s does not contain a name' % cell.get_text())
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        label, value, unit, timepoint_value, timepoint_unit = (None, None, None, None, None)
        if cell_type == 'NAME_VALUE_UNIT_TIMEPOINT':
            label, value, unit, timepoint_value, timepoint_unit = self._get_name_values_unit_timepoint(tokens)
            content = {} 
            content['name'] = self.process_name_with_uri(label, cell.get_text_with_url())
            content['value'] = value
            content['unit'] = self.process_content_item_unit(unit, fluid_units, timepoint_units)
            content['timepoints'] = self.process_timepoint(timepoint_value, timepoint_unit, timepoint_units)
            list_of_contents.append(content)
        elif cell_type == 'NAME_VALUE_UNIT':
            label, value, unit = self._get_name_values_unit(tokens)
            content = {} 
            content['name'] = self.process_name_with_uri(label, cell.get_text_with_url())
            content['value'] = value
            content['unit'] = self.process_content_item_unit(unit, fluid_units, timepoint_units)
            list_of_contents.append(content)
        elif cell_type == 'NAME':
            labels = table_utils.extract_name_value(cell.get_text())
            for label in labels:
                content = {} 
                content['name'] = self.process_name_with_uri(label, cell.get_text_with_url())
                list_of_contents.append(content)
        else:
            raise TableException('Unable to parse %s' % cell.get_text())
        return list_of_contents
    
    def process_reagent_header(self, cell, units, unit_type):
        tokens = self._cell_tokenizer.tokenize(cell.get_text(), keep_skip=False) 
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        name = {}
        timepoint = {}
        if cell_type == 'NAME_SEPARATOR_VALUE_UNIT':
            label, timepoint_value, timepoint_unit = self._get_name_timepoint(tokens)
            name = self.process_name_with_uri(label, cell.get_text_with_url())
            abbrev_units = self._abbreviated_unit_dict[unit_type] if unit_type is not None else {}
            unit = self._determine_unit(timepoint_unit, units, abbrev_units)
            timepoint['value'] = float(timepoint_value)
            timepoint['unit'] = unit 
        elif cell_type == 'NAME':
            label = ' '.join([self._get_token_value(token) for token in tokens])
            name = self.process_name_with_uri(label, cell.get_text_with_url())
        else:
            label, value, unit = table_utils.parse_reagent_header(cell.get_text(), units, unit_type)
            if value and unit:
                timepoint['value'] = float(value)
                timepoint['unit'] = unit 
            name = self.process_name_with_uri(label, cell.get_text_with_url())
        return name, timepoint

    def process_name_with_uri(self, label, uri_dictionary):
        uri = 'NO PROGRAM DICTIONARY ENTRY' 
        if label in uri_dictionary and uri_dictionary[label]:
            uri = uri_dictionary[label]
        return {'label': label, 'sbh_uri' : uri}  
    
    def process_content_item_unit(self, unit, fluid_units, timepoint_units):
        all_units = set()
        if fluid_units:
            all_units.update(fluid_units)
        if timepoint_units:
            all_units.update(timepoint_units)
        abbrev_units = self._abbreviated_unit_dict['fluid'] if 'fluid' is not None else {}
        abbrev_units.update(self._abbreviated_unit_dict['timepoints'] if 'timepoints' is not None else {})
        return self._determine_unit(unit, all_units, abbrev_units) 
    
    def process_timepoint(self, timepoint_value, timepoint_unit, timepoint_units):
        abbrev_units = self._abbreviated_unit_dict['timepoints'] if 'timepoints' is not None else {}
        validated_unit = self._determine_unit(timepoint_unit, timepoint_units, abbrev_units) 
        return [{'value': float(timepoint_value), 'unit': validated_unit}] 
        
    def process_table_caption(self, cell):
        tokens = self._table_tokenizer.tokenize(cell.get_text(), keep_space=False, keep_skip=False)
        table_keyword = self._get_token_value(tokens[0]).lower()
        table_value = self._get_token_value(tokens[1])
        return ''.join([table_keyword, table_value]) 
        
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
        
        abbrev_units = self._abbreviated_unit_dict[unit_type] if unit_type is not None else {}
        if cell_type == 'VALUES_UNIT':
            values, unit = self._get_values_unit(tokens)
            validated_unit = self._determine_unit(unit, 
                                        units, abbrev_units)
            if units and validated_unit in units:
                for value in values:
                    result.append({'value': float(value), 'unit': validated_unit})
        elif cell_type == 'VALUE_UNIT_PAIRS':
            for value,unit in self._get_values_unit_pairs(tokens, units, unit_type):
                validated_unit = self._determine_unit(unit, 
                                        units, abbrev_units)
                if units and validated_unit in units:
                    result.append({'value': float(value), 'unit': unit})
        return result

    def process_boolean_flag(self, cell):
        tokens = self._cell_tokenizer.tokenize(cell.get_text(), keep_space=False, keep_skip=False)
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        if cell_type == 'BOOLEAN_FLAG':
            token_type = self._get_token_type(tokens[0])
            if token_type == 'BOOLEAN_FALSE':
                return False
            elif token_type == 'BOOLEAN_TRUE':
                return True
        if self._get_token_value(tokens[0]).lower() == 'false':
            return False
        elif self._get_token_value(tokens[0]).lower() == 'true':
            return True
        return None


    def process_numbers(self, cell):
        result = []
        tokens = self._cell_tokenizer.tokenize(cell.get_text(), keep_space=False, keep_skip=False)
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        if cell_type == 'NUMBER':
            for token in tokens:
                result.append(self._get_token_value(token))
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
    
    def _get_name_timepoint(self, tokens):
        timepoint_unit = self._get_token_value(tokens[-1])
        timepoint_value = self._get_token_value(tokens[-2])
        name = ' '.join([self._get_token_value(token) for token in tokens[0:-3]])
        return name, timepoint_value, timepoint_unit
    
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
    
    def _get_token_type(self, token):
        return token[0]

    def _get_token_value(self, token):
        return token[1]
    
    def process_names(self, cell, check_name_in_url=False):
        """
        Parses a NAME cell.
        Args:
            cell: An IntentParserCell
            check_name_in_url: a boolean flag default to False. Set flag to True in order to use linked URLs when present.
        Returns:
            a list of NAME strings.
        """
        result = []
        links = cell.get_text_with_url()
        for name in self.extract_name_value(cell):
            stripped_name = name.strip()
            if check_name_in_url:
                if stripped_name in links and links[stripped_name] is not None:
                    result.append(links[stripped_name])
                else:
                    result.append(stripped_name)
            else:
                result.append(stripped_name)
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
            if value.startswith('\u000b'):
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
            ('BOOLEAN_TRUE', r'True|true'),
            ('BOOLEAN_FALSE', r'False|false'),
            ('DATE', r'\d{4}-\d{2}-\d{2}')
            ('TIME', r'\d{2}:\d{2}:\d{2}')
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
            ('NAME',       r'[^\t \d,:][^ \t,:]*'),
            ('SKIP',     r'([ \t]|\u000b)+'),
            ('SEPARATOR',     r'[,:]')]
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
 
class _TableHeaderTokenizer(_Tokenizer): 
    
    token_specification = [
            (constants.HEADER_BATCH_TYPE, r'(Batch|batch)'),
            (constants.HEADER_CHANNEL_TYPE, r'(Channel|channel)'),
            (constants.HEADER_CONTENTS_TYPE, r'(Contents|contents)'),
            (constants.HEADER_CONTROL_TYPE_TYPE, r'(Control|control)[ \t\n]*(Type|type)'),
            (constants.HEADER_CONTROL_TYPE, r'(Control|control)'),
            (constants.HEADER_FILE_TYPE_TYPE, r'(File|file)[ \t\n]*-[ \t\n]*(Type|type)'),
            (constants.HEADER_LAST_UPDATED_TYPE, r'(Last|last)[ \t\n]*(Updated|updated)'),
            (constants.HEADER_MEASUREMENT_TYPE_TYPE, r'(Measurement|measurement)[ \t\n]*-[ \t\n]*(Type|type)'),
            (constants.HEADER_NOTES_TYPE, r'(Notes|notes)'),
            (constants.HEADER_ODS_TYPE, r'(Ods|ods|ODS)'),
            (constants.HEADER_PATH_TYPE, r'(Path|path)'),
            (constants.HEADER_PARAMETER_TYPE, r'(Parameter|parameter)'),
            (constants.HEADER_PARAMETER_VALUE_TYPE, r'(Value|value)'),
            (constants.HEADER_PIPELINE_STATUS_TYPE, r'(Pipeline|pipeline)[ \t\n]*(Status|status)'),
            (constants.HEADER_REPLICATE_TYPE, r'Replicate|replicate'),
            (constants.HEADER_SAMPLES_TYPE, r'(Samples|samples)'),
            (constants.HEADER_SKIP_TYPE,     r'([ \t\n]|\u000b)+'),
            (constants.HEADER_STATE_TYPE,   r'State|state'),
            (constants.HEADER_STRAINS_TYPE,   r'Strains|strains'),
            (constants.HEADER_TEMPERATURE_TYPE, r'(Temperature|temperature)'),
            (constants.HEADER_TIMEPOINT_TYPE, r'(Timepoint|timepoint)'),
            (constants.HEADER_UNKNOWN_TYPE, r'.+')]
    
    def __init__(self):
        super().__init__(self.token_specification)
        
class _TokenMatcher(object):
    def __init__(self, token_type, value='[^»]+', qualifier='', group=None):
        self._type = token_type
        self._value = value
        self._qualifier = qualifier
        self._group = group
            
    def __str__(self):
        if self._group:
            return '«%s,(?P<%s>%s)»%s' % (self._type, self._group, self._value, self._qualifier)
        return '(«%s,%s»)%s' % (self._type, self._value, self._qualifier)

class _AnyMatcher(_TokenMatcher):
    def __init__(self, token_type='[^,]+', value='[^»]+', qualifier=''):
        super().__init__(token_type, value, qualifier)
   
def _make_regex(token_matchers, qualifier=''):
    return r'(%s)%s«END_OF_MATCH»' % (''.join([str(token_matcher) for token_matcher in token_matchers]), qualifier)
                
class _Parser(_Tokenizer):
    token_specification = [
            ('BOOLEAN_FLAG', _make_regex([_TokenMatcher('(BOOLEAN_FALSE|BOOLEAN_TRUE)')])),
            ('DATETIME', _make_regex([_TokenMatcher('DATE'),
                                      _TokenMatcher('TIME')])),
            ('KEYWORD_SEPARATOR_NAME', _make_regex([_TokenMatcher('NAME'),
                                                    _TokenMatcher('SEPARATOR', value=':'),
                                                    _TokenMatcher('NAME')])),
            ('KEYWORD_SEPARATOR_VALUE', _make_regex([_TokenMatcher('NAME'),
                                                _TokenMatcher('SEPARATOR', value=':'),
                                                _TokenMatcher('NUMBER')])),
            ('NAME_VALUE_UNIT_TIMEPOINT', _make_regex([_TokenMatcher('NAME', qualifier='+'),
                                                       _TokenMatcher('NUMBER'),
                                                       _TokenMatcher('NAME'),
                                                       _TokenMatcher('SEPARATOR'),
                                                       _TokenMatcher('NUMBER'),
                                                       _TokenMatcher('NAME')])
            ),
            ('NAME_SEPARATOR_VALUE_UNIT', _make_regex([_TokenMatcher('NAME', qualifier='+'),
                                                       _TokenMatcher('SEPARATOR', value='@'),
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
            ('TABLE', _make_regex([_TokenMatcher('KEYWORD', qualifier='+')])),
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
        token_str = '%s«END_OF_MATCH»' % (''.join(['«%s,%s»' % token for token in tokens]))
        return self.tokenize(token_str) 


PARSER = CellParser()
