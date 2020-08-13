from datetime import datetime
from intent_parser.intent_parser_exceptions import TableException
import intent_parser.constants.intent_parser_constants as constants
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import collections
import re

class CellParser(object):
    """
    Parses the contents of a cell
    """
    _Token = collections.namedtuple('Token', ['type', 'value'])
    _fluid_units = {'x': 'X',
                    'fold': 'X',
                    'mmol': 'mM',
                    'uM': 'micromole'}
    _temperature_units = {'Celsius': 'celsius',
                          'celsius': 'celsius',
                          'C': 'celsius',
                          'c': 'celsius',
                          'Fahrenheit': 'fahrenheit',
                          'fahrenheit': 'fahrenheit',
                          'F': 'fahrenheit',
                          'f': 'fahrenheit'}
    _timepoint_units = {'hours': 'hour',
                        'hr': 'hour',
                        'h': 'hour'}
    _abbreviated_unit_dict = {'fluid': _fluid_units,
                              'temperature': _temperature_units,
                              'timepoints': _timepoint_units
                             }
    
    def __init__(self):
        self._cell_tokenizer = _CellContentTokenizer()
        self._experiment_id_tokenizer = _ExperimentIdTokenizer()
        self._lab_tokenizer = _LabTableTokenizer()
        self._table_tokenizer = _TableCaptionTokenizer()
        self._table_header_tokenizer = _TableHeaderTokenizer()
        self._cell_parser = _Parser()

    def extract_name_value(self, text):
        """
        Parse text to get a list of NAME strings.

        Args:
            text: a string

        Returns:
            A list of strings identified as a NAME.
        """
        cell_str = []
        result = []
        tokens = self._cell_tokenizer.tokenize(text)
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
        if len(cell_str) > 0:
            result.append(''.join(cell_str))
        return result

    def get_header_type(self, text):
        tokens = self._table_header_tokenizer.tokenize(text, keep_skip=False)
        if len(tokens) != 1:
            return 'UNKNOWN'
        return self._get_token_type(tokens[0])

    def has_lab_table_keyword(self, text, keyword):
        tokens = self._lab_tokenizer.tokenize(text)
        return len(tokens) > 0 and self._get_token_value(tokens[0]).lower() == keyword.lower()

    def is_experiment_id(self, text, lab_names={}):
        tokens = self._experiment_id_tokenizer.tokenize(text)

        if len(tokens) != 5:
            return False

        if self._get_token_type(tokens[0]) != 'KEYWORD' or self._get_token_type(tokens[2]) != 'NAME' or self._get_token_type(tokens[4]) != 'NAME':
            return False

        if self._get_token_value(tokens[2]) not in lab_names:
            return False

        return True

    def is_name(self, text):
        """
        Check if the content of a cell is alpha-numeric.
        """
        tokens = self._cell_tokenizer.tokenize(text)
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        if cell_type == 'NAME':
            return True
        return False

    def is_number(self, text):
        """
        Check if the content of a cell only has numbers.
        """
        tokens = self._cell_tokenizer.tokenize(text, keep_skip=False)
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        return cell_type == 'NUMBER'


    def is_table_caption(self, text):
        tokens = self._table_tokenizer.tokenize(text)
        return len(tokens) > 0 and self._get_token_type(tokens[0]) == 'KEYWORD'

    def is_valued_cell(self, text):
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
        tokens = self._cell_tokenizer.tokenize(text, keep_separator=False, keep_skip=False)
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        return cell_type == 'VALUES_UNIT' or cell_type == 'VALUE_UNIT_PAIRS'

    def parse_content_item(self, text, text_with_uri, fluid_units={}, timepoint_units={}):
        list_of_contents = []
        tokens = self._cell_tokenizer.tokenize(text, keep_skip=False)
        if len(tokens) < 1:
            raise TableException('Invalid value: %s does not contain a name' % text.get_text())
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        label, value, unit, timepoint_value, timepoint_unit = (None, None, None, None, None)
        if cell_type == 'NAME_VALUE_UNIT_TIMEPOINT':
            label, value, unit, timepoint_value, timepoint_unit = self._get_name_values_unit_timepoint(tokens)
            content = {dc_constants.NAME: self.create_name_with_uri(label, text_with_uri),
                       dc_constants.VALUE: value,
                       dc_constants.UNIT: self.process_content_item_unit(unit, fluid_units, timepoint_units),
                       dc_constants.TIMEPOINTS: self.process_timepoint(timepoint_value,
                                                                       timepoint_unit,
                                                                       timepoint_units)}
            list_of_contents.append(content)
        elif cell_type == 'NAME_VALUE_UNIT':
            label, value, unit = self._get_name_values_unit(tokens)
            content = {dc_constants.NAME: self.create_name_with_uri(label, text_with_uri),
                       dc_constants.VALUE: value,
                       dc_constants.UNIT: self.process_content_item_unit(unit, fluid_units, timepoint_units)}
            list_of_contents.append(content)
        elif cell_type == 'NAME':
            for label in self.extract_name_value(text):
                content = {dc_constants.NAME: self.create_name_with_uri(label, text_with_uri)}
                list_of_contents.append(content)
        else:
            raise TableException('Unable to parse %s' % text)
        return list_of_contents

    def process_boolean_flag(self, text):
        tokens = self._cell_tokenizer.tokenize(text, keep_separator=False, keep_skip=False)
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

    def process_content_item_unit(self, unit, fluid_units, timepoint_units):
        all_units = set()
        if fluid_units:
            all_units.update(fluid_units)
        if timepoint_units:
            all_units.update(timepoint_units)
        abbrev_units = self._abbreviated_unit_dict['fluid'] if 'fluid' is not None else {}
        abbrev_units.update(self._abbreviated_unit_dict['timepoints'] if 'timepoints' is not None else {})
        return self._determine_unit(unit, all_units, abbrev_units)

    def process_datetime_format(self, text):
        return datetime.strptime(text, '%Y/%m/%d %H:%M:%S')

    def process_lab_name(self, text, accepted_lab_names={}):
        tokens = self._lab_tokenizer.tokenize(text, keep_skip=False)
        if self._get_token_type(tokens[0]) != 'KEYWORD':
            return None
        if accepted_lab_names:
            for lab in accepted_lab_names:
                canonicalize_lab_name = lab.lower()
                processed_lab_name = self._get_token_value(tokens[-1]).lower()
                if canonicalize_lab_name == processed_lab_name:
                    return lab
        return None

    def process_lab_table_value(self, text):
        tokens = self._lab_tokenizer.tokenize(text, keep_skip=False)
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        if cell_type == 'KEYWORD_SEPARATOR_NAME' or cell_type == 'KEYWORD_SEPARATOR_VALUE':
            return self._get_token_value(tokens[-1])
        return None

    def process_names_with_uri(self, text, text_with_uri={}):
        """Process the given text for a list of string and its attached URL.
        Note that commas are used as delimators for specifying a list of words in a given text.

        Args:
            text: a string
            text_with_uri: a dictionary of terms with
        """
        tokens = self._cell_tokenizer.tokenize(text, keep_separator=True, keep_skip=False)
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        if cell_type != 'NAME':
            raise TableException('%s was not identified as an alpha numeric value.')

        for token in self.extract_name_value(text):
            name = token.strip()
            if '\n' in name:
                raise TableException('A newline was detected in %s.' % name)

            if text_with_uri and name in text_with_uri:
                yield name, text_with_uri[name]
            else:
                yield name, None

    def create_name_with_uri(self, label, uri_dictionary):
        stripped_label = label.strip()
        if stripped_label in uri_dictionary and uri_dictionary[stripped_label]:
            return {dc_constants.LABEL: stripped_label, dc_constants.SBH_URI: uri_dictionary[stripped_label]}

        return {dc_constants.LABEL: stripped_label, dc_constants.SBH_URI: 'NO PROGRAM DICTIONARY ENTRY'}

    def process_numbers(self, text):
        """
        Process a given string for a list of numbers, using commas as a delimiter.
        Args:
            text: a string
        Returns:
            A list of strings
        """
        result = []
        tokens = self._cell_tokenizer.tokenize(text, keep_separator=False, keep_skip=False)
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        if len(tokens) == 0:
            if self._get_token_type(tokens[0]) != 'NUMBER':
                raise TableException('%s is not a number' % text)
            return [self._get_token_value(0)]

        if len(tokens) == 2:
            if self._get_token_type(tokens[0]) == 'NUMBER':
                if self._get_token_type(tokens[1]) == 'NUMBER':
                    raise TableException('Commas must be used to provide a list of values for %s' % text)
                else:
                    raise TableException('%s does not follow correct format to specify a number or a list of number' % text)
        index = 0
        while index < len(tokens) - 2:
            if self._get_token_type(tokens[index]) == 'NUMBER':
                if self._get_token_type(tokens[index+1]) == 'SEPARATOR':
                    result.append(self._get_token_value(tokens[index]))
                    index += 2
                elif self._get_token_type(tokens[index+1]) == 'NUMBER':
                    raise TableException('Commas must be used to provide a list of values for %s' % text)
                else:
                    raise TableException('%s does not follow correct format to specify a number or a list of number' % text)
            else:
                raise TableException('%s does not follow correct format to specify a number or a list of number' % text)
        return result

    def process_reagent_header(self, text, text_with_uri, units, unit_type):
        tokens = self._cell_tokenizer.tokenize(text, keep_skip=False)
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        name = {}
        timepoint = {}
        if cell_type == 'NAME_SEPARATOR_VALUE_UNIT':
            label, timepoint_value, timepoint_unit = self._get_name_timepoint(tokens)
            name = self.create_name_with_uri(label, text_with_uri)
            abbrev_units = self._abbreviated_unit_dict[unit_type] if unit_type is not None else {}
            unit = self._determine_unit(timepoint_unit, units, abbrev_units)
            timepoint['value'] = float(timepoint_value)
            timepoint['unit'] = unit
        elif cell_type == 'NAME':
            name = self.create_name_with_uri(text.strip(), text_with_uri)

        return name, timepoint

    def process_timepoint(self, timepoint_value, timepoint_unit, timepoint_units):
        abbrev_units = self._abbreviated_unit_dict['timepoints'] if 'timepoints' is not None else {}
        validated_unit = self._determine_unit(timepoint_unit, timepoint_units, abbrev_units) 
        return [{'value': float(timepoint_value), 'unit': validated_unit}] 
        
    def process_table_caption_index(self, text):
        tokens = self._table_tokenizer.tokenize(text, keep_separator=False, keep_skip=False)
        table_value = self._get_token_value(tokens[1])
        return int(table_value)
        
    def process_values_unit(self, text, units={}, unit_type=None):
        """
        Parses the content of a cell to identify its value and unit. 
    
        Args: 
            text: the content of a cell
            units: a list of units that the cell can be assigned to as its unit type.
            unit_type: an optional variable to specify what type of cell this function is parsing. Default to None. 
        
        Return:
            a list of dictionaries for representing values and units. 
        Raises:
            A TableException is thrown for a cell that has no unit. 
        """
        result = []
        tokens = self._cell_tokenizer.tokenize(text, keep_separator=False, keep_skip=False)
        if not self.is_valued_cell(text):
            raise TableException('%s does not contain a unit' % text)
        if len(tokens) < 1:
            raise TableException('Invalid value: %s does not contain a numerical value' % text)
        cell_type = self._get_token_type(self._cell_parser.parse(tokens))
        
        abbrev_units = self._abbreviated_unit_dict[unit_type] if unit_type is not None else {}
        if cell_type == 'VALUES_UNIT':
            values, unit = self._get_values_unit(tokens)
            validated_unit = self._determine_unit(unit, units, abbrev_units)
            if units and validated_unit in units:
                for value in values:
                    result.append({'value': value, 'unit': validated_unit})
        elif cell_type == 'VALUE_UNIT_PAIRS':
            for value, unit in self._get_values_unit_pairs(tokens, units, unit_type):
                validated_unit = self._determine_unit(unit, units, abbrev_units)
                if units and validated_unit in units:
                    result.append({'value': value, 'unit': unit})
        return result

    def transform_strateos_string(self, text):
        """
        Parses a given string to generate strateos string patterns:
        1. number followed by a named value (ex: 1:microliter)
        2. named value

        Args:
            cell: Content of a cell

        Return:
            Array containing the result of the identified pattern for a cell.
        """
        tokens = self._cell_tokenizer.tokenize(text, keep_separator=False, keep_skip=False)
        if self.is_valued_cell(text):
            if len(tokens) == 2:
                if self._get_token_type(tokens[0]) == 'NUMBER' and self._get_token_type(tokens[1]) == 'NAME':
                    return [self._get_token_value(tokens[0]) + ':' + self._get_token_value(tokens[1])]
        return self.extract_name_value(text)

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
            determined_unit = abbrev_units[unit]
        
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
    

    


class _Tokenizer(object):
    
    _Token = collections.namedtuple('Token', ['type', 'value'])
    
    def __init__(self, specification):
        self.token_specification = specification

    def _preprocess_text(self, text):
       return text.replace('\n', '')

    def tokenize(self, text, keep_skip=True, keep_separator=True):
        tokens = []
        ignore_tokens = self._ignore_tokens(keep_skip, keep_separator)
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in self.token_specification)
        for mo in re.finditer(tok_regex, self._preprocess_text(text)):
            kind = mo.lastgroup
            value = mo.group()
            if kind not in ignore_tokens: 
                tokens.append(self._Token(kind, value))
        return tokens

    def _ignore_tokens(self, keep_skip, keep_separator):
        ignore_tokens = []
        if not keep_skip:
            ignore_tokens.append('SKIP')
        if not keep_separator:
            ignore_tokens.append('SEPARATOR')
        return ignore_tokens

class _CellContentTokenizer(_Tokenizer): 
    
    token_specification = [
            ('BOOLEAN_TRUE', r'True|true'),
            ('BOOLEAN_FALSE', r'False|false'),
            ('NUMBER',   r'\d+(\.\d*)?([eE]([-+])?\d+)?'),
            ('NAME',       r'[^\t \d\n,:@][^ \t\n,@]*'),
            ('SKIP',     r'([ \t\u000b\n])+'),
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

class _ExperimentIdTokenizer(_Tokenizer):
    token_specification = [
        ('KEYWORD', r'experiment|Experiment'),
        ('NAME', r'[^\t \n.]+'),
        ('SKIP', r'([ \t]|\u000b)+'),
        ('SEPARATOR', r'[.]')]

    def __init__(self):
        super().__init__(self.token_specification)
 
class _TableHeaderTokenizer(_Tokenizer): 
    
    token_specification = [
            (constants.HEADER_BATCH_TYPE, r'(Batch|batch)'),
            (constants.HEADER_CHANNEL_TYPE, r'(Channel|channel)'),
            (constants.HEADER_CONTENTS_TYPE, r'(Contents|contents)'),
            (constants.HEADER_CONTROL_TYPE_TYPE, r'(Control|control)[ \t\n]*(Type|type)'),
            (constants.HEADER_CONTROL_TYPE, r'(Control|control)'),
            (constants.HEADER_EXPERIMENT_ID_TYPE, r'([Ee]xperiment)[ \t\n]*([Ii][Dd])'),
            (constants.HEADER_EXPERIMENT_STATUS_TYPE, r'([Ee]xperiment)[ \t\n]*([Ss]tatus)'),
            (constants.HEADER_FILE_TYPE_TYPE, r'(File|file)[ \t\n]*-[ \t\n]*(Type|type)'),
            (constants.HEADER_LAST_UPDATED_TYPE, r'(Last|last)[ \t\n]*(Update|update)'),
            (constants.HEADER_MEASUREMENT_TYPE_TYPE, r'(Measurement|measurement)[ \t\n]*-[ \t\n]*(Type|type)'),
            (constants.HEADER_NOTES_TYPE, r'(Notes|notes)'),
            (constants.HEADER_ODS_TYPE, r'(Ods|ods|ODS)'),
            (constants.HEADER_PATH_TYPE, r'([Oo]utput)[ \t\n]*([Ff]rom)[ \t\n]*([Pp]ipeline)'),
            (constants.HEADER_PARAMETER_TYPE, r'(Parameter|parameter)'),
            (constants.HEADER_PARAMETER_VALUE_TYPE, r'(Value|value)'),
            (constants.HEADER_PIPELINE_STATUS_TYPE, r'(Pipeline|pipeline)[ \t\n]*(Status|status)'),
            (constants.HEADER_REPLICATE_TYPE, r'Replicate|replicate'),
            (constants.HEADER_SAMPLES_TYPE, r'(Samples|samples)'),
            (constants.HEADER_SKIP_TYPE,     r'([ \t\n]|\u000b)+'),
            (constants.HEADER_STATE_TYPE,   r'Processed|processed'),
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
            # ('NUMBER_LIST', _make_regex([_TokenMatcher('NUMBER'),
            #                              _TokenMatcher(_TokenMatcher('SEPARATOR') + '|' + _TokenMatcher('NUMBER'), qualifier='*')])),
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
