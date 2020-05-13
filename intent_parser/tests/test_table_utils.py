from intent_parser.intent_parser_exceptions import TableException
import intent_parser.table.table_utils as tu
import unittest

class TableUtilsTest(unittest.TestCase):
    """
    Test table utility methods
    """

    def test_cell_with_propagated_unit(self):
        cell_str = '1 X, 2 X, 3 X'
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
            self.assertEqual(unit, 'X')
            self.assertTrue(value in expected_values) 
           
    def test_cell_without_propagated_unit(self):
        cell_str = '1, 2, 3 X'
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
            self.assertEqual(unit, 'X')
            self.assertTrue(value in expected_values) 

    def test_cell_without_units(self):
        cell_str = '1, 2, 3'
        with self.assertRaises(TableException):
            _, _ = tu.transform_cell(cell_str, ['X'], cell_type='fluid')

    def test_cell_with_unit_abbreviation(self):
        cell_str = '1, 2, 3 fold'
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
            self.assertEqual(unit, 'X')
            self.assertTrue(value in expected_values)
    
    def test_cell_with_unspecified_unit(self):
        cell_str = '1, 2, 3 foo'
        with self.assertRaises(TableException):
            _, _ = tu.transform_cell(cell_str, ['X'], cell_type='fluid')
    
    def test_cell_with_incorrect_unit_location(self):
        cell_str = '1 X, 2, 3'
        with self.assertRaises(TableException):
            _, _ = tu.transform_cell(cell_str, ['X'], cell_type='fluid')
    
    def test_cell_with_incorrect_unit_value_swapped(self):
        cell_str = '1, 2, X 3'
        with self.assertRaises(TableException):
            _, _ = tu.transform_cell(cell_str, ['X'], cell_type='fluid')
    
    def test_cell_with_unit_without_spacing(self):
        cell_str = '1X'
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
            self.assertEqual(unit, 'X')
            self.assertEqual('1', value)
           
    def test_cell_with_multiple_value_unit_without_space(self):
        cell_str = '1X,2X,3X'
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
            self.assertEqual(unit, 'X')
            self.assertTrue(value in expected_values)
           
    def test_cell_with_single_value(self):
        cell_str = '1 X'
        expected_values = ['1']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
            self.assertEqual(unit, 'X')
            self.assertTrue(value in expected_values)       

    def test_cell_with_nonvalues(self):
        cell_str = 'one, two X'
        with self.assertRaises(TableException):
            _, _ = tu.transform_cell(cell_str, ['X'], cell_type='fluid')

    def test_cell_not_type_value_unit(self):
        cell_str = 'A simple string'
        with self.assertRaises(TableException):
            _, _ = tu.transform_cell(cell_str, ['celsius', 'fahrenheit'], cell_type='temperature')
                
    def test_cell_without_cell_type(self):
        cell_str = '1, 2 hour'
        expected_values = ['1', '2']
        for value, unit in tu.transform_cell(cell_str, ['hour']):
            self.assertEqual(unit, 'hour')
            self.assertTrue(value in expected_values) 
    
    def test_cell_values_with_numbers(self):
        cell_str = '1, 2'
        expected_values = ['1', '2']
        self.assertListEqual(expected_values, tu.extract_number_value(cell_str))
        
    def test_cell_values_with_name_containing_underscore_numbers(self):
        cell_str = 'AND_00, NAND_00'
        expected_values = ['AND_00', 'NAND_00']
        self.assertListEqual(expected_values, tu.extract_name_value(cell_str))
        
    def test_cell_values_with_long_name(self):
        cell_str = 'B_subtilis_WT_JH642_Colony_1, B_subtilis_WT_JH642_Colony_2, B_subtilis_WT_JH642_Colony_3'
        expected_values = ['B_subtilis_WT_JH642_Colony_1', 
                           'B_subtilis_WT_JH642_Colony_2', 
                           'B_subtilis_WT_JH642_Colony_3']
        self.assertListEqual(expected_values, tu.extract_name_value(cell_str)) 
         
    
    def test_cell_values_without_underscore(self):
        cell_str = 'CSV, FCS'
        expected_values = ['CSV', 'FCS']
        self.assertListEqual(expected_values, tu.extract_name_value(cell_str))
    
    def test_cell_values_with_one_name(self):
        cell_str = 'CSV'
        expected_values = ['CSV']
        self.assertListEqual(expected_values, tu.extract_name_value(cell_str))
    
    def test_cell_is_number(self):  
        self.assertTrue(tu.is_number('3'))
        
    def test_cell_list_is_number(self):
        self.assertTrue(tu.is_number('3, 5, 7'))
        
    def test_cell_is_number_with_unit(self):
        self.assertFalse(tu.is_number('3 X'))
    
    def test_cell_unit_is_not_number(self):
        self.assertFalse(tu.is_number('x'))
        
    def test_extract_number_value_with_unit(self):
        self.assertListEqual(['1', '2'], tu.extract_number_value('1, 2 X'))
        
    def test_cell_values_with_special_character(self):
        for value,unit in tu.transform_cell('8 %', ['%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L']):
            self.assertEqual('8', value)
            self.assertEqual('%', unit)
        
    def test_cell_values_with_backslash(self):
        for value,unit in tu.transform_cell('9 g/L', ['%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L']):
            self.assertEqual('9', value)
            self.assertEqual('g/L', unit)
    
    def test_cell_values_with_exponent(self):
        self.assertTrue(tu.is_number('5e-06'))  
        self.assertTrue(tu.is_number('5e+06'))  
        self.assertTrue(tu.is_number('5e06'))  
        self.assertTrue(tu.is_number('2.05e7'))  
        self.assertFalse(tu.is_number('2.0e.07'))  
        self.assertFalse(tu.is_number('2.0e'))  
                             
    def test_cell_values_with_named_spacing(self):
        cell_str = 'Yeast_Extract_Peptone_Adenine_Dextrose (a.k.a. YPAD Media)'   
        for name in tu.extract_name_value(cell_str):
            self.assertEquals(cell_str, name)
    
    def test_cell_values_with_named_and_numerical_spacing(self):
        cell_str = 'B. subtilis 168 PmtlA-comKS'   
        for name in tu.extract_name_value(cell_str):
            self.assertEquals(cell_str, name)
    
    def test_cell_with_trailing_whitespace(self):
        cell_str = 'Yeast1_, Yeast2_, Yeast3_ '
        exp_res = ['Yeast1_', 'Yeast2_', 'Yeast3_']
        for name in tu.extract_name_value(cell_str):
            self.assertTrue(name in exp_res)

    def test_cell_with_strateos_number_unit(self):
        cell_str = '5 microliter'
        actual_res = tu.transform_strateos_string(cell_str)   
        self.assertEquals(1, len(actual_res))
        self.assertEquals('5:microliter', actual_res[0])
        
    def test_cell_with_strateos_name(self):
        cell_str = 'sc_media'
        actual_res = tu.transform_strateos_string(cell_str)   
        self.assertEquals(1, len(actual_res))
        self.assertEquals('sc_media', actual_res[0])
    
    def test_cell_with_unit_containing_multiple_abbreviations(self):
        cell_str = '1 h, 2 hr, 3 hours'
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['hour'], cell_type='timepoints'):
            self.assertEqual(unit, 'hour')
            self.assertTrue(value in expected_values)
          
    def test_cell_with_unicode_characters(self):
        cell_str = '\x0bApp'
        self.assertTrue('App', tu.extract_name_value(cell_str))
        
    def test_cell_valued(self):
        self.assertFalse(tu.is_valued_cells('Modified M9 Media + Kan 5_ug_per_ml')) 
        self.assertTrue(tu.is_valued_cells('5X'))
        self.assertTrue(tu.is_valued_cells('1X,2X,3X'))
        
    def test_get_name_with_prefix(self):
        cell_str = 'lab: abc'
        lab_name = tu.extract_name_from_str(cell_str, 'lab:')
        self.assertEqual(lab_name, 'abc')
        
    def test_get_name_with_prefix_and_whitespace(self):
        cell_str = 'lab: abc defg'
        lab_name = tu.extract_name_from_str(cell_str, 'lab:')
        self.assertEqual(lab_name, 'abcdefg')
        
    def test_get_name_with_capitalize_prefix(self):
        cell_str = 'LAB: abc defg'
        lab_name = tu.extract_name_from_str(cell_str, 'lab:')
        self.assertEqual(lab_name, 'abcdefg')
    
    def test_get_name_with_underscore_prefix(self):
        cell_str = 'Experiment_Id: abc'
        lab_name = tu.extract_name_from_str(cell_str, 'experiment_id:')
        self.assertEqual(lab_name, 'abc')
    
    def test_get_name_with_numerical_values(self):
        cell_str = 'Experiment_Id: 123'
        lab_name = tu.extract_name_from_str(cell_str, 'experiment_id:')
        self.assertEqual(lab_name, '123')
        
    def test_get_name_without_name(self):
        cell_str = 'Experiment_Id: '
        lab_name = tu.extract_name_from_str(cell_str, 'experiment_id:')
        self.assertFalse(lab_name)
            
    def test_get_name_with_unkown_prefix(self):
        cell_str = 'unknown: @foo'
        with self.assertRaises(TableException):
            tu.extract_name_from_str(cell_str, 'experiment_id:')
        
if __name__ == "__main__":
    unittest.main()