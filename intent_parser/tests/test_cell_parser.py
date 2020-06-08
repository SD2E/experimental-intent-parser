from intent_parser.table.cell_parser import CellParser
from intent_parser.table.intent_parser_cell import IntentParserCell
import unittest

class CellParserTest(unittest.TestCase):

    def setUp(self):
        self.parser = CellParser()

    def tearDown(self):
        pass
    
    def test_parse_content_item_with_name(self):
        cell = IntentParserCell()
        cell.add_paragraph('name')
        result = self.parser.parse_content_item(cell)
        name = result['name']
        self.assertEqual(2, len(name))
        self.assertEqual('name', name['label'])
        self.assertEqual('NO PROGRAM DICTIONARY ENTRY', name['sbh_uri'])
        
    def test_parse_content_item_with_name_value_unit(self):
        cell = IntentParserCell()
        cell.add_paragraph('name1 123 unit')
        result = self.parser.parse_content_item(cell, timepoint_units={'unit', 'timeunit'})
        name = result['name']
        self.assertEqual(2, len(name))
        self.assertEqual('name1', name['label'])
        self.assertEqual('NO PROGRAM DICTIONARY ENTRY', name['sbh_uri'])
        self.assertEqual('123', result['value'])
        self.assertEqual('unit', result['unit'])
        
    def test_parse_content_item_with_name_value_unit_timepoint(self):
        cell = IntentParserCell()
        cell.add_paragraph('name1 name2 123 unit @ 15 timeunit')
        result = self.parser.parse_content_item(cell, timepoint_units={'unit', 'timeunit'})
        name = result['name']
        timepoints = result['timepoints']
        self.assertEqual(2, len(name))
        self.assertEquals(1, len(timepoints))
        self.assertEqual('name1 name2', name['label'])
        self.assertEqual('NO PROGRAM DICTIONARY ENTRY', name['sbh_uri'])
        self.assertEqual('123', result['value'])
        self.assertEqual('unit', result['unit'])
        self.assertEqual(15.0, timepoints[0]['value'])
        self.assertEqual('timeunit', timepoints[0]['unit'])

    def test_names_without_separators(self):
        cell = IntentParserCell()
        cell.add_paragraph('foo')
        self.assertTrue(self.parser.is_name(cell))
        
    def test_names_with_separators(self):
        cell = IntentParserCell()
        cell.add_paragraph('one, two X')
        self.assertTrue(self.parser.is_name(cell))
        
    def test_names_from_numerical_values(self):
        cell = IntentParserCell()
        cell.add_paragraph('1, 2')
        self.assertFalse(self.parser.is_name(cell))
        
    def test_numbers(self):
        cell = IntentParserCell()
        cell.add_paragraph('1, 2')
        self.assertTrue(self.parser.is_number(cell))
    
    def test_number(self):
        cell = IntentParserCell()
        cell.add_paragraph('12')
        self.assertTrue(self.parser.is_number(cell))
            
    def test_numbers_with_unit(self):
        cell = IntentParserCell()
        cell.add_paragraph('12, 24 X')
        self.assertFalse(self.parser.is_number(cell))
        
    def test_is_value(self):
        cell = IntentParserCell()
        cell.add_paragraph('1 X')
        self.assertTrue(self.parser.is_valued_cell(cell))
        
    def test_is_value_with_pairing_units(self):
        cell = IntentParserCell()
        cell.add_paragraph('1 X, 2 unit, 3 mm')
        self.assertTrue(self.parser.is_valued_cell(cell))
        
    def test_is_value_with_ending_unit(self):
        cell = IntentParserCell()
        cell.add_paragraph('1, 2, 3 X')
        self.assertTrue(self.parser.is_valued_cell(cell))
    
    def test_is_value_with_starting_unit(self):
        cell = IntentParserCell()
        cell.add_paragraph('1 X, 2, 3')
        self.assertFalse(self.parser.is_valued_cell(cell))
        
    def test_value_unit(self):
        cell = IntentParserCell()
        cell.add_paragraph('3 hour')
        result = self.parser.process_values_unit(cell, units={'hour'}, unit_type='timepoints')
        self.assertEqual(1, len(result))
        self.assertEqual({'value': 3.0, 'unit': 'hour'}, result[0])
        
    def test_leading_values_unit(self):
        cell = IntentParserCell()
        cell.add_paragraph('1, 2,3 hour')
        result = self.parser.process_values_unit(cell, units={'hour'}, unit_type='timepoints')
        self.assertEqual(3, len(result))
        self.assertEqual({'value': 1.0, 'unit': 'hour'}, result[0])   
        self.assertEqual({'value': 2.0, 'unit': 'hour'}, result[1])   
        self.assertEqual({'value': 3.0, 'unit': 'hour'}, result[2])   
        
    def test_value_unit_pairs(self):
        cell = IntentParserCell()
        cell.add_paragraph('1 X, 2 mM ,3 micromole')
        result = self.parser.process_values_unit(cell, units={'X', 'mM', 'micromole'}, unit_type='fluid')
        self.assertEqual(3, len(result))
        self.assertEqual({'value': 1.0, 'unit': 'X'}, result[0])   
        self.assertEqual({'value': 2.0, 'unit': 'mM'}, result[1])   
        self.assertEqual({'value': 3.0, 'unit': 'micromole'}, result[2])  
        
if __name__ == "__main__":
    unittest.main()