"""
List of constants used for reading and writing contents from intent parser
"""

RELEASE_VERSION = '3.2'
# name of labs Intent Parser has connection to
LAB_TRANSCRIPTIC = 'Transcriptic'
LAB_DUKE_HASE = 'Duke_Haase'
AQUARIUM_NAMESPACE = 'http://aquarium.bio/'
STRATEOS_NAMESPACE = 'http://strateos.com/'

# keywords used for calling POST methods
ANALYZE_LINK = 'link'
ANALYZE_NEVER_LINK = 'process_never_link'
ANALYZE_NO = 'process_analyze_no'
ANALYZE_NO_TO_ALL = 'process_no_to_all'
ANALYZE_PROGRESS = 'progress'
ANALYZE_SEARCH_RESULTS = 'search_results'
ANALYZE_SEARCH_RESULT_INDEX = 'search_result_index'
ANALYZE_TERM = 'term'
ANALYZE_YES = 'process_analyze_yes'
ANALYZE_YES_TO_ALL = 'process_link_all'

SELECTED_CONTENT_TERM = 'content_term'
SELECTED_END_OFFSET = 'end_offset'
SELECTED_PARAGRAPH_INDEX = 'paragraph_index'
SELECTED_START_OFFSET = 'offset'

SPELLCHECK_ADD_IGNORE = 'spellcheck_add_ignore'
SPELLCHECK_ADD_IGNORE_ALL = 'spellcheck_add_ignore_all'
SPELLCHECK_ADD_DICTIONARY = 'spellcheck_add_dictionary'
SPELLCHECK_ADD_SYNBIOHUB = 'spellcheck_add_synbiohub'
SPELLCHECK_ENTERLINK = 'EnterLink'
SPELLCHECK_ADD_SELECT_PREVIOUS = 'spellcheck_add_select_previous'
SPELLCHECK_ADD_SELECT_NEXT = 'spellcheck_add_select_next'
SPELLCHECK_ADD_DROP_FIRST = 'spellcheck_add_drop_first'
SPELLCHECK_ADD_DROP_LAST = 'spellcheck_add_drop_last'

SUBMIT_FORM_LINK = 'link'
SUBMIT_FORM_LINK_ALL = 'linkAll'
SUBMIT_FORM = 'submit'
SUBMIT_FORM_CREATE_CONTROLS_TABLE = 'createControlsTable'
SUBMIT_FORM_CREATE_MEASUREMENT_TABLE = 'createMeasurementTable'
SUBMIT_FORM_CREATE_PARAMETER_TABLE = 'createParameterTable'

# Intent Parser's supporting unit types
UNIT_TYPE_FLUID = 'fluid'
UNIT_TYPE_TEMPERATURE = 'temperature'
UNIT_TYPE_TIMEPOINTS = 'timepoints'

UNIT_DAY = 'day'

# Mappings used for submitting terms to SynBioHub
LAB_IDS_LIST = ['BioFAB UID',
                'CalTech UID',
                'EmeraldCloud UID',
                'Ginkgo UID',
                'LBNL UID',
                'PennState (Salis) UID',
                'Transcriptic UID']

SBOL_COMPONENT_MAPPINGS = {
    'Bead': 'http://purl.obolibrary.org/obo/NCIT_C70671',
    'CHEBI': 'http://identifiers.org/chebi/CHEBI:24431',
    'DNA': 'http://www.biopax.org/release/biopax-level3.owl#DnaRegion',
    'Protein': 'http://www.biopax.org/release/biopax-level3.owl#Protein',
    'RNA': 'http://www.biopax.org/release/biopax-level3.owl#RnaRegion'
}

SBOL_MODULE_MAPPINGS = {
    'Strain': 'http://purl.obolibrary.org/obo/NCIT_C14419',
    'Media': 'http://purl.obolibrary.org/obo/NCIT_C85504',
    'Stain': 'http://purl.obolibrary.org/obo/NCIT_C841',
    'Buffer': 'http://purl.obolibrary.org/obo/NCIT_C70815',
    'Solution': 'http://purl.obolibrary.org/obo/NCIT_C70830'
}

SBOL_COLLECTION_MAPPING = {
    'Challenge Problem': '',
    'Collection': ''
}

SBOL_EXTERNAL_MAPPINGS = {
    'Attribute': ''
}

ITEM_TYPES = {
    'component': SBOL_COMPONENT_MAPPINGS,
    'module': SBOL_MODULE_MAPPINGS,
    'collection': SBOL_COLLECTION_MAPPING,
    'external': SBOL_EXTERNAL_MAPPINGS
}

SPARQL_LIMIT = 5
# sbol3 encodings
MEASUREMENT_TYPE_AUTOMATED_TEST = 'AUTOMATED_TEST'
MEASUREMENT_TYPE_CFU = 'CFU'
MEASUREMENT_TYPE_CONDITION_SPACE = 'CONDITION_SPACE'
MEASUREMENT_TYPE_FLOW = 'FLOW'
MEASUREMENT_TYPE_DNA_SEQ = 'DNA_SEQ'
MEASUREMENT_TYPE_EXPERIMENTAL_DESIGN = 'EXPERIMENTAL_DESIGN'
MEASUREMENT_TYPE_IMAGE = 'IMAGE'
MEASUREMENT_TYPE_PLATE_READER = 'PLATE_READER'
MEASUREMENT_TYPE_PROTEOMICS = 'PROTEOMICS'
MEASUREMENT_TYPE_RNA_SEQ = 'RNA_SEQ'
MEASUREMENT_TYPE_SEQUENCING_CHROMATOGRAM = 'SEQUENCING_CHROMATOGRAM'
MEASUREMENT_TYPE_FLUOESCENE_MICROSCOPY = 'FLUORESCENCE MICROSCOPY'

NCIT_INDUCER_NAME = 'Inducer'
NCIT_MEDIA_NAME = 'Growth Medium'
NCIT_REAGENT_NAME = 'Reagent'
NCIT_STRAIN_NAME = 'Organism Strain'

NCIT_ANTIBIOTIC_URI = 'https://identifiers.org/ncit:C258'
NCIT_CFU_URI = 'https://identifiers.org/ncit:C68742'
NCIT_DNA_SEQ_URI = 'https://identifiers.org/ncit:C153598'
NCIT_FLOW_URI = 'https://identifiers.org/ncit:C78806'
NCIT_FLUORESCENCE_MICROSCOPY = 'https://identifiers.org/NCIT:C16856'
NCIT_IMAGE_URI = 'https://identifiers.org/ncit:C16853'
NCIT_INDUCER_URI = 'https://identifiers.org/ncit:C120268'
NCIT_MEDIA_URI = 'https://identifiers.org/ncit:C85504'
NCIT_PLATE_READER_URI = 'https://identifiers.org/ncit:C70661'
NCIT_PROTEOMICS_URI = 'https://identifiers.org/ncit:C20085'
NCIT_REAGENT_URI = 'https://identifiers.org/ncit:C802'
NCIT_RNA_SEQ_URI = 'https://identifiers.org/ncit:C124261'
NCIT_SEQUENCING_CHROMATOGRAM_URI = 'https://identifiers.org/ncit:C63580'
NCIT_STRAIN_URI = 'https://identifiers.org/ncit:C14419'

NCIT_CELSIUS = 'https://identifiers.org/ncit:C42559'
NCIT_CONCENTRATION = 'https://identifiers.org/ncit:C41185'
NCIT_DAY = 'https://identifiers.org/ncit:C25301'
NCIT_CONCENTRATION_ENTITY_POOL = 'https://identifiers.org/SBO:0000196'
NCIT_FAHRENHEIT = 'https://identifiers.org/ncit:C44277'
NCIT_FOLD_CHANGE = 'https://identifiers.org/ncit:C60693'
NCIT_HOUR = 'https://identifiers.org/ncit:C25529'
NCIT_MICROGRAM_PER_MILLILITER = 'https://identifiers.org/ncit:C64572'
NCIT_MICROMOLE = 'https://identifiers.org/ncit:C48509'
NCIT_MICROSECOND = 'https://identifiers.org/ncit:C69149'
NCIT_MILLISECOND = 'https://identifiers.org/ncit:C41140'
NCIT_MINUTE = 'https://identifiers.org/ncit:C48154'
NCIT_MONTH = 'https://identifiers.org/ncit:C29846'
NCIT_NANOMOLE = 'https://identifiers.org/ncit:C48517'
NCIT_NANOSECOND = 'https://identifiers.org/ncit:C73767'
NCIT_NOT_APPLICABLE = 'https://identifiers.org/ncit:C48660'
NCIT_PICOSECOND = 'https://identifiers.org/ncit:C73768'
NCIT_SECOND = 'https://identifiers.org/ncit:C42535'
NCIT_WEEK = 'https://identifiers.org/ncit:C29844'
NCIT_YEAR = 'https://identifiers.org/ncit:C29848'

OTU_FEMTOSECOND = 'http://www.ontology-of-units-of-measure.org/resource/om-2/femtosecond-Time'
OTU_NANOMETER = 'http://www.ontology-of-units-of-measure.org/resource/om-2/nanometre'
OTU_HOUR = 'http://www.ontology-of-units-of-measure.org/resource/om-2/hour'
OTU_MICROLITRE = 'http://www.ontology-of-units-of-measure.org/resource/om-2/microlitre'

UO_MILLIGRAM_PER_MILLILITER = 'https://identifiers.org/UO:0000176'
UO_MOLAR = 'https://identifiers.org/UO:0000062'
UO_MILLI_MOLAR = 'https://identifiers.org/UO:0000063'
UO_GRAM_PER_LITER = 'https://identifiers.org/UO:0000175'
UO_NANO_GRAM_PER_LITER = 'https://identifiers.org/UO:0010050'

FLUID_UNIT_CONCENTRATION = '%'
FLUID_UNIT_MOLAR = 'M'
FLUID_UNIT_MILLI_MOLAR = 'mM'
FLUID_UNIT_FOLD = 'X'
FLUID_UNIT_GRAM_PER_LITER = 'g/L'
FLUID_UNIT_MICROGRAM_PER_MILLILITER = 'ug/ml'
FLUID_UNIT_MICROMOLE = 'micromole'
FLUID_UNIT_MICROMOLE_ABBREVIATION = 'uM'
FLUID_UNIT_NANOMOLE = 'nM'
FLUID_UNIT_MILLIGRAM_PER_MILLILITER = 'mg/ml'
FLUID_UNIT_NANOGRAM_PER_LITER = 'ng/ul'
FLUID_UNIT_MICROLITRE = 'microliter'
FLUID_UNIT_NANOMETER = 'nanometer'

FLUID_UNIT_MAP = {FLUID_UNIT_CONCENTRATION: NCIT_CONCENTRATION,
                  FLUID_UNIT_MOLAR: UO_MOLAR,
                  FLUID_UNIT_MILLI_MOLAR: UO_MILLI_MOLAR,
                  FLUID_UNIT_FOLD: NCIT_FOLD_CHANGE,
                  FLUID_UNIT_GRAM_PER_LITER: UO_GRAM_PER_LITER,
                  FLUID_UNIT_MICROGRAM_PER_MILLILITER: NCIT_MICROGRAM_PER_MILLILITER,
                  FLUID_UNIT_MICROMOLE: NCIT_MICROMOLE,
                  FLUID_UNIT_NANOMOLE: NCIT_NANOMOLE,
                  FLUID_UNIT_MICROMOLE_ABBREVIATION: NCIT_MICROMOLE,
                  FLUID_UNIT_MILLIGRAM_PER_MILLILITER: UO_MILLIGRAM_PER_MILLILITER,
                  FLUID_UNIT_NANOGRAM_PER_LITER: UO_NANO_GRAM_PER_LITER,
                  FLUID_UNIT_MICROLITRE: OTU_MICROLITRE,
                  FLUID_UNIT_NANOMETER: OTU_NANOMETER}

TEMPERATURE_UNIT_CELSIUS = 'celsius'
TEMPERATURE_UNIT_FAHRENHEIT = 'fahrenheit'
TEMPERATURE_UNIT_MAP = {TEMPERATURE_UNIT_CELSIUS: NCIT_CELSIUS,
                        TEMPERATURE_UNIT_FAHRENHEIT: NCIT_FAHRENHEIT}

TIME_UNIT_DAY = 'day'
TIME_UNIT_HOUR = 'hour'
TIME_UNIT_FEMTOSECOND = 'femtosecond'
TIME_UNIT_MICROSECOND = 'microsecond'
TIME_UNIT_MILLISECOND = 'millisecond'
TIME_UNIT_MINUTE = 'minute'
TIME_UNIT_MONTH = 'month'
TIME_UNIT_NANOSECOND = 'nanosecond'
TIME_UNIT_PICOSECOND = 'picosecond'
TIME_UNIT_SECOND = 'second'
TIME_UNIT_WEEK = 'week'
TIME_UNIT_YEAR = 'year'
TIME_UNIT_MAP = {TIME_UNIT_DAY: NCIT_MONTH,
                 TIME_UNIT_HOUR: NCIT_HOUR,
                 TIME_UNIT_FEMTOSECOND: OTU_FEMTOSECOND,
                 TIME_UNIT_MICROSECOND: NCIT_MICROSECOND,
                 TIME_UNIT_MILLISECOND: NCIT_MILLISECOND,
                 TIME_UNIT_MINUTE: NCIT_MINUTE,
                 TIME_UNIT_MONTH: NCIT_MONTH,
                 TIME_UNIT_NANOSECOND: NCIT_NANOSECOND,
                 TIME_UNIT_PICOSECOND: NCIT_PICOSECOND,
                 TIME_UNIT_SECOND: NCIT_SECOND,
                 TIME_UNIT_WEEK: NCIT_WEEK,
                 TIME_UNIT_YEAR: NCIT_YEAR}

# measurement-type specific to SD2 project
SD2_AUTOMATED_TEST_URI = 'http://sd2e.org#automatedTest'
SD2_CONDITION_SPACE_URI = 'http://sd2e.org#conditionSpace'
SD2_EXPERIMENTAL_DESIGN_URI = 'http://sd2e.org#experimentalDesign'

MEASUREMENT_TYPE_MAPPINGS = {
    MEASUREMENT_TYPE_FLOW: NCIT_FLOW_URI,
    MEASUREMENT_TYPE_RNA_SEQ: NCIT_RNA_SEQ_URI,
    MEASUREMENT_TYPE_DNA_SEQ: NCIT_DNA_SEQ_URI,
    MEASUREMENT_TYPE_PROTEOMICS: NCIT_PROTEOMICS_URI,
    MEASUREMENT_TYPE_SEQUENCING_CHROMATOGRAM: NCIT_SEQUENCING_CHROMATOGRAM_URI,
    MEASUREMENT_TYPE_AUTOMATED_TEST: SD2_AUTOMATED_TEST_URI,
    MEASUREMENT_TYPE_CFU: NCIT_CFU_URI,
    MEASUREMENT_TYPE_PLATE_READER: NCIT_PLATE_READER_URI,
    MEASUREMENT_TYPE_CONDITION_SPACE: SD2_CONDITION_SPACE_URI,
    MEASUREMENT_TYPE_EXPERIMENTAL_DESIGN: SD2_EXPERIMENTAL_DESIGN_URI
}

# Strateos Protocols Supported in IP
GROWTH_CURVE_PROTOCOL = 'GrowthCurve'
OBSTACLE_COURSE_PROTOCOL = 'ObstacleCourse'
TIME_SERIES_HTP_PROTOCOL = 'TimeSeriesHTP'
CELL_FREE_RIBO_SWITCH_PROTOCOL = 'CellFreeRiboswitches'

# Mapping protocols to human readible names
PROTOCOL_PLACEHOLDER = 'Select a protocol'

PROTOCOL_FIELD_XPLAN_BASE_DIRECTORY = 'XPlan Base Directory'
PROTOCOL_FIELD_XPLAN_REACTOR = 'XPlan Reactor'
PROTOCOL_FIELD_PLATE_SIZE = 'Plate Size'
PROTOCOL_FIELD_PLATE_NUMBER = 'Plate Number'
PROTOCOL_FIELD_CONTAINER_SEARCH_STRING = 'Container Search String'
PROTOCOL_FIELD_STRAIN_PROPERTY = 'Strain Property'
PROTOCOL_FIELD_XPLAN_PATH = 'XPlan Path'
PROTOCOL_FIELD_PROTOCOL_ID = 'Protocol ID'
PROTOCOL_FIELD_EXPERIMENT_REFERENCE_URL_FOR_XPLAN = 'Experiment Reference URL For XPlan'
PROTOCOL_FIELD_SUBMIT = 'Submit'
PROTOCOL_FIELD_TEST_MODE = 'Test Mode'

PARAMETER_PROTOCOL_NAME = 'protocol'
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
PARAMETER_READER_INFO_LIST_OF_GAINS = 'plate_reader_info.list_of_gains'
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
PARAMETER_RXN_INFO_RXN_GROUP_INFO_MG_GLU2 = 'rxn_info.rxn_group.rxn_info.mg_glu2'
PARAMETER_INDUCERS = 'inducers'

SD2_SPREADSHEET_ID = '1oLJTTydL_5YPyk-wY-dspjIw_bPZ3oCiWiK0xtG8t3g'  # Sd2 Program dict
TEST_SPREADSHEET_ID = '1wHX8etUZFMrvmsjvdhAGEVU1lYgjbuRX5mmYlKv7kdk'  # Intent parser test dict
UNIT_TEST_SPREADSHEET_ID = '1r3CIyv75vV7A7ghkB0od-TM_16qSYd-byAbQ1DhRgB0'  #sd2 unit test dictionary

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

HEADER_NUMBER_OF_NEGATIVE_CONTROLS_VALUE = 'Number of Negative Controls'
HEADER_USE_RNA_INHIBITOR_IN_REACTION_VALUE = 'Use RNAse Inhibitor in Reaction'
HEADER_DNA_REACTION_CONCENTRATION_VALUE = 'DNA Reaction Concentration'
HEADER_TEMPLATE_DNA_VALUE = 'Template DNA'

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
HEADER_NUM_NEG_CONTROL_TYPE = 'NUM_NEG_CONTROLS'
HEADER_RNA_INHIBITOR_REACTION_TYPE = 'RNA_INHIBITOR_REACTION'
HEADER_DNA_REACTION_CONCENTRATION_TYPE = 'DNA_REACTION_CONCENTRATION'
HEADER_TEMPLATE_DNA_TYPE = 'TEMPLATE_DNA'

SYNBIOHUB_DEPLOYED_DATABASE = 'hub.sd2e.org'
SYNBIOHUB_STAGING_DATABASE = 'hub-staging.sd2e.org'
SYNBIOHUB_DEPLOYED_DATABASE_URL = 'https://%s' % SYNBIOHUB_DEPLOYED_DATABASE
SYNBIOHUB_STAGING_DATABASE_URL = 'https://%s' % SYNBIOHUB_STAGING_DATABASE
SYNBIOHUB_DESIGN_COLLECTION_USER = 'sd2e'
SYNBIOHUB_DESIGN_COLLECTION_PREFIX = 'https://hub.sd2e.org/user/%s/design/' % SYNBIOHUB_DESIGN_COLLECTION_USER
SYNBIOHUB_DESIGN_COLLECTION_URI = SYNBIOHUB_DESIGN_COLLECTION_PREFIX + 'design_collection/1'
SYBIOHUB_COLLECTION_NAME_DESIGN = 'design'

SD2E_NAMESPACE = 'https://sd2e.org/'
TACC_SERVER = 'TACC'
GOOGLE_DRIVE_EXPERIMENT_REQUEST_FOLDER = '1FYOFBaUDIS-lBn0fr76pFFLBbMeD25b3'