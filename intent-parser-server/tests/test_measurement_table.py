from measurement_table import MeasurementTable
import json
import os
import table_utils
import unittest


class MeasurementTableTest(unittest.TestCase):
    '''
       Class to test measurement table
    '''
                
    def test_table_with_measurement_type(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'measurement-type\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'FLOW\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable(measurement_types={'PLATE_READER', 'FLOW'})
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        self.assertEquals(meas_result[0]['measurement_type'], 'FLOW')

    def test_table_with_empty_file_type(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'file-type\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable()
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        self.assertTrue(not meas_result[0])
    
    def test_table_with_file_type(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'file-type\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'FASTQ\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable()
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        self.assertEquals(1, len(meas_result[0]['file_type']))
        self.assertEquals(meas_result[0]['file_type'][0], 'FASTQ')  
    
    def test_table_with_1_replicate(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'replicate\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '3\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable()
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        self.assertEquals(meas_result[0]['replicates'], 3)  
    
    def test_table_with_1_strain(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'strains\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'AND_00\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable()
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        self.assertEqual(1, len(meas_result[0]['strains']))
        self.assertEqual('AND_00', meas_result[0]['strains'][0]) 
        
        
    def test_table_with_3_strains(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'strains\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'MG1655, MG1655_LPV3,MG1655_RPU_Standard\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable()
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res = ['MG1655', 'MG1655_LPV3','MG1655_RPU_Standard']
        self.assertListEqual(exp_res, meas_result[0]['strains'])
    
    
    def test_table_with_1_timepoint(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'timepoint\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '3 hour\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable(timepoint_units={'hour'})
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'value': 3.0, 'unit': 'hour'}
        self.assertEquals(1, len(meas_result[0]['timepoints']))
        self.assertDictEqual(exp_res1, meas_result[0]['timepoints'][0])
                  
    def test_table_with_3_timepoint(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'timepoint\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '6, 12, 24 hour\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable(timepoint_units={'hour'})
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'value': 6.0, 'unit': 'hour'}
        exp_res2 = {'value': 12.0, 'unit': 'hour'}
        exp_res3 = {'value': 24.0, 'unit': 'hour'}
        self.assertEquals(3, len(meas_result[0]['timepoints']))
        for list in meas_result[0]['timepoints']:
            self.assertFalse(list != exp_res1 and list != exp_res2 and list != exp_res3)
    
    def test_table_with_1_temperature(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'temperature\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '1 fahrenheit\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable(temperature_units={'fahrenheit'})
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'value': 1.0, 'unit': 'fahrenheit'}
        self.assertEquals(1, len(meas_result[0]['temperatures']))
        self.assertDictEqual(exp_res1, meas_result[0]['temperatures'][0]) 
        
    def test_table_with_1_temperature_and_unspecified_unit(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'temperature\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '1 dummy\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable(temperature_units={'celsius', 'fahrenheit'})
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'value': 1.0, 'unit': 'unspecified'}
        self.assertEquals(1, len(meas_result[0]['temperatures']))
        self.assertDictEqual(exp_res1, meas_result[0]['temperatures'][0])  
    
    def test_table_with_2_temperature_and_unit_abbreviation(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'temperature\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '3, 2, 1 C\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable(temperature_units={'celsius'})
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'value': 3.0, 'unit': 'celsius'}
        exp_res2 = {'value': 2.0, 'unit': 'celsius'}
        exp_res3 = {'value': 1.0, 'unit': 'celsius'}
        self.assertEquals(3, len(meas_result[0]['temperatures']))
        for list in meas_result[0]['temperatures']:
            self.assertFalse(list != exp_res1 and list != exp_res2 and list != exp_res3)  
             
    def test_table_with_3_temperature(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'temperature\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '3, 2, 1 celsius\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable(temperature_units={'celsius'})
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'value': 3.0, 'unit': 'celsius'}
        exp_res2 = {'value': 2.0, 'unit': 'celsius'}
        exp_res3 = {'value': 1.0, 'unit': 'celsius'}
        self.assertEquals(3, len(meas_result[0]['temperatures']))
        for list in meas_result[0]['temperatures']:
            self.assertFalse(list != exp_res1 and list != exp_res2 and list != exp_res3)  
    
    def test_table_with_samples(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'samples\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '5, 10, 15\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable()
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        self.assertTrue(not meas_result[0])
    
    def test_table_with_notes(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'notes\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'A simple string\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable()
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        self.assertTrue(not meas_result[0])
    
    def test_table_with_1_ods(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'ods\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '3\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable()
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        self.assertEquals(1, len(meas_result[0]['ods']))
        self.assertListEqual([3.0], meas_result[0]['ods'])
        
    def test_table_with_3_ods(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'ods\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '33, 22, 11\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable()
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        self.assertEquals(3, len(meas_result[0]['ods']))
        self.assertListEqual([33.0, 22.0, 11.0], meas_result[0]['ods'])
        
    def test_table_with_one_value_reagent(self):
        reagent_name = 'L-arabinose'
        reagent_uri = 'https://hub.sd2e.org/user/sd2e/design/Larabinose/1'
        
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': reagent_name, 'textStyle': {'link': {'url': reagent_uri}
                        }}},
                {'textRun': {
                    'content': '\n'}}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '9 mM\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable(fluid_units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'})
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'name' : {'label' : reagent_name, 'sbh_uri' : reagent_uri}, 'value' : '9', 'unit' : 'mM'}
        self.assertEquals(1, len(meas_result[0]['contents'][0]))
        self.assertEquals(exp_res1, meas_result[0]['contents'][0][0])
            
    def test_table_with_three_value_reagent(self):
        reagent_name = 'L-arabinose'
        reagent_uri = 'https://hub.sd2e.org/user/sd2e/design/Larabinose/1'
        
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': reagent_name, 'textStyle': {'link': {'url': reagent_uri}
                        }}},
                {'textRun': {
                    'content': '\n'}}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '0, 1, 2 micromole\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable(fluid_units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'})
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'name' : {'label' : reagent_name, 'sbh_uri' : reagent_uri}, 'value' : '0', 'unit' : 'micromole'}
        exp_res2 = {'name' : {'label' : reagent_name, 'sbh_uri' : reagent_uri}, 'value' : '1', 'unit' : 'micromole'}
        exp_res3 = {'name' : {'label' : reagent_name, 'sbh_uri' : reagent_uri}, 'value' : '2', 'unit' : 'micromole'}
        self.assertEquals(3, len(meas_result[0]['contents'][0]))
        for act_res in meas_result[0]['contents'][0]:
            self.assertFalse(act_res != exp_res1 and act_res != exp_res2 and act_res != exp_res3)
            
    def test_table_with_reagent_and_unit_abbreviation(self):
        reagent_name = 'L-arabinose'
        reagent_uri = 'https://hub.sd2e.org/user/sd2e/design/Larabinose/1'
        
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': reagent_name, 'textStyle': {'link': {'url': reagent_uri}
                        }}},
                {'textRun': {
                    'content': '\n'}}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '1 fold\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable(fluid_units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'})
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'name' : {'label' : reagent_name, 'sbh_uri' : reagent_uri}, 'value' : '1', 'unit' : 'X'}
        self.assertEquals(1, len(meas_result[0]['contents'][0]))
        self.assertEquals(exp_res1, meas_result[0]['contents'][0][0])
    
    def test_table_with_reagent_and_percentage_unit(self):
        reagent_name = 'L-arabinose'
        reagent_uri = 'https://hub.sd2e.org/user/sd2e/design/Larabinose/1'
        
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': reagent_name, 'textStyle': {'link': {'url': reagent_uri}
                        }}},
                {'textRun': {
                    'content': '\n'}}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '11 %\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable(fluid_units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'})
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'name' : {'label' : reagent_name, 'sbh_uri' : reagent_uri}, 'value' : '11', 'unit' : '%'}
        self.assertEquals(1, len(meas_result[0]['contents'][0]))
        self.assertEquals(exp_res1, meas_result[0]['contents'][0][0])
        
    def test_table_with_reagent_and_unit_containing_backslash(self):
        reagent_name = 'L-arabinose'
        reagent_uri = 'https://hub.sd2e.org/user/sd2e/design/Larabinose/1'
        
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': reagent_name, 'textStyle': {'link': {'url': reagent_uri}}
                        }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '11 g/L\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable(fluid_units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'})
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'name' : {'label' : reagent_name, 'sbh_uri' : reagent_uri}, 'value' : '11', 'unit' : 'g/L'}
        self.assertEquals(1, len(meas_result[0]['contents'][0]))
        self.assertEquals(exp_res1, meas_result[0]['contents'][0][0])
        
    def test_table_with_reagent_and_timepoint(self):
        reagent_uri = 'https://hub.sd2e.org/user/sd2e/design/beta0x2Destradiol/1'
        
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'SC_Media @ 18 hour', 'textStyle': {'link': {'url': reagent_uri}}
                        }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '0 M\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable(timepoint_units={'hour'}, fluid_units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'})
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'name' : {'label' : 'SC_Media', 'sbh_uri' : reagent_uri}, 'value' : '0', 'unit' : 'M', 
                    'timepoint' : {'value' : 18.0, 'unit' : 'hour'}}
        self.assertEquals(1, len(meas_result[0]['contents'][0]))
        self.assertEquals(exp_res1, meas_result[0]['contents'][0][0])
       
    def test_table_with_media(self):
        media_uri = 'https://hub.sd2e.org/user/sd2e/design/Media/1'
        input_table ={'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Media','textStyle': {'link': {'url': media_uri}, 'bold': True}}},
                    {'textRun': {
                        'content': '\n'}}
                  ]}}]}]} ,
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'sc_media\n'}}]}}]}]}]
        } 
 
        meas_table = MeasurementTable()
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'name' : {'label' : 'Media', 'sbh_uri' : media_uri}, 'value' : 'sc_media'}
        self.assertEquals(1, len(meas_result[0]['contents'][0]))
        self.assertEquals(exp_res1, meas_result[0]['contents'][0][0])
     
    def test_table_with_media_containing_period_values(self):
        input_table ={'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'media','textStyle': {'bold': True}}},
                    {'textRun': {
                        'content': '\n'}}
                  ]}}]}]} ,
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Yeast_Extract_Peptone_Adenine_Dextrose (a.k.a. YPAD Media)\n'}}]}}]}]}]
        } 
 
        meas_table = MeasurementTable()
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'name' : {'label' : 'media', 'sbh_uri' : 'NO PROGRAM DICTIONARY ENTRY'}, 
                    'value' : 'Yeast_Extract_Peptone_Adenine_Dextrose (a.k.a. YPAD Media)'}
        self.assertEquals(1, len(meas_result[0]['contents'][0]))
        self.assertEquals(exp_res1, meas_result[0]['contents'][0][0])
        
    def test_table_with_media_containing_percentage_values(self):
        input_table ={'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'media','textStyle': {'bold': True}}},
                    {'textRun': {
                        'content': '\n'}}
                  ]}}]}]} ,
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'Synthetic_Complete_2%Glycerol_2%Ethanol\n'}}]}}]}]}]
        } 
 
        meas_table = MeasurementTable()
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'name' : {'label' : 'media', 'sbh_uri' : 'NO PROGRAM DICTIONARY ENTRY'}, 'value' : 'Synthetic_Complete_2%Glycerol_2%Ethanol'}
        self.assertEquals(1, len(meas_result[0]['contents'][0]))
        self.assertEquals(exp_res1, meas_result[0]['contents'][0][0])
    
    def test_table_with_media_containing_numerical_values(self):
        input_table ={'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'media','textStyle': {'bold': True}}},
                    {'textRun': {
                        'content': '\n'}}
                  ]}}]}]} ,
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'SC+Glucose+Adenine+0.8M\n'}}]}}]}]}]
        } 
 
        meas_table = MeasurementTable()
        meas_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {'name' : {'label' : 'media', 'sbh_uri' : 'NO PROGRAM DICTIONARY ENTRY'}, 'value' : 'SC+Glucose+Adenine+0.8M'}
        self.assertEquals(1, len(meas_result[0]['contents'][0]))
        self.assertEquals(exp_res1, meas_result[0]['contents'][0][0])
        
if __name__ == '__main__':
    unittest.main()