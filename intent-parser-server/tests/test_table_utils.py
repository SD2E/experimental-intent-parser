import unittest
import table_utils as tu

class TableUtilsTest(unittest.TestCase):
    """Unit test for table_utils class"""

    def testCellWithPropagatedUnit(self):
        cell_str = '1 X, 2 X, 3 X'
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
           self.assertEqual(unit, 'X')
           self.assertTrue(value in expected_values) 
           
    def testCellWithoutPropagatedUnit(self):
        cell_str = '1, 2, 3 X'
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
           self.assertEqual(unit, 'X')
           self.assertTrue(value in expected_values) 

    def testCellWithoutProgatedUnit2(self):
        cell_str = '1 X, 2, 3'
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
           self.assertEqual(unit, 'unspecified')
           self.assertTrue(value in expected_values)  

    def testCellWithoutUnits(self):
        cell_str = '1, 2, 3'
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
           self.assertEqual(unit, 'unspecified')
           self.assertTrue(value in expected_values) 

    def testCellWithUnitAbbreviation(self):
        cell_str = '1, 2, 3 fold'
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
           self.assertEqual(unit, 'X')
           self.assertTrue(value in expected_values)
    
    def testCellWithUnspecifiedUnit(self):
        cell_str = '1, 2, 3 foo'
        expected_values = ['1', '2', '3']
        for value, unit in tu.transform_cell(cell_str, ['X'], cell_type='fluid'):
           self.assertEqual(unit, 'unspecified')
           self.assertTrue(value in expected_values)  
       
     
if __name__ == "__main__":
    unittest.main()