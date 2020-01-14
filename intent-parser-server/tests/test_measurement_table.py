from measurement_table import MeasurementTable
import json
import os
import table_utils
import unittest

input_table_def = {
    'rows': 5,
    'columns': 9,
    'tableRows': [
      {
        'tableCells': [
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'IPTG',
                        'textStyle': {
                          'bold': True
                        }
                      }
                    },
                    {
                      'textRun': {
                        'content': '\n'
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'Kanamycin Sulfate',
                        'textStyle': {
                          'bold': True
                        }
                      }
                    },
                    {
                      'textRun': {
                        'content': '\n'
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'L-arabinose',
                        'textStyle': {
                          'link': {
                            'url': 'https://hub.sd2e.org/user/sd2e/design/Larabinose/1'
                          }
                        }
                      }
                    },
                    {
                      'textRun': {
                        'content': '\n'
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'measurement-type\n'
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'file-type'
                      }
                    },
                    {
                      'textRun': {
                        'content': '\n'
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'replicate\n'
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'strains\n'
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'timepoint\n'
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'samples\n'
                      }
                    }
                  ]
                }
              }
            ]
          }
        ]
      },
      {
        'tableCells': [
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '0.0 mM,7e-5 mM\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '0.0019 mM\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '0 mM, 0.0125 mM\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'FLOW\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'FCS\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '4\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'MG1655, MG1655_LPV3,MG1655_RPU_Standard\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '5.0 hour, 18 hour\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '1088\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          }
        ]
      },
      {
        'tableCells': [
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '0 mM,7e-5 mM\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '0 mM, 0.0125 mM\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'RNA_SEQ\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              },
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'FASTQ, FASTQ\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '4\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'MG1655, MG1655_LPV3\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '5.0 hour, 18 hour\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '1056\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          }
        ]
      },
      {
        'tableCells': [
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '0 mM,7e-5 mM\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '4.98e-8 mM\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '0 mM, 0.0125 mM\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'RNA_SEQ\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'FASTQ, FASTQ\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '4\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'MG1655_RPU_Standard\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '5.0 hour, 18 hour\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '64\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          }
        ]
      },
      {
        'tableCells': [
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '0 mM,7e-5 mM\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '4.98e-8 mM\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '0 mM, 0.0125 mM\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'PLATE_READER\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'PLAIN,CSV\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '4\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': 'MG1655, MG1655_LPV3\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '5.0 hour, 18 hour\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            'content': [
              {
                'paragraph': {
                  'elements': [
                    {
                      'textRun': {
                        'content': '2112\n',
                        'textStyle': {}
                      }
                    }
                  ]
                }
              }
            ]
          }
        ]
      }
    ]
  } 

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
        actual_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(actual_result))
        self.assertEquals(actual_result[0]['measurement_type'], 'FLOW')

    def test_table_with_empty_file_type(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'file-type\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable()
        actual_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(actual_result))
        self.assertTrue(not actual_result[0])
    
    def test_table_with_file_type(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'file-type\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'FASTQ\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable()
        actual_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(actual_result))
        self.assertEquals(1, len(actual_result[0]['file_type']))
        self.assertEquals(actual_result[0]['file_type'][0], 'FASTQ')  
    
    def test_table_with_1_replicate(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'replicate\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': '3\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable()
        actual_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(actual_result))
        self.assertEquals(actual_result[0]['replicates'], 3)  
    
    def test_table_with_1_strain(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'strains\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'AND_00\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable()
        actual_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(actual_result))
        self.assertEqual(1, len(actual_result[0]['strains']))
        self.assertEqual('AND_00', actual_result[0]['strains'][0]) 
        
        
    def test_table_with_3_strains(self):
        input_table = {'tableRows': [
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'strains\n' }}]}}]}]},
            {'tableCells': [{'content': [{'paragraph': {'elements': [{'textRun': {
                'content': 'MG1655, MG1655_LPV3,MG1655_RPU_Standard\n'}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable()
        actual_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(actual_result))
        
        exp_res = ['MG1655', 'MG1655_LPV3','MG1655_RPU_Standard']
        self.assertListEqual(exp_res, actual_result[0]['strains'])
    
    
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
        
 
        
    
    
               
if __name__ == '__main__':
    unittest.main()