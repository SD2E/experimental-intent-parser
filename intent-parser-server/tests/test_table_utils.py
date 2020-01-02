import unittest
import table_utils as tu

class TableUtilsTest(unittest.TestCase):
    """Unit test for table_utils class"""

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
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
           self.assertEqual(unit, 'unspecified')
           self.assertTrue(value in expected_values) 

    def test_cell_with_unit_abbreviation(self):
        cell_str = '1, 2, 3 fold'
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
           self.assertEqual(unit, 'X')
           self.assertTrue(value in expected_values)
    
    def test_cell_with_unspecified_unit(self):
        cell_str = '1, 2, 3 foo'
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
           self.assertEqual(unit, 'unspecified')
           self.assertTrue(value in expected_values)  
    
    def test_cell_with_incorrect_unit_location(self):
        cell_str = '1 X, 2, 3'
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
           self.assertEqual(unit, 'unspecified')
           self.assertTrue(value in expected_values)  
    
    def test_cell_with_incorrect_unit_location2(self):
        cell_str = '1, 2, X 3'
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
           self.assertEqual(unit, 'unspecified')
           self.assertTrue(value in expected_values)   
    
    def test_cell_with_single_value(self):
        cell_str = '1 X'
        expected_values = ['1']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
           self.assertEqual(unit, 'X')
           self.assertTrue(value in expected_values)       

    def test_cell_with_nonvalues(self):
        cell_str = 'one, two X'
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
            self.assertEqual(unit, 'unspecified')
            self.assertTrue(value == cell_str)

    def test_cell_not_type_value_unit(self):
        cell_str = 'A simple string'
        for value, unit in tu.transform_cell(cell_str, ['celsius', 'fahrenheit'], cell_type='temperature'):
            self.assertEqual(unit, 'unspecified')
            self.assertTrue(value == cell_str)
    
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
    
       
if __name__ == "__main__":
    unittest.main()