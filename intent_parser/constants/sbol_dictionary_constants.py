import intent_parser.constants.sd2_datacatalog_constants as dc_constants

"""
List of constants used for referring to terms in SBOL Dictionary spreadsheet.
"""
ATTRIBUTE_TAB = 'Attribute'
STRAIN_TAB = 'Strain'

COLUMN_BIOFAB_UID = 'BioFAB UID'
COLUMN_CALTECH_UID = 'CalTech UID'
COLUMN_COMMON_NAME = 'Common Name'
COLUMN_DAMP_UID = 'DAMP (BU) UID'
COLUMN_DUKE_UID = 'Duke UID'
COLUMN_EMERALD_CLOUD_UID = 'EmeraldCloud UID'
COLUMN_GINKGO_UID = 'Ginkgo UID'
COLUMN_LBNL_UID = 'LBNL UID'
COLUMN_PENNSTATE_UID = 'PennState (Salis) UID'
COLUMN_SYNBIOHUB_URI = 'SynBioHub URI'
COLUMN_TACC_UID = 'TACC UID'
COLUMN_TRANSCRIPT_UID = 'Transcriptic UID'

MAPPED_LAB_UID = {dc_constants.LAB_CALTECH: COLUMN_CALTECH_UID,
                  dc_constants.LAB_DUKE_HAASE: COLUMN_DUKE_UID,
                  dc_constants.LAB_EMERALD: COLUMN_EMERALD_CLOUD_UID,
                  dc_constants.LAB_GEO: None,
                  dc_constants.LAB_GINKGO: COLUMN_GINKGO_UID,
                  dc_constants.LAB_MARSHALL: None,
                  dc_constants.LAB_PNNL_EGBERT: None,
                  dc_constants.LAB_PSU_SALIS: COLUMN_PENNSTATE_UID,
                  dc_constants.LAB_TACC: COLUMN_TACC_UID,
                  dc_constants.LAB_TRANSCRIPTIC: COLUMN_TRANSCRIPT_UID,
                  dc_constants.LAB_UCSB_YEUNG: None,
                  dc_constants.LAB_UW_BIOFAB: COLUMN_BIOFAB_UID
                  }
