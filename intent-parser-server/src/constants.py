"""
List of constants used for intent parser server
"""

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

# How many results we allow
SPARQL_LIMIT = 5

GROWTH_CURVE_PROTOCOL = 'GrowthCurve'
TIME_SERIES_HTP_PROTOCOL = 'TimeSeriesHTP'
OBSTACLE_COURSE_PROTOCOL = 'ObstacleCourse'

PROTOCOL_NAMES = {GROWTH_CURVE_PROTOCOL: 'Growth Curves', 
                  TIME_SERIES_HTP_PROTOCOL: 'Time Series', 
                  OBSTACLE_COURSE_PROTOCOL: 'Obstacle Course'}

# String defines for headers in measurements table
COL_HEADER_FILE_TYPE = 'file-type'
COL_HEADER_MEASUREMENT_TYPE = 'measurement-type'
COL_HEADER_NOTES = 'notes'
COL_HEADER_ODS = 'ods'
COL_HEADER_REPLICATE = 'replicate'
COL_HEADER_SAMPLES = 'samples'
COL_HEADER_STRAIN = 'strains'
COL_HEADER_TEMPERATURE = 'temperature'
COL_HEADER_TIMEPOINT = 'timepoint'

COL_HEADER_PARAMETER = 'Parameter'
COL_HEADER_PARAMETER_VALUE = 'Value'

PARAMETER_EXP_INFO_MEDIA_WELL_STRINGS = 'exp_info.media_well_strings'
PARAMETER_INDUCTION_INFO_REAGENTS_INDUCER = 'induction_info.induction_reagents.inducer'
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

