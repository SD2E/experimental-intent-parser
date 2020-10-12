from enum import Enum

"""
List of constants used for reading and writing contents from intent parser 
"""

RELEASE_VERSION = '2.9'

LAB_IDS_LIST = sorted(['BioFAB UID',
                            'Ginkgo UID',
                            'Transcriptic UID',
                            'LBNL UID',
                            'EmeraldCloud UID',
                            'CalTech UID',
                            'PennState (Salis) UID'])

ITEM_TYPES = {
            'component': {
                'Bead'     : 'http://purl.obolibrary.org/obo/NCIT_C70671',
                'CHEBI'    : 'http://identifiers.org/chebi/CHEBI:24431',
                'DNA'      : 'http://www.biopax.org/release/biopax-level3.owl#DnaRegion',
                'Protein'  : 'http://www.biopax.org/release/biopax-level3.owl#Protein',
                'RNA'      : 'http://www.biopax.org/release/biopax-level3.owl#RnaRegion'
            },
            'module': {
                'Strain'   : 'http://purl.obolibrary.org/obo/NCIT_C14419',
                'Media'    : 'http://purl.obolibrary.org/obo/NCIT_C85504',
                'Stain'    : 'http://purl.obolibrary.org/obo/NCIT_C841',
                'Buffer'   : 'http://purl.obolibrary.org/obo/NCIT_C70815',
                'Solution' : 'http://purl.obolibrary.org/obo/NCIT_C70830'
            },
            'collection': {
                'Challenge Problem' : '',
                'Collection' : ''
            },
            'external': {
                'Attribute' : ''
            }
        }

SPARQL_LIMIT = 5

GOOGLE_DRIVE_EXPERIMENT_REQUEST_FOLDER = '1FYOFBaUDIS-lBn0fr76pFFLBbMeD25b3'
GOOGLE_DOC_URL_PREFIX = 'https://docs.google.com/document/d/'
GOOGLE_DOC_MIMETYPE = 'application/vnd.google-apps.document'
WORD_DOC_MIMETYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

# Stateos Protocols Supported in IP
GROWTH_CURVE_PROTOCOL = 'GrowthCurve'
OBSTACLE_COURSE_PROTOCOL = 'ObstacleCourse'
TIME_SERIES_HTP_PROTOCOL = 'TimeSeriesHTP'
CELL_FREE_RIBO_SWITCH_PROTOCOL = 'CellFreeRiboswitches'

# Mapping protocols to human readible names
PARAMETER_PROTOCOL = 'protocol'
PROTOCOL_NAMES = {'PLACEHOLDER': 'Select a protocol',
                  GROWTH_CURVE_PROTOCOL: 'Growth Curves',
                  OBSTACLE_COURSE_PROTOCOL: 'Obstacle Course',
                  TIME_SERIES_HTP_PROTOCOL: 'Time Series',
                  CELL_FREE_RIBO_SWITCH_PROTOCOL: 'Cell Free Ribo Switch'}

DEFAULT_PARAMETERS = 'default_parameters'
PARAMETER_EXPERIMENT_REFERENCE_URL_FOR_XPLAN = 'experiment_reference_url_for_xplan'
PARAMETER_TEST_MODE = 'test_mode'
PARAMETER_SUBMIT = 'submit'
PARAMETER_BASE_DIR = 'xplan_base_dir'
PARAMETER_XPLAN_REACTOR = 'xplan_reactor'
PARAMETER_PLATE_SIZE = 'plate_size'
PARAMETER_PLATE_NUMBER = 'plate_number'
PARAMETER_CONTAINER_SEARCH_STRING = 'container_search_string'
PARAMETER_STRAIN_PROPERTY = 'strain_property'
PARAMETER_XPLAN_PATH = 'xplan_path'
PARAMETER_PROTOCOL_ID = 'protocol_id'

PARAMETER_EXP_INFO_MEDIA_WELL_STRINGS = 'exp_info.media_well_strings'
PARAMETER_INDUCTION_INFO_REAGENTS = 'induction_info.induction_reagents'
PARAMETER_INDUCTION_INFO_REAGENTS_INDUCER = 'induction_info.induction_reagents.inducer'
PARAMETER_INDUCTION_INFO_SAMPLING_INFO = 'induction_info.sampling_info'
PARAMETER_MEASUREMENT_INFO_36_HR_READ = 'measurement_info.36_hr_read'
PARAMETER_MEASUREMENT_INFO_FLOW_INFO = 'measurement_info.flow_info'
PARAMETER_MEASUREMENT_INFO_PLATE_READER_INFO = 'measurement_info.plate_reader_info'
PARAMETER_PLATE_READER_INFO_GAIN = 'plate_reader_info.gain'
PARAMETER_REAGENT_INFO_INDUCER_INFO = 'reagent_info.inducer_info'
PARAMETER_REAGENT_INFO_KILL_SWITCH = 'reagent_info.kill_switch'
PARAMETER_RECOVERY_INFO = 'recovery_info'
PARAMETER_RUN_INFO_ONLY_ENDPOINT_FLOW = 'run_info.only_endpoint_flow'
PARAMETER_RUN_INFO_READ_EACH_RECOVER = 'run_info.read_each_recovery'
PARAMETER_RUN_INFO_READ_EACH_INDUCTION = 'run_info.read_each_induction'
PARAMETER_RUN_INFO_SAVE_FOR_RNASEQ = 'run_info.save_for_rnaseq'
PARAMETER_RUN_INFO_SKIP_FIRST_FLOW = 'run_info.skip_first_flow'
PARAMETER_VALIDATE_SAMPLES = 'validate_samples'
PARAMETER_RUN_INFO_INCUBATE_IN_READER = 'run_info.incubate_in_reader'
PARAMETER_INDUCERS = 'inducers'

SD2_SPREADSHEET_ID = '1oLJTTydL_5YPyk-wY-dspjIw_bPZ3oCiWiK0xtG8t3g' # Sd2 Program dict
TEST_SPREADSHEET_ID = '1wHX8etUZFMrvmsjvdhAGEVU1lYgjbuRX5mmYlKv7kdk' # Intent parser test dict
UNIT_TEST_SPREADSHEET_ID = '1r3CIyv75vV7A7ghkB0od-TM_16qSYd-byAbQ1DhRgB0' #sd2 unit test dictionary 

# Table headers
HEADER_BATCH_VALUE = 'batch'
HEADER_CHANNEL_VALUE = 'Channel'
HEADER_COLUMN_ID_VALUE = 'Column_id'
HEADER_CONTENTS_VALUE = 'Contents'
HEADER_CONTROL_VALUE = 'control'
HEADER_CONTROL_TYPE_VALUE = 'Control Type'
HEADER_EXPERIMENT_ID_VALUE = 'Experiment_id'
HEADER_EXPERIMENT_STATUS_VALUE = 'Experiment Status'
HEADER_FILE_TYPE_VALUE = 'file-type'
HEADER_LAB_VALUE = 'Lab'
HEADER_LAB_ID_VALUE = 'Lab_id'
HEADER_LAST_UPDATED_VALUE = 'Last Update'
HEADER_MEASUREMENT_TYPE_VALUE = 'measurement-type'
HEADER_NOTES_VALUE = 'notes'
HEADER_ODS_VALUE = 'ods'
HEADER_PARAMETER_VALUE = 'Parameter'
HEADER_PARAMETER_VALUE_VALUE = 'Value'
HEADER_PIPELINE_STATUS_VALUE = 'Pipeline Status'
HEADER_PATH_VALUE = 'Output From Pipeline'
HEADER_ROW_ID_VALUE = 'Row_id'
HEADER_REPLICATE_VALUE = 'replicate'
HEADER_SAMPLES_VALUE = 'samples'
HEADER_STATE_VALUE = 'Processed'
HEADER_STRAINS_VALUE = 'Strains'
HEADER_TEMPERATURE_VALUE = 'temperature'
HEADER_TIMEPOINT_VALUE = 'Timepoint'

# Table header types
HEADER_BATCH_TYPE = 'BATCH'
HEADER_CHANNEL_TYPE = 'CHANNEL'
HEADER_COLUMN_ID_TYPE = 'COLUMN_ID'
HEADER_CONTENTS_TYPE = 'CONTENTS'
HEADER_CONTROL_TYPE = 'CONTROL'
HEADER_CONTROL_TYPE_TYPE = 'CONTROL_TYPE'
HEADER_EXPERIMENT_ID_TYPE = 'EXPERIMENT_ID'
HEADER_EXPERIMENT_STATUS_TYPE = 'EXPERIMENT_STATUS'
HEADER_FILE_TYPE_TYPE = 'FILE_TYPE'
HEADER_LAST_UPDATED_TYPE = 'LAST_UPDATED'
HEADER_MEASUREMENT_LAB_ID_TYPE = 'MEASUREMENT_LAB_ID'
HEADER_MEASUREMENT_TYPE_TYPE = 'MEASUREMENT_TYPE'
HEADER_NOTES_TYPE = 'NOTES'
HEADER_ODS_TYPE = 'ODS'
HEADER_PARAMETER_TYPE = 'PARAMETER'
HEADER_PARAMETER_VALUE_TYPE = 'PARAMETER_VALUE'
HEADER_PATH_TYPE = 'PATH'
HEADER_PIPELINE_STATUS_TYPE = 'PIPELINE_STATUS'
HEADER_REPLICATE_TYPE = 'REPLICATE'
HEADER_ROW_ID_TYPE = 'ROW_ID'
HEADER_SAMPLES_TYPE = 'SAMPLES'
HEADER_SKIP_TYPE = 'SKIP'
HEADER_STRAINS_TYPE = 'STRAINS'
HEADER_STATE_TYPE = 'STATE'
HEADER_TEMPERATURE_TYPE = 'TEMPERATURE'
HEADER_TIMEPOINT_TYPE = 'TIMEPOINT'
HEADER_UNKNOWN_TYPE = 'UNKNOWN'

TACC_SERVER = 'TACC'
