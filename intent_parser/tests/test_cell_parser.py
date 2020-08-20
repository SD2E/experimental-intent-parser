from intent_parser.intent_parser_exceptions import TableException
from intent_parser.table.cell_parser import CellParser
from intent_parser.table.intent_parser_cell import IntentParserCell
import datetime
import unittest

class CellParserTest(unittest.TestCase):

    def setUp(self):
        self.parser = CellParser()

    def tearDown(self):
        pass
    
    def test_reagent_header_without_timepoint(self):
        cell = IntentParserCell()
        cell.add_paragraph('name1')
        name, _ = self.parser.process_reagent_header(cell.get_text(),
                                                     cell.get_text_with_url(),
                                                     units={'hour'},
                                                     unit_type='timepoints')
        self.assertEqual('name1', name['label'])
    
    def test_reagent_alphanumeric_header_with_timepoint(self):
        cell = IntentParserCell()
        cell.add_paragraph('BE1 @ 15 hours')
        name, timepoint = self.parser.process_reagent_header(cell.get_text(),
                                                             cell.get_text_with_url(),
                                                             units={'hour'},
                                                             unit_type='timepoints')
        self.assertEqual('BE1', name['label'])
        self.assertEqual('NO PROGRAM DICTIONARY ENTRY', name['sbh_uri'])
        self.assertEqual(timepoint['value'], 15.0)
        self.assertEqual(timepoint['unit'], 'hour')
            
    def test_reagent_header_with_timepoint(self):
        cell = IntentParserCell()
        cell.add_paragraph('name @ 15 hours')
        name, timepoint = self.parser.process_reagent_header(cell.get_text(),
                                                             cell.get_text_with_url(),
                                                             units={'hour'},
                                                             unit_type='timepoints')
        self.assertEqual('name', name['label'])
        self.assertEqual('NO PROGRAM DICTIONARY ENTRY', name['sbh_uri'])
        self.assertEqual(timepoint['value'], 15.0)
        self.assertEqual(timepoint['unit'], 'hour')
        
    def test_parse_content_item_with_name(self):
        cell = IntentParserCell()
        cell.add_paragraph('name')
        results = self.parser.parse_content_item(cell.get_text(), cell.get_text_with_url())
        self.assertEqual(len(results), 1)
        result = results[0]
        name = result['name']
        self.assertEqual(2, len(name))
        self.assertEqual('name', name['label'])
        self.assertEqual('NO PROGRAM DICTIONARY ENTRY', name['sbh_uri'])

    def test_cell_values_with_named_spacing(self):
        cell_str = 'Yeast_Extract_Peptone_Adenine_Dextrose (a.k.a. YPAD Media)'
        name = self.parser.extract_name_value(cell_str)
        self.assertEqual(1, len(name))
        self.assertEqual(cell_str, name[0])

    def test_cell_values_with_named_and_numerical_spacing(self):
        cell_str = 'B. subtilis 168 PmtlA-comKS'
        name = self.parser.extract_name_value(cell_str)
        self.assertEqual(1, len(name))
        self.assertEqual(cell_str, name[0])

    def test_cell_with_trailing_whitespace(self):
        cell_str = 'Yeast1_, Yeast2_, Yeast3_ '
        exp_res = ['Yeast1_', 'Yeast2_', 'Yeast3_']
        names = self.parser.extract_name_value(cell_str)
        self.assertEqual(3, len(names))
        self.assertListEqual(exp_res, names)

    def test_cell_with_strateos_number_unit(self):
        cell_str = '5 microliter'
        actual_res = self.parser.transform_strateos_string(cell_str)
        self.assertEqual(1, len(actual_res))
        self.assertEqual('5:microliter', actual_res[0])

    def test_cell_with_strateos_name(self):
        cell_str = 'sc_media'
        actual_res = self.parser.transform_strateos_string(cell_str)
        self.assertEqual(1, len(actual_res))
        self.assertEqual('sc_media', actual_res[0])

    def test_cell_with_unit_containing_multiple_abbreviations(self):
        cell_str = '1 h, 2 hr, 3 hours'
        expected_values = ['1', '2', '3']
        result = self.parser.process_values_unit(cell_str, units={'hour'}, unit_type='timepoints')
        self.assertEqual(3, len(result))
        self.assertEqual({'value': '1', 'unit': 'hour'}, result[0])
        self.assertEqual({'value': '2', 'unit': 'hour'}, result[1])
        self.assertEqual({'value': '3', 'unit': 'hour'}, result[2])

    def test_cell_with_unicode_characters(self):
        cell_str = '\x0bApp'
        self.assertTrue('App', self.parser.extract_name_value(cell_str))
        
    def test_parse_content_item_with_list_of_names(self):
        cell = IntentParserCell()
        cell.add_paragraph('name1, name2, name3')
        results = self.parser.parse_content_item(cell.get_text(), cell.get_text_with_url())
        self.assertEqual(3, len(results))
        name1 = results[0]['name']
        name2 = results[1]['name']
        name3 = results[2]['name']
        self.assertEqual(name1, {'label': 'name1', 'sbh_uri': 'NO PROGRAM DICTIONARY ENTRY'})
        self.assertEqual(name2, {'label': 'name2', 'sbh_uri': 'NO PROGRAM DICTIONARY ENTRY'})
        self.assertEqual(name3, {'label': 'name3', 'sbh_uri': 'NO PROGRAM DICTIONARY ENTRY'})
        
    def test_parse_content_item_with_name_value_unit(self):
        cell = IntentParserCell()
        cell.add_paragraph('name1 123 unit')
        results = self.parser.parse_content_item(cell.get_text(),
                                                 cell.get_text_with_url(),
                                                 timepoint_units={'unit', 'timeunit'})
        self.assertEqual(len(results), 1)
        result = results[0]
        name = result['name']
        self.assertEqual(2, len(name))
        self.assertEqual('name1', name['label'])
        self.assertEqual('NO PROGRAM DICTIONARY ENTRY', name['sbh_uri'])
        self.assertEqual('123', result['value'])
        self.assertEqual('unit', result['unit'])
        
    def test_parse_content_item_with_name_value_unit_timepoint(self):
        cell = IntentParserCell()
        cell.add_paragraph('name1 name2 123 unit @ 15 timeunit')
        results = self.parser.parse_content_item(cell.get_text(),
                                                 cell.get_text_with_url(),
                                                 timepoint_units={'unit', 'timeunit'})
        self.assertEqual(len(results), 1)
        result = results[0]
        name = result['name']
        timepoints = result['timepoints']
        self.assertEqual(2, len(name))
        self.assertEqual(1, len(timepoints))
        self.assertEqual('name1 name2', name['label'])
        self.assertEqual('NO PROGRAM DICTIONARY ENTRY', name['sbh_uri'])
        self.assertEqual('123', result['value'])
        self.assertEqual('unit', result['unit'])
        self.assertEqual(15.0, timepoints[0]['value'])
        self.assertEqual('timeunit', timepoints[0]['unit'])
        
    def test_parse_content_item_with_name_uri_value_unit(self):
        cell = IntentParserCell()
        cell.add_paragraph('name1', link='https://hub.sd2e.org/user/sd2e/design/beta_estradiol/1')
        cell.add_paragraph('123 unit')
        results = self.parser.parse_content_item(cell.get_text(),
                                                 cell.get_text_with_url(),
                                                 timepoint_units={'unit', 'timeunit'})
        self.assertEqual(len(results), 1)
        result = results[0]
        name = result['name']
        self.assertEqual(2, len(name))
        self.assertEqual('name1', name['label'])
        self.assertEqual('https://hub.sd2e.org/user/sd2e/design/beta_estradiol/1', name['sbh_uri'])
        self.assertEqual('123', result['value'])
        self.assertEqual('unit', result['unit'])

    def test_names_without_separators(self):
        self.assertTrue(self.parser.is_name('foo'))
        
    def test_names_with_separators(self):
        self.assertTrue(self.parser.is_name('one, two X'))
        
    def test_names_from_numerical_values(self):
        self.assertFalse(self.parser.is_name('1, 2'))
        
    def test_numbers(self):
        self.assertTrue(self.parser.is_number('1, 2'))
        self.assertTrue(self.parser.is_number('12'))
        self.assertFalse(self.parser.is_number('12, 24 X'))
        self.assertFalse(self.parser.is_number('X'))

    def test_cell_values_with_exponent(self):
        self.assertTrue(self.parser.is_number('5e-06'))
        self.assertTrue(self.parser.is_number('5e+06'))
        self.assertTrue(self.parser.is_number('5e06'))
        self.assertTrue(self.parser.is_number('2.05e7'))
        self.assertFalse(self.parser.is_number('2.0e.07'))
        self.assertFalse(self.parser.is_number('2.0e'))

    def test_is_value_with_units(self):
        self.assertTrue(self.parser.is_valued_cell('1 X'))
        self.assertTrue(self.parser.is_valued_cell('1 X, 2 unit, 3 mm'))
        self.assertTrue(self.parser.is_valued_cell('1, 2, 3 X'))
        self.assertFalse(self.parser.is_valued_cell('1 X, 2, 3'))
        self.assertFalse(self.parser.is_valued_cell('Modified M9 Media + Kan 5_ug_per_ml'))

    def test_value_unit(self):
        result = self.parser.process_values_unit('3 hour', units={'hour'}, unit_type='timepoints')
        self.assertEqual(1, len(result))
        self.assertEqual({'value': '3', 'unit': 'hour'}, result[0])

    def test_cell_values_with_special_character(self):
        result = self.parser.process_values_unit('3 %',
                                                 units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'},
                                                 unit_type='timepoints')
        self.assertEqual(1, len(result))
        self.assertEqual({'value': '3', 'unit': '%'}, result[0])

    def test_units_with_backslash(self):
        result = self.parser.process_values_unit('9 g/L',
                                                 units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'},
                                                 unit_type='timepoints')
        self.assertEqual(1, len(result))
        self.assertEqual({'value': '9', 'unit': 'g/L'}, result[0])
        
    def test_leading_values_unit(self):
        result = self.parser.process_values_unit('1, 2,3 hour', units={'hour'}, unit_type='timepoints')
        self.assertEqual(3, len(result))
        self.assertEqual({'value': '1', 'unit': 'hour'}, result[0])
        self.assertEqual({'value': '2', 'unit': 'hour'}, result[1])
        self.assertEqual({'value': '3', 'unit': 'hour'}, result[2])
        
    def test_value_unit_pairs(self):
        result = self.parser.process_values_unit('1 X, 2 mM ,3 micromole',
                                                 units={'X', 'mM', 'micromole'},
                                                 unit_type='fluid')
        self.assertEqual(3, len(result))
        self.assertEqual({'value': '1', 'unit': 'X'}, result[0])
        self.assertEqual({'value': '2', 'unit': 'mM'}, result[1])
        self.assertEqual({'value': '3', 'unit': 'micromole'}, result[2])

    def test_cell_without_units(self):
        with self.assertRaises(TableException):
            _, _ = self.parser.process_values_unit('1, 2, 3', units=['X'], unit_type='fluid')

    def test_cell_with_unit_abbreviation(self):
        result = self.parser.process_values_unit('1, 2, 3 fold', units=['X'], unit_type='fluid')
        self.assertEqual(3, len(result))
        self.assertEqual({'value': '1', 'unit': 'X'}, result[0])
        self.assertEqual({'value': '2', 'unit': 'X'}, result[1])
        self.assertEqual({'value': '3', 'unit': 'X'}, result[2])

    def test_cell_with_unit_without_spacing(self):
        result = self.parser.process_values_unit('1X', units={'X'}, unit_type='fluid')
        self.assertEqual(1, len(result))
        self.assertEqual({'value': '1', 'unit': 'X'}, result[0])

    def test_cell_with_multiple_value_unit_without_space(self):
        result = self.parser.process_values_unit('1X,2X,3X', units=['X'], unit_type='fluid')
        self.assertEqual(3, len(result))
        self.assertEqual({'value': '1', 'unit': 'X'}, result[0])
        self.assertEqual({'value': '2', 'unit': 'X'}, result[1])
        self.assertEqual({'value': '3', 'unit': 'X'}, result[2])

    def test_cell_with_unspecified_unit(self):
        with self.assertRaises(TableException):
            _ = self.parser.process_values_unit('1, 2, 3 foo', units=['X'], unit_type='fluid')

    def test_cell_with_nonvalues(self):
        with self.assertRaises(TableException):
            _ = self.parser.process_values_unit('one, two X', units=['X'], unit_type='fluid')

    def test_cell_not_type_value_unit(self):
        with self.assertRaises(TableException):
            _ = self.parser.process_values_unit('A simple string', units=['celsius', 'fahrenheit'], unit_type='temperature')

    def test_cell_with_incorrect_unit_location(self):
        with self.assertRaises(TableException):
            _ = self.parser.process_values_unit('1 X, 2, 3', units=['X'], unit_type='fluid')

    def test_cell_with_incorrect_unit_value_swapped(self):
        with self.assertRaises(TableException):
            _ = self.parser.process_values_unit('1, 2, X 3', units=['X'], unit_type='fluid')

    def test_cell_values_with_name_containing_underscore_numbers(self):
        cell_str = 'AND_00, NAND_00'
        expected_values = ['AND_00', 'NAND_00']
        self.assertListEqual(expected_values, self.parser.extract_name_value(cell_str))

    def test_cell_values_with_long_name(self):
        cell_str = 'B_subtilis_WT_JH642_Colony_1, B_subtilis_WT_JH642_Colony_2, B_subtilis_WT_JH642_Colony_3'
        expected_values = ['B_subtilis_WT_JH642_Colony_1',
                           'B_subtilis_WT_JH642_Colony_2',
                           'B_subtilis_WT_JH642_Colony_3']
        self.assertListEqual(expected_values, self.parser.extract_name_value(cell_str))
    
    def test_is_table_caption(self):
        self.assertFalse(self.parser.is_table_caption('foo 1: a table caption'))
        self.assertTrue(self.parser.is_table_caption('table 1:'))
        self.assertTrue(self.parser.is_table_caption('Table1'))
        self.assertTrue(self.parser.is_table_caption('Table 1: a table caption'))
        self.assertTrue(self.parser.is_table_caption('Table1:Controls'))

    def test_parsing_number(self):
        self.assertEqual(['7'], self.parser.process_numbers('7'))
        self.assertEqual(['7'], self.parser.process_numbers(' 7 '))

    def test_boolean_values(self):
        self.assertTrue(self.parser.process_boolean_flag('true'))
        self.assertTrue(self.parser.process_boolean_flag('True'))
        self.assertFalse(self.parser.process_boolean_flag('False'))
        self.assertFalse(self.parser.process_boolean_flag('False'))
        self.assertEqual(self.parser.process_boolean_flag('neither'), None)

    def test_lab_name(self):
        self.assertEqual('foo', self.parser.process_lab_name('Lab: foo'))

    def test_lab_experiment_id(self):
        cell_text = 'Experiment_id: foo'
        self.assertTrue(self.parser.has_lab_table_keyword(cell_text, 'experiment_id'))
        self.assertEqual('foo', self.parser.process_lab_table_value(cell_text))

    def test_text_with_underscore(self):
        cell_text = 'xplan_request_submitted'
        self.assertTrue(self.parser.is_name(cell_text))
        names = [name for name, _ in self.parser.process_names_with_uri(cell_text)]
        self.assertEqual(len(names), 1)
        self.assertEqual(names[0], 'xplan_request_submitted')

    def test_text_with_url(self):
        cell_text = 'agave://data-sd2e-community/uploads/transcriptic/202006/r1egb6rhggaqwt/samples.json'
        self.assertTrue(self.parser.is_name(cell_text))
        names = [name for name, _ in self.parser.process_names_with_uri(cell_text)]
        self.assertEqual(len(names), 1)
        self.assertEqual(names[0], cell_text)

    def test_text_with_dash(self):
        cell_text = 'P---'
        self.assertTrue(self.parser.is_name(cell_text))
        names = [name for name, _ in self.parser.process_names_with_uri(cell_text)]
        self.assertEqual(len(names), 1)
        self.assertEqual(names[0], cell_text)

    def test_datetime(self):
        self.assertEqual(self.parser.process_datetime_format('2020/06/04 18:52:47'), datetime.datetime(2020, 6, 4, 18, 52, 47))
        self.assertEqual(self.parser.process_datetime_format('2020/6/4 18:52:47'), datetime.datetime(2020, 6, 4, 18, 52, 47))

    def test_invalid_datetime_format(self):
        with self.assertRaises(ValueError):
            self.assertEqual(self.parser.process_datetime_format('20/6/4 18:52:47'))

    def test_processing_table_caption_index(self):
        self.assertEqual(1, self.parser.process_table_caption_index('Table 1'))
        self.assertEqual(123, self.parser.process_table_caption_index('Table123'))
        self.assertEqual(123, self.parser.process_table_caption_index('Table123:'))

    def test_cell_with_newline(self):
        self.assertEqual(['AND_00', 'AND_01', 'AND_10'], [value for value, _ in self.parser.process_names_with_uri('AND_00, \n\nAND_01,\n AND_10\n')])
        self.assertEqual(['AND_00', 'AND_01'], [value for value, _ in self.parser.process_names_with_uri('AND_00 \n \n \n ,AND_01')])
        self.assertEqual(['AND_00', 'AND_01'], [value for value, _ in self.parser.process_names_with_uri('AND_0\n0,AND_01')])
        self.assertEqual(['1', '10', '15'], self.parser.process_numbers('1, 1\n0, 15'))

    def test_cell_without_delimiter(self):
        self.assertFalse(self.parser.is_number('1 2 3'))
        with self.assertRaises(TableException):
            self.parser.process_numbers('1 2 3')





if __name__ == "__main__":
    unittest.main()
