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
            
                    
if __name__ == "__main__":
    unittest.main()