from measurement_table import MeasurementTable
import json
import os
import table_utils
import unittest

input_table_def = {
    "rows": 5,
    "columns": 9,
    "tableRows": [
      {
        "tableCells": [
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "IPTG",
                        "textStyle": {
                          "bold": True
                        }
                      }
                    },
                    {
                      "textRun": {
                        "content": "\n"
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "Kanamycin Sulfate",
                        "textStyle": {
                          "bold": True
                        }
                      }
                    },
                    {
                      "textRun": {
                        "content": "\n"
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "L-arabinose",
                        "textStyle": {
                          "link": {
                            "url": "https://hub.sd2e.org/user/sd2e/design/Larabinose/1"
                          }
                        }
                      }
                    },
                    {
                      "textRun": {
                        "content": "\n"
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "measurement-type\n"
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "file-type"
                      }
                    },
                    {
                      "textRun": {
                        "content": "\n"
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "replicate\n"
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "strains\n"
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "timepoint\n"
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "samples\n"
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
        "tableCells": [
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "0.0 mM,7e-5 mM\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "0.0019 mM\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "0 mM, 0.0125 mM\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "FLOW\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "FCS\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "4\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "MG1655, MG1655_LPV3,MG1655_RPU_Standard\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "5.0 hour, 18 hour\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "1088\n",
                        "textStyle": {}
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
        "tableCells": [
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "0 mM,7e-5 mM\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "0 mM, 0.0125 mM\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "RNA_SEQ\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              },
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "FASTQ, FASTQ\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "4\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "MG1655, MG1655_LPV3\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "5.0 hour, 18 hour\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "1056\n",
                        "textStyle": {}
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
        "tableCells": [
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "0 mM,7e-5 mM\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "4.98e-8 mM\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "0 mM, 0.0125 mM\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "RNA_SEQ\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "FASTQ, FASTQ\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "4\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "MG1655_RPU_Standard\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "5.0 hour, 18 hour\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "64\n",
                        "textStyle": {}
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
        "tableCells": [
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "0 mM,7e-5 mM\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "4.98e-8 mM\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "0 mM, 0.0125 mM\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "PLATE_READER\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "PLAIN,CSV\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "4\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "MG1655, MG1655_LPV3\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "5.0 hour, 18 hour\n",
                        "textStyle": {}
                      }
                    }
                  ]
                }
              }
            ]
          },
          {
            "content": [
              {
                "paragraph": {
                  "elements": [
                    {
                      "textRun": {
                        "content": "2112\n",
                        "textStyle": {}
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
    """
       Class to test measurement table
    """
    
#     def setUp(self):
#         curr_path = os.path.dirname(os.path.realpath(__file__))
#         data_dir = os.path.join(curr_path, '../tests/data')
#         with open(os.path.join(data_dir, 'test_tables.json'), 'r') as file:
#             self.input_tables = json.load(file)
#         
#         self.collected_meas_table = []
#         self.table_ids = []
#         for table_indx in range(len(self.input_tables)):
#             table = self.input_tables[table_indx]
#             if table_utils.detect_new_measurement_table(table):
#                 self.collected_meas_table.append(table)
                
    def test_measurement_table_with_measurement_type(self):
        input_table = {"tableRows": [
            {"tableCells": [{"content": [{"paragraph": {"elements": [{"textRun": {
                "content": "measurement-type\n" }}]}}]}]},
            {"tableCells": [{"content": [{"paragraph": {"elements": [{"textRun": {
                "content": "FLOW\n"}}]}}]}]}]
        } 
    
        meas_table = MeasurementTable(measurement_types={'PLATE_READER', 'FLOW'})
        actual_result = meas_table.parse_table(input_table)
        self.assertEquals(1, len(actual_result))
        self.assertEquals(actual_result[0]['measurement_type'], 'FLOW')

        
        
    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()