from intent_parser.table.controls_table import ControlsTable
from intent_parser.table.measurement_table import MeasurementTable
from intent_parser.table.intent_parser_cell import IntentParserCell
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
from intent_parser.intent.strain_intent import StrainIntent
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.tests.test_util as test_utils
import unittest

class MeasurementTableTest(unittest.TestCase):
    """
    Test parsing information from a measurement table.
    """
    def setUp(self):
        self.ip_table_factory = IntentParserTableFactory()
        strain1 = StrainIntent('https://hub.sd2e.org/user/sd2e/design/MG1655/1', 'ip_admin', 'strain1',
                               lab_strain_names=['MG1655'])
        strain2 = StrainIntent('https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1', 'ip_admin', 'strain2',
                               lab_strain_names=['MG1655_LPV3'])
        strain3 = StrainIntent('https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1', 'ip_admin', 'strain3',
                               lab_strain_names=['UWBF_7376'])
        self.strain_mappings = {'https://hub.sd2e.org/user/sd2e/design/MG1655/1': strain1,
                                'https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1': strain2,
                                'https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1': strain3}

    def tearDown(self):
        pass
              
    def test_table_with_measurement_type(self):
        ip_table = test_utils.create_fake_measurement_table()
        measurement_type = IntentParserCell()
        measurement_type.add_paragraph('FLOW')
        data_row = test_utils.create_measurement_table_row(measurement_type_cell=measurement_type)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, measurement_types={'PLATE_READER', 'FLOW'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        self.assertEqual(meas_result[0][dc_constants.MEASUREMENT_TYPE], 'FLOW')

    def test_table_with_empty_file_type(self):
        ip_table = test_utils.create_fake_measurement_table()
        file_type = IntentParserCell()
        file_type.add_paragraph('')
        data_row = test_utils.create_measurement_table_row(file_type_cell=file_type)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(0, len(meas_result))
    
    def test_table_with_file_type(self):
        ip_table = test_utils.create_fake_measurement_table()
        file_type = IntentParserCell()
        file_type.add_paragraph('FASTQ')
        data_row = test_utils.create_measurement_table_row(file_type_cell=file_type)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, file_type={'FASTQ'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        self.assertTrue(dc_constants.FILE_TYPE in meas_result[0])
        self.assertEqual(['FASTQ'], meas_result[0][dc_constants.FILE_TYPE])

    def test_mixture_of_lab_row_col_ids(self):
        ip_table = test_utils.create_fake_measurement_table()
        col_ids = IntentParserCell()
        col_ids.add_paragraph('13')
        lab_ids = IntentParserCell()
        lab_ids.add_paragraph('foo')
        row_ids = IntentParserCell()
        row_ids.add_paragraph('3')
        data_row = test_utils.create_measurement_table_row(lab_id_cell=lab_ids, row_id_cell=row_ids, col_id_cell=col_ids)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        expected_results = {'contents': [[{'name': {'label': 'column_id', 'sbh_uri': 'NO PROGRAM DICTIONARY ENTRY'}, 'value': 13}],
                                         [{'name': {'label': 'lab_id', 'sbh_uri': 'NO PROGRAM DICTIONARY ENTRY'}, 'value': 'foo'}],
                                         [{'name': {'label': 'row_id', 'sbh_uri': 'NO PROGRAM DICTIONARY ENTRY'}, 'value': 3}]]}
        self.assertEqual(1, len(meas_result))
        self.assertEqual(expected_results[dc_constants.CONTENTS], meas_result[0][dc_constants.CONTENTS])

    def test_table_with_3_lab_ids(self):
        ip_table = test_utils.create_fake_measurement_table()
        lab_ids = IntentParserCell()
        lab_ids.add_paragraph('foo, r1eu66zybzdwew, lab_id')
        data_row = test_utils.create_measurement_table_row(lab_id_cell=lab_ids)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        expected_results = {'contents': [[{'name': {'label': 'lab_id', 'sbh_uri': 'NO PROGRAM DICTIONARY ENTRY'}, 'value': 'foo'},
                            {'name': {'label': 'lab_id', 'sbh_uri': 'NO PROGRAM DICTIONARY ENTRY'}, 'value': 'r1eu66zybzdwew'},
                            {'name': {'label': 'lab_id', 'sbh_uri': 'NO PROGRAM DICTIONARY ENTRY'}, 'value': 'lab_id'}]]}
        self.assertEqual(1, len(meas_result))
        self.assertEqual(expected_results[dc_constants.CONTENTS], meas_result[0][dc_constants.CONTENTS])

    def test_table_with_3_row_ids(self):
        ip_table = test_utils.create_fake_measurement_table()
        row_ids = IntentParserCell()
        row_ids.add_paragraph('1, 2, 3')
        data_row = test_utils.create_measurement_table_row(row_id_cell=row_ids)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        expected_results = {'contents': [[{'name': {'label': 'row_id', 'sbh_uri': 'NO PROGRAM DICTIONARY ENTRY'}, 'value': 1},
                                          {'name': {'label': 'row_id', 'sbh_uri': 'NO PROGRAM DICTIONARY ENTRY'}, 'value': 2},
                                          {'name': {'label': 'row_id', 'sbh_uri': 'NO PROGRAM DICTIONARY ENTRY'}, 'value': 3}]]}
        self.assertEqual(1, len(meas_result))
        self.assertEqual(expected_results[dc_constants.CONTENTS], meas_result[0][dc_constants.CONTENTS])

    def test_table_with_3_col_ids(self):
        ip_table = test_utils.create_fake_measurement_table()
        col_ids = IntentParserCell()
        col_ids.add_paragraph('1, 2, 3')
        data_row = test_utils.create_measurement_table_row(col_id_cell=col_ids)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        expected_results = {'contents': [[{'name': {'label': 'column_id', 'sbh_uri': 'NO PROGRAM DICTIONARY ENTRY'}, 'value': 1},
                                          {'name': {'label': 'column_id', 'sbh_uri': 'NO PROGRAM DICTIONARY ENTRY'}, 'value': 2},
                                          {'name': {'label': 'column_id', 'sbh_uri': 'NO PROGRAM DICTIONARY ENTRY'}, 'value': 3}]]}
        self.assertEqual(1, len(meas_result))
        self.assertEqual(expected_results[dc_constants.CONTENTS], meas_result[0][dc_constants.CONTENTS])

    def test_table_with_number_of_negative_control_type(self):
        ip_table = test_utils.create_fake_measurement_table()
        num_neg_controls = IntentParserCell()
        num_neg_controls.add_paragraph('1, 2, 3')
        data_row = test_utils.create_measurement_table_row(num_neg_controls_cell=num_neg_controls)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        expected_results = {dc_constants.CONTENTS: [[{dc_constants.NAME: {dc_constants.LABEL: ip_constants.HEADER_NUMBER_OF_NEGATIVE_CONTROLS_VALUE,
                                                                          dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
                                                      dc_constants.VALUE: 1},
                                                     {dc_constants.NAME: {
                                                         dc_constants.LABEL: ip_constants.HEADER_NUMBER_OF_NEGATIVE_CONTROLS_VALUE,
                                                         dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
                                                      dc_constants.VALUE: 2},
                                                     {dc_constants.NAME: {
                                                         dc_constants.LABEL: ip_constants.HEADER_NUMBER_OF_NEGATIVE_CONTROLS_VALUE,
                                                         dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
                                                      dc_constants.VALUE: 3}]]}
        self.assertEqual(1, len(meas_result))
        self.assertEqual(expected_results[dc_constants.CONTENTS], meas_result[0][dc_constants.CONTENTS])

    def test_table_with_rna_inhibitor_in_reaction(self):
        ip_table = test_utils.create_fake_measurement_table()
        rna_inhibitor_reaction = IntentParserCell()
        rna_inhibitor_reaction.add_paragraph('false, true')
        data_row = test_utils.create_measurement_table_row(rna_inhibitor_reaction_cell=rna_inhibitor_reaction)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        expected_results = {dc_constants.CONTENTS: [
            [{dc_constants.NAME: {dc_constants.LABEL: ip_constants.HEADER_USE_RNA_INHIBITOR_IN_REACTION_VALUE,
                                  dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
              dc_constants.VALUE: 'False'},
             {dc_constants.NAME: {dc_constants.LABEL: ip_constants.HEADER_USE_RNA_INHIBITOR_IN_REACTION_VALUE,
                                  dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
              dc_constants.VALUE: 'True'}
             ]]}
        self.assertEqual(1, len(meas_result))
        self.assertEqual(expected_results[dc_constants.CONTENTS], meas_result[0][dc_constants.CONTENTS])

    def test_table_with_template_dna(self):
        ip_table = test_utils.create_fake_measurement_table()
        template_dna = IntentParserCell()
        template_dna.add_paragraph('Test DNA1, Test DNA2')
        data_row = test_utils.create_measurement_table_row(template_dna_cell=template_dna)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        expected_results = {dc_constants.CONTENTS: [
            [{dc_constants.NAME: {dc_constants.LABEL: ip_constants.HEADER_TEMPLATE_DNA_VALUE,
                                  dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
              dc_constants.VALUE: 'Test DNA1'},
             {dc_constants.NAME: {dc_constants.LABEL: ip_constants.HEADER_TEMPLATE_DNA_VALUE,
                                  dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
              dc_constants.VALUE: 'Test DNA2'}
             ]]}
        self.assertEqual(1, len(meas_result))
        self.assertEqual(expected_results[dc_constants.CONTENTS], meas_result[0][dc_constants.CONTENTS])

    def test_table_with_dna_reaction_concentration_cell(self):
        ip_table = test_utils.create_fake_measurement_table()
        dna_reaction_concentration = IntentParserCell()
        dna_reaction_concentration.add_paragraph('1, 2, 3')
        data_row = test_utils.create_measurement_table_row(dna_reaction_concentration_cell=dna_reaction_concentration)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        expected_results = {dc_constants.CONTENTS: [[{dc_constants.NAME: {dc_constants.LABEL: ip_constants.HEADER_DNA_REACTION_CONCENTRATION_VALUE,
                                                                          dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
                                                      dc_constants.VALUE: 1},
                                                     {dc_constants.NAME: {
                                                         dc_constants.LABEL: ip_constants.HEADER_DNA_REACTION_CONCENTRATION_VALUE,
                                                         dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
                                                      dc_constants.VALUE: 2},
                                                     {dc_constants.NAME: {
                                                         dc_constants.LABEL: ip_constants.HEADER_DNA_REACTION_CONCENTRATION_VALUE,
                                                         dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
                                                      dc_constants.VALUE: 3}]]}
        self.assertEqual(1, len(meas_result))
        self.assertEqual(expected_results[dc_constants.CONTENTS], meas_result[0][dc_constants.CONTENTS])
    
    def test_table_with_1_replicate(self):
        ip_table = test_utils.create_fake_measurement_table()
        replicate = IntentParserCell()
        replicate.add_paragraph('3')
        data_row = test_utils.create_measurement_table_row(replicate_cell=replicate)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        self.assertEqual(meas_result[0][dc_constants.REPLICATES], 3)
        
    def test_table_with_3_replicates(self):
        ip_table = test_utils.create_fake_measurement_table()
        replicate = IntentParserCell()
        replicate.add_paragraph('1,2,3')
        data_row = test_utils.create_measurement_table_row(replicate_cell=replicate)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        self.assertEqual(meas_result[0][dc_constants.REPLICATES], 1)
    
    def test_table_with_1_strain(self):
        ip_table = test_utils.create_fake_measurement_table()
        strains = IntentParserCell()
        strains.add_paragraph('test_strain', link='https://foo.com')
        data_row = test_utils.create_measurement_table_row(strain_cell=strains)
        ip_table.add_row(data_row)

        strain_obj = StrainIntent('https://foo.com', 'myLab', 'AND_00', lab_strain_names={'test_strain', 'foo-strain'})
        strain_mapping = {'https://foo.com': strain_obj}

        meas_table = MeasurementTable(ip_table, strain_mapping=strain_mapping)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        self.assertEqual(1, len(meas_result[0][dc_constants.STRAINS]))
        expected_strain = {dc_constants.SBH_URI: 'https://foo.com',
                           dc_constants.LABEL: 'AND_00',
                           dc_constants.LAB_ID: 'name.mylab.test_strain'}
        self.assertEqual(expected_strain, meas_result[0][dc_constants.STRAINS][0])

    def test_strain_with_unknown_links(self):
        ip_table = test_utils.create_fake_measurement_table()
        strains = IntentParserCell()
        strains.add_paragraph('test_strain', link='https://foo.com')
        data_row = test_utils.create_measurement_table_row(strain_cell=strains)
        ip_table.add_row(data_row)

        strain_obj = StrainIntent('https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1', 'myLab', 'AND_00', lab_strain_names={'test_strain', 'foo-strain'})
        strain_mapping = {'https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1': strain_obj}

        meas_table = MeasurementTable(ip_table, strain_mapping=strain_mapping)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(0, len(meas_result))

    def test_strain_not_supported_in_lab_name(self):
        ip_table = test_utils.create_fake_measurement_table()
        strains = IntentParserCell()
        strains.add_paragraph('test_strain', link='https://foo.com')
        data_row = test_utils.create_measurement_table_row(strain_cell=strains)
        ip_table.add_row(data_row)

        strain_obj = StrainIntent('https://foo.com', dc_constants.LAB_TACC, 'AND_00', lab_strain_names={'UWBF_7376'})
        strain_mapping = {'https://foo.com': strain_obj}

        meas_table = MeasurementTable(ip_table, strain_mapping=strain_mapping)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(0, len(meas_result))

    def test_strains_with_inconsistent_links(self):
        ip_table = test_utils.create_fake_measurement_table()
        lab_strain1 = 'UWBF_7376'
        lab_strain2 = 'UWBF_7378'
        strain_link1 = 'https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1'
        strain_link2 = 'https://hub.sd2e.org/user/sd2e/design/UWBF_7378/1'
        strains = IntentParserCell()
        strains.add_paragraph(lab_strain1, link=strain_link1)
        strains.add_paragraph(',test_strain,')
        strains.add_paragraph(lab_strain2, link=strain_link2)
        data_row = test_utils.create_measurement_table_row(strain_cell=strains)
        ip_table.add_row(data_row)

        strain1_obj = StrainIntent(strain_link1, 'myLab', 'AND_00', lab_strain_names={lab_strain1})
        strain2_obj = StrainIntent(strain_link2, 'myLab', 'AND_01', lab_strain_names={lab_strain2})
        strain_mapping = {strain_link1: strain1_obj,
                          strain_link2: strain2_obj}

        meas_table = MeasurementTable(ip_table, strain_mapping=strain_mapping)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        actual_strains = meas_result[0][dc_constants.STRAINS]
        self.assertEqual(2, len(actual_strains))
        expected_strain1 = {dc_constants.SBH_URI: strain_link1,
                           dc_constants.LABEL: 'AND_00',
                           dc_constants.LAB_ID: 'name.mylab.%s' % lab_strain1}
        expected_strain2 = {dc_constants.SBH_URI: strain_link2,
                            dc_constants.LABEL: 'AND_01',
                            dc_constants.LAB_ID: 'name.mylab.%s' % lab_strain2}
        self.assertEqual(expected_strain1, actual_strains[0])
        self.assertEqual(expected_strain2, actual_strains[1])

    def test_table_with_1_timepoint(self):
        ip_table = test_utils.create_fake_measurement_table()
        timepoint = IntentParserCell()
        timepoint.add_paragraph('3 hour')
        data_row = test_utils.create_measurement_table_row(timepoint_cell=timepoint)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, timepoint_units={'hour'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        
        exp_res1 = {dc_constants.VALUE: 3.0, dc_constants.UNIT: 'hour'}
        self.assertEqual(1, len(meas_result[0][dc_constants.TIMEPOINTS]))
        self.assertDictEqual(exp_res1, meas_result[0][dc_constants.TIMEPOINTS][0])
                  
    def test_table_with_3_timepoint(self):
        ip_table = test_utils.create_fake_measurement_table()
        timepoint = IntentParserCell()
        timepoint.add_paragraph('6, 12, 24 hour')
        data_row = test_utils.create_measurement_table_row(timepoint_cell=timepoint)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, timepoint_units={'hour'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        
        exp_res1 = {dc_constants.VALUE: 6.0, dc_constants.UNIT: 'hour'}
        exp_res2 = {dc_constants.VALUE: 12.0, dc_constants.UNIT: 'hour'}
        exp_res3 = {dc_constants.VALUE: 24.0, dc_constants.UNIT: 'hour'}
        self.assertEqual(3, len(meas_result[0][dc_constants.TIMEPOINTS]))
        for timepoint in meas_result[0][dc_constants.TIMEPOINTS]:
            self.assertFalse(timepoint != exp_res1 and timepoint != exp_res2 and timepoint != exp_res3)
    
    def test_table_with_1_temperature(self):
        ip_table = test_utils.create_fake_measurement_table()
        temperature = IntentParserCell()
        temperature.add_paragraph('1 fahrenheit')
        data_row = test_utils.create_measurement_table_row(temperature_cell=temperature)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, temperature_units={'fahrenheit'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        
        exp_res1 = {dc_constants.VALUE: 1.0, dc_constants.UNIT: 'fahrenheit'}
        self.assertEqual(1, len(meas_result[0][dc_constants.TEMPERATURES]))
        self.assertDictEqual(exp_res1, meas_result[0][dc_constants.TEMPERATURES][0])
        
    def test_table_with_1_temperature_and_unspecified_unit(self):
        ip_table = test_utils.create_fake_measurement_table()
        temperature = IntentParserCell()
        temperature.add_paragraph('1 dummy')
        data_row = test_utils.create_measurement_table_row(temperature_cell=temperature)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, temperature_units={'celsius', 'fahrenheit'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(0, len(meas_result))

    def test_table_with_2_temperature_and_unit_abbreviation(self):
        ip_table = test_utils.create_fake_measurement_table()
        temperature = IntentParserCell()
        temperature.add_paragraph('3, 2, 1 C')
        data_row = test_utils.create_measurement_table_row(temperature_cell=temperature)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, temperature_units={'celsius'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        
        exp_res1 = {dc_constants.VALUE: 3.0, dc_constants.UNIT: 'celsius'}
        exp_res2 = {dc_constants.VALUE: 2.0, dc_constants.UNIT: 'celsius'}
        exp_res3 = {dc_constants.VALUE: 1.0, dc_constants.UNIT: 'celsius'}
        self.assertEqual(3, len(meas_result[0][dc_constants.TEMPERATURES]))
        for temperature in meas_result[0][dc_constants.TEMPERATURES]:
            self.assertFalse(temperature != exp_res1 and temperature != exp_res2 and temperature != exp_res3)  
             
    def test_table_with_3_temperature(self):
        ip_table = test_utils.create_fake_measurement_table()
        temperature = IntentParserCell()
        temperature.add_paragraph('3, 2, 1 celsius')
        data_row = test_utils.create_measurement_table_row(temperature_cell=temperature)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, temperature_units={'celsius'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        
        exp_res1 = {dc_constants.VALUE: 3.0, dc_constants.UNIT: 'celsius'}
        exp_res2 = {dc_constants.VALUE: 2.0, dc_constants.UNIT: 'celsius'}
        exp_res3 = {dc_constants.VALUE: 1.0, dc_constants.UNIT: 'celsius'}
        self.assertEqual(3, len(meas_result[0][dc_constants.TEMPERATURES]))
        for temperature in meas_result[0][dc_constants.TEMPERATURES]:
            self.assertFalse(temperature != exp_res1 and temperature != exp_res2 and temperature != exp_res3)  
    
    def test_table_with_samples(self):
        ip_table = test_utils.create_fake_measurement_table()
        samples = IntentParserCell()
        samples.add_paragraph('5, 10, 15')
        data_row = test_utils.create_measurement_table_row(sample_cell=samples)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(0, len(meas_result))
    
    def test_table_with_notes(self):
        ip_table = test_utils.create_fake_measurement_table()
        notes = IntentParserCell()
        notes.add_paragraph('5, 10, 15')
        data_row = test_utils.create_measurement_table_row(notes_cell=notes)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(0, len(meas_result))
    
    def test_table_with_1_ods(self):
        ip_table = test_utils.create_fake_measurement_table()
        ods = IntentParserCell()
        ods.add_paragraph('3')
        data_row = test_utils.create_measurement_table_row(ods_cell=ods)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        self.assertEqual(1, len(meas_result[0]['ods']))
        self.assertListEqual([3.0], meas_result[0]['ods'])
        
    def test_table_with_3_ods(self):
        ip_table = test_utils.create_fake_measurement_table()
        ods = IntentParserCell()
        ods.add_paragraph('33, 22, 11')
        data_row = test_utils.create_measurement_table_row(ods_cell=ods)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        self.assertEqual(3, len(meas_result[0][dc_constants.ODS]))
        self.assertListEqual([33.0, 22.0, 11.0], meas_result[0][dc_constants.ODS])
        
    def test_table_with_one_value_reagent(self):
        reagent_name = 'L-arabinose'
        reagent_uri = 'https://hub.sd2e.org/user/sd2e/design/Larabinose/1'
        reagent_header = IntentParserCell()
        reagent_header.add_paragraph(reagent_name, link=reagent_uri)
        ip_table = test_utils.create_fake_measurement_table(reagent_media_cells=[reagent_header])

        reagent = IntentParserCell()
        reagent.add_paragraph('9 mM')
        data_row = test_utils.create_measurement_table_row(reagent)
        data_row.append(reagent)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, fluid_units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        
        exp_res1 = {dc_constants.NAME: {dc_constants.LABEL: reagent_name, dc_constants.SBH_URI: reagent_uri},
                    dc_constants.VALUE: '9.0',
                    dc_constants.UNIT: 'mM'}
        self.assertEqual(1, len(meas_result[0][dc_constants.CONTENTS][0]))
        self.assertEqual(exp_res1, meas_result[0][dc_constants.CONTENTS][0][0])
            
    def test_table_with_three_value_reagent(self):
        reagent_name = 'L-arabinose'
        reagent_uri = 'https://hub.sd2e.org/user/sd2e/design/Larabinose/1'
        reagent_header = IntentParserCell()
        reagent_header.add_paragraph(reagent_name, link=reagent_uri)
        ip_table = test_utils.create_fake_measurement_table(reagent_media_cells=[reagent_header])

        reagent = IntentParserCell()
        reagent.add_paragraph('0, 1, 2 micromole')
        data_row = test_utils.create_measurement_table_row(reagent)
        data_row.append(reagent)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, fluid_units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        
        exp_res1 = {dc_constants.NAME: {dc_constants.LABEL: reagent_name, dc_constants.SBH_URI: reagent_uri},
                    dc_constants.VALUE: '0.0',
                    dc_constants.UNIT: 'micromole'}
        exp_res2 = {dc_constants.NAME: {dc_constants.LABEL: reagent_name, dc_constants.SBH_URI: reagent_uri},
                    dc_constants.VALUE: '1.0',
                    dc_constants.UNIT: 'micromole'}
        exp_res3 = {dc_constants.NAME: {dc_constants.LABEL: reagent_name, dc_constants.SBH_URI: reagent_uri},
                    dc_constants.VALUE: '2.0',
                    dc_constants.UNIT: 'micromole'}
        self.assertEqual(3, len(meas_result[0][dc_constants.CONTENTS][0]))
        for act_res in meas_result[0][dc_constants.CONTENTS][0]:
            self.assertFalse(act_res != exp_res1 and act_res != exp_res2 and act_res != exp_res3)
            
    def test_table_with_reagent_and_unit_abbreviation(self):
        reagent_name = 'L-arabinose'
        reagent_uri = 'https://hub.sd2e.org/user/sd2e/design/Larabinose/1'
        reagent_header = IntentParserCell()
        reagent_header.add_paragraph(reagent_name, link=reagent_uri)
        ip_table = test_utils.create_fake_measurement_table(reagent_media_cells=[reagent_header])

        reagent = IntentParserCell()
        reagent.add_paragraph('1 fold')
        data_row = test_utils.create_measurement_table_row(reagent)
        data_row.append(reagent)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, fluid_units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        
        exp_res1 = {dc_constants.NAME: {dc_constants.LABEL: reagent_name, dc_constants.SBH_URI: reagent_uri},
                    dc_constants.VALUE: '1.0',
                    dc_constants.UNIT: 'X'}
        self.assertEqual(1, len(meas_result[0][dc_constants.CONTENTS][0]))
        self.assertEqual(exp_res1, meas_result[0][dc_constants.CONTENTS][0][0])
    
    def test_table_with_reagent_and_percentage_unit(self):
        reagent_name = 'L-arabinose'
        reagent_uri = 'https://hub.sd2e.org/user/sd2e/design/Larabinose/1'
        reagent_header = IntentParserCell()
        reagent_header.add_paragraph(reagent_name, link=reagent_uri)
        ip_table = test_utils.create_fake_measurement_table(reagent_media_cells=[reagent_header])

        reagent = IntentParserCell()
        reagent.add_paragraph('11 %')
        data_row = test_utils.create_measurement_table_row(reagent)
        data_row.append(reagent)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, fluid_units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        
        exp_res1 = {dc_constants.NAME: {dc_constants.LABEL: reagent_name, dc_constants.SBH_URI: reagent_uri},
                    dc_constants.VALUE: '11.0', dc_constants.UNIT: '%'}
        self.assertEqual(1, len(meas_result[0][dc_constants.CONTENTS][0]))
        self.assertEqual(exp_res1, meas_result[0][dc_constants.CONTENTS][0][0])
        
    def test_table_with_reagent_and_unit_containing_backslash(self):
        reagent_name = 'L-arabinose'
        reagent_uri = 'https://hub.sd2e.org/user/sd2e/design/Larabinose/1'
        reagent_header = IntentParserCell()
        reagent_header.add_paragraph(reagent_name, link=reagent_uri)
        ip_table = test_utils.create_fake_measurement_table(reagent_media_cells=[reagent_header])

        reagent = IntentParserCell()
        reagent.add_paragraph('11 g/L')
        data_row = test_utils.create_measurement_table_row(reagent)
        data_row.append(reagent)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, fluid_units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        
        exp_res1 = {dc_constants.NAME: {dc_constants.LABEL: reagent_name, dc_constants.SBH_URI: reagent_uri},
                    dc_constants.VALUE: '11.0',
                    dc_constants.UNIT: 'g/L'}
        self.assertEquals(1, len(meas_result[0][dc_constants.CONTENTS][0]))
        self.assertEquals(exp_res1, meas_result[0][dc_constants.CONTENTS][0][0])
        
    def test_table_with_reagent_and_timepoint(self):
        reagent_uri = 'https://hub.sd2e.org/user/sd2e/design/beta0x2Destradiol/1'
        reagent_header = IntentParserCell()
        reagent_header.add_paragraph('SC_Media @ 18 hour', link=reagent_uri)
        ip_table = test_utils.create_fake_measurement_table(reagent_media_cells=[reagent_header])

        reagent = IntentParserCell()
        reagent.add_paragraph('0 M')
        data_row = test_utils.create_measurement_table_row(reagent)
        data_row.append(reagent)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, timepoint_units={'hour'}, fluid_units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        
        exp_res1 = {dc_constants.NAME: {dc_constants.LABEL: 'SC_Media', dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
                    dc_constants.VALUE: '0.0',
                    dc_constants.UNIT: 'M',
                    dc_constants.TIMEPOINT: {dc_constants.VALUE: 18.0, dc_constants.UNIT: 'hour'}}
        self.assertEqual(1, len(meas_result[0][dc_constants.CONTENTS][0]))
        self.assertEqual(exp_res1, meas_result[0][dc_constants.CONTENTS][0][0])

    def test_reagent_values_with_floating_points(self):
        reagent_uri = 'https://hub.sd2e.org/user/sd2e/design/Xylose/1'
        reagent_header = IntentParserCell()
        reagent_header.add_paragraph('Xylose', link=reagent_uri)
        ip_table = test_utils.create_fake_measurement_table(reagent_media_cells=[reagent_header])

        reagent = IntentParserCell()
        reagent.add_paragraph('26, 13, 6.5, 3.25, 1.625, .8125, .40625, .203125, .1015625, 0.05078125 mM')
        data_row = test_utils.create_measurement_table_row(reagent)
        data_row.append(reagent)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, timepoint_units={'hour'},
                                      fluid_units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))

        exp_res1 = [{dc_constants.NAME: {dc_constants.LABEL: 'Xylose', dc_constants.SBH_URI: reagent_uri}, dc_constants.VALUE: '26.0', dc_constants.UNIT: 'mM'},
                    {dc_constants.NAME: {dc_constants.LABEL: 'Xylose', dc_constants.SBH_URI: reagent_uri}, dc_constants.VALUE: '13.0', dc_constants.UNIT: 'mM'},
                    {dc_constants.NAME: {dc_constants.LABEL: 'Xylose', dc_constants.SBH_URI: reagent_uri}, dc_constants.VALUE: '6.5', dc_constants.UNIT: 'mM'},
                    {dc_constants.NAME: {dc_constants.LABEL: 'Xylose', dc_constants.SBH_URI: reagent_uri}, dc_constants.VALUE: '3.25', dc_constants.UNIT: 'mM'},
                    {dc_constants.NAME: {dc_constants.LABEL: 'Xylose', dc_constants.SBH_URI: reagent_uri}, dc_constants.VALUE: '1.625', dc_constants.UNIT: 'mM'},
                    {dc_constants.NAME: {dc_constants.LABEL: 'Xylose', dc_constants.SBH_URI: reagent_uri}, dc_constants.VALUE: '0.8125', dc_constants.UNIT: 'mM'},
                    {dc_constants.NAME: {dc_constants.LABEL: 'Xylose', dc_constants.SBH_URI: reagent_uri}, dc_constants.VALUE: '0.40625', dc_constants.UNIT: 'mM'},
                    {dc_constants.NAME: {dc_constants.LABEL: 'Xylose', dc_constants.SBH_URI: reagent_uri}, dc_constants.VALUE: '0.203125', dc_constants.UNIT: 'mM'},
                    {dc_constants.NAME: {dc_constants.LABEL: 'Xylose', dc_constants.SBH_URI: reagent_uri}, dc_constants.VALUE: '0.1015625', dc_constants.UNIT: 'mM'},
                    {dc_constants.NAME: {dc_constants.LABEL: 'Xylose', dc_constants.SBH_URI: reagent_uri}, dc_constants.VALUE: '0.05078125', dc_constants.UNIT: 'mM'}]
        self.assertEqual(10, len(meas_result[0][dc_constants.CONTENTS][0]))
        self.assertEqual(exp_res1, meas_result[0][dc_constants.CONTENTS][0])

    def test_table_text_with_reagent_and_timepoint(self):
        reagent_uri = 'https://hub.sd2e.org/user/sd2e/design/IPTG/1'
        reagent_header = IntentParserCell()
        reagent_header.add_paragraph('IPTG', link=reagent_uri)
        reagent_header.add_paragraph('@ 40 hours')
        ip_table = test_utils.create_fake_measurement_table(reagent_media_cells=[reagent_header])

        reagent = IntentParserCell()
        reagent.add_paragraph('NA')
        data_row = test_utils.create_measurement_table_row(reagent)
        data_row.append(reagent)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, timepoint_units={'hour'}, fluid_units={'%', 'M', 'mM', 'X', 'micromole', 'nM', 'g/L'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))

        exp_res1 = {dc_constants.NAME: {dc_constants.LABEL: 'IPTG', dc_constants.SBH_URI: reagent_uri},
                    dc_constants.VALUE: 'NA',
                    dc_constants.TIMEPOINT: {dc_constants.VALUE: 40.0, dc_constants.UNIT: 'hour'}}
        self.assertEqual(1, len(meas_result[0][dc_constants.CONTENTS][0]))
        self.assertEqual(exp_res1, meas_result[0][dc_constants.CONTENTS][0][0])

    def test_table_with_media(self):
        media_uri = 'https://hub.sd2e.org/user/sd2e/design/Media/1'
        media_header = IntentParserCell()
        media_header.add_paragraph('Media', link=media_uri)
        ip_table = test_utils.create_fake_measurement_table(reagent_media_cells=[media_header])

        reagent = IntentParserCell()
        reagent.add_paragraph('sc_media')
        data_row = test_utils.create_measurement_table_row(reagent)
        data_row.append(reagent)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table, timepoint_units={'hour'})
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEquals(1, len(meas_result))
        
        exp_res1 = {dc_constants.NAME: {dc_constants.LABEL: 'Media', dc_constants.SBH_URI: media_uri},
                    dc_constants.VALUE: 'sc_media'}
        self.assertEqual(1, len(meas_result[0][dc_constants.CONTENTS][0]))
        self.assertEqual(exp_res1, meas_result[0][dc_constants.CONTENTS][0][0])
     
    def test_table_with_media_containing_period_values(self):
        media_header = IntentParserCell()
        media_header.add_paragraph('media')
        ip_table = test_utils.create_fake_measurement_table(reagent_media_cells=[media_header])

        reagent = IntentParserCell()
        reagent.add_paragraph('Yeast_Extract_Peptone_Adenine_Dextrose (a.k.a. YPAD Media)')
        data_row = test_utils.create_measurement_table_row(reagent)
        data_row.append(reagent)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        
        exp_res1 = {dc_constants.NAME: {dc_constants.LABEL: 'media', dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
                    dc_constants.VALUE: 'Yeast_Extract_Peptone_Adenine_Dextrose (a.k.a. YPAD Media)'}
        self.assertEquals(1, len(meas_result[0][dc_constants.CONTENTS][0]))
        self.assertEquals(exp_res1, meas_result[0][dc_constants.CONTENTS][0][0])
        
    def test_table_with_media_containing_percentage_values(self):
        media_header = IntentParserCell()
        media_header.add_paragraph('media')
        ip_table = test_utils.create_fake_measurement_table(reagent_media_cells=[media_header])

        reagent = IntentParserCell()
        reagent.add_paragraph('Synthetic_Complete_2%Glycerol_2%Ethanol')
        data_row = test_utils.create_measurement_table_row(reagent)
        data_row.append(reagent)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        
        exp_res1 = {dc_constants.NAME: {dc_constants.LABEL: 'media', dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
                    dc_constants.VALUE: 'Synthetic_Complete_2%Glycerol_2%Ethanol'}
        self.assertEqual(1, len(meas_result[0][dc_constants.CONTENTS][0]))
        self.assertEqual(exp_res1, meas_result[0][dc_constants.CONTENTS][0][0])
    
    def test_table_with_media_containing_numerical_values(self):
        media_header = IntentParserCell()
        media_header.add_paragraph('media')
        ip_table = test_utils.create_fake_measurement_table(reagent_media_cells=[media_header])

        reagent = IntentParserCell()
        reagent.add_paragraph('SC+Glucose+Adenine+0.8M')
        data_row = test_utils.create_measurement_table_row(reagent)
        data_row.append(reagent)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        
        exp_res1 = {dc_constants.NAME: {dc_constants.LABEL: 'media', dc_constants.SBH_URI: dc_constants.NO_PROGRAM_DICTIONARY},
                    dc_constants.VALUE: 'SC+Glucose+Adenine+0.8M'}
        self.assertEqual(1, len(meas_result[0][dc_constants.CONTENTS][0]))
        self.assertEqual(exp_res1, meas_result[0][dc_constants.CONTENTS][0][0])
        
    def test_table_with_batch_values(self):
        ip_table = test_utils.create_fake_measurement_table()
        batch = IntentParserCell()
        batch.add_paragraph('0, 1')
        data_row = test_utils.create_measurement_table_row(batch_cell=batch)
        ip_table.add_row(data_row)

        meas_table = MeasurementTable(ip_table)
        meas_table.process_table()
        meas_result = meas_table.get_structured_request()
        self.assertEqual(1, len(meas_result))
        self.assertEqual(meas_result[0][dc_constants.BATCH], [0,1])
        
    def test_table_with_1_reference_control(self):
        ip_table_measurment = test_utils.create_fake_measurement_table()
        controls = IntentParserCell()
        controls.add_paragraph('Table 2')
        data_row = test_utils.create_measurement_table_row(controls_cell=controls)
        ip_table_measurment.add_row(data_row)

        ip_table_controls = test_utils.create_fake_controls_table(2)
        control_type = IntentParserCell()
        control_type.add_paragraph('HIGH_FITC')
        strains = IntentParserCell()
        strains.add_paragraph('UWBF_7376', link='https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1')
        data_row = test_utils.create_control_table_row(control_type_cell=control_type, strains_cell=strains)
        ip_table_controls.add_row(data_row)

        control_parser = ControlsTable(ip_table_controls, control_types={'HIGH_FITC'}, strain_mapping=self.strain_mappings)
        control_parser.process_table()
        control_result = control_parser.get_structured_request()
        
        measurement_parser = MeasurementTable(ip_table_measurment)
        measurement_parser.process_table(control_data={control_parser.get_table_caption(): control_result})
        meas_result = measurement_parser.get_structured_request()
        self.assertEqual(1, len(meas_result))
        self.assertEqual(1, len(meas_result[0][dc_constants.CONTROLS]))
        control = meas_result[0][dc_constants.CONTROLS][0]
        self.assertEqual(control[dc_constants.TYPE], 'HIGH_FITC')
        self.assertListEqual(control[dc_constants.STRAINS], [{dc_constants.LAB_ID: 'name.ip_admin.UWBF_7376',
                                                              dc_constants.LABEL: 'strain3',
                                                              dc_constants.SBH_URI: 'https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1'}])
    
    def test_table_with_2_reference_control_in_one_measurement(self):
        ip_measurement_table = test_utils.create_fake_measurement_table()
        controls = IntentParserCell()
        controls.add_paragraph('Table 1, Table 2')
        data_row = test_utils.create_measurement_table_row(controls_cell=controls)
        ip_measurement_table.add_row(data_row)

        ip_control_table1 = test_utils.create_fake_controls_table(1)
        control_type = IntentParserCell()
        control_type.add_paragraph('HIGH_FITC')
        strains = IntentParserCell()
        strains.add_paragraph('UWBF_7376', link='https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1')
        data_row = test_utils.create_control_table_row(control_type_cell=control_type, strains_cell=strains)
        ip_control_table1.add_row(data_row)

        ip_control_table2 = test_utils.create_fake_controls_table(1)
        control_type = IntentParserCell()
        control_type.add_paragraph('foo')
        strains = IntentParserCell()
        strains.add_paragraph('MG1655_LPV3', link='https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1')
        data_row = test_utils.create_control_table_row(control_type_cell=control_type, strains_cell=strains)
        ip_control_table2.add_row(data_row)

        control1_parser = ControlsTable(ip_control_table1, control_types={'HIGH_FITC'}, strain_mapping=self.strain_mappings)
        control1_parser.process_table()
        control1_result = control1_parser.get_structured_request()

        control2_parser = ControlsTable(ip_control_table2, control_types={'foo'}, strain_mapping=self.strain_mappings)
        control2_parser.process_table()
        control2_result = control2_parser.get_structured_request()
        
        measurement_parser = MeasurementTable(ip_measurement_table)
        measurement_parser.process_table(control_data={1: control1_result, 2: control2_result})
        meas_result = measurement_parser.get_structured_request()

        self.assertEqual(1, len(meas_result))
        self.assertEqual(2, len(meas_result[0]['controls']))
        
        control1 = meas_result[0][dc_constants.CONTROLS][0]
        self.assertEqual(control1[dc_constants.TYPE], 'HIGH_FITC')
        self.assertListEqual(control1[dc_constants.STRAINS], [{dc_constants.LAB_ID: 'name.ip_admin.UWBF_7376',
                                                              dc_constants.LABEL: 'strain3',
                                                              dc_constants.SBH_URI: 'https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1'}])

        control2 = meas_result[0][dc_constants.CONTROLS][1]
        self.assertEqual(control2[dc_constants.TYPE], 'foo')
        self.assertListEqual(control2[dc_constants.STRAINS], [{dc_constants.LAB_ID: 'name.ip_admin.MG1655_LPV3',
                                                              dc_constants.LABEL: 'strain2',
                                                              dc_constants.SBH_URI: 'https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1'}])
    
    def test_table_with_2_reference_control_in_seperate_measurements(self):
        ip_measurement_table = test_utils.create_fake_measurement_table()
        controls = IntentParserCell()
        controls.add_paragraph('Table 1')
        data_row = test_utils.create_measurement_table_row(controls_cell=controls)
        ip_measurement_table.add_row(data_row)

        controls = IntentParserCell()
        controls.add_paragraph('Table 2')
        data_row = test_utils.create_measurement_table_row(controls_cell=controls)
        ip_measurement_table.add_row(data_row)

        ip_control_table1 = test_utils.create_fake_controls_table(1)
        control_type = IntentParserCell()
        control_type.add_paragraph('HIGH_FITC')
        strains = IntentParserCell()
        strains.add_paragraph('UWBF_7376', link='https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1')
        data_row = test_utils.create_control_table_row(control_type_cell=control_type, strains_cell=strains)
        ip_control_table1.add_row(data_row)

        ip_control_table2 = test_utils.create_fake_controls_table(1)
        control_type = IntentParserCell()
        control_type.add_paragraph('foo')
        strains = IntentParserCell()
        strains.add_paragraph('MG1655_LPV3', link='https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1')
        data_row = test_utils.create_control_table_row(control_type_cell=control_type, strains_cell=strains)
        ip_control_table2.add_row(data_row)

        control1_parser = ControlsTable(ip_control_table1, control_types={'HIGH_FITC'}, strain_mapping=self.strain_mappings)
        control1_parser.process_table()
        control1_result = control1_parser.get_structured_request()

        control2_parser = ControlsTable(ip_control_table2, control_types={'foo'}, strain_mapping=self.strain_mappings)
        control2_parser.process_table()
        control2_result = control2_parser.get_structured_request()
        
        measurement_parser = MeasurementTable(ip_measurement_table)
        measurement_parser.process_table(control_data={1: control1_result, 2: control2_result})
        meas_result = measurement_parser.get_structured_request()

        self.assertEquals(2, len(meas_result))
        self.assertEquals(1, len(meas_result[0][dc_constants.CONTROLS]))
        
        control1 = meas_result[0][dc_constants.CONTROLS][0]
        self.assertEqual(control1[dc_constants.TYPE], 'HIGH_FITC')
        self.assertListEqual(control1[dc_constants.STRAINS], [{dc_constants.LAB_ID: 'name.ip_admin.UWBF_7376',
                                                              dc_constants.LABEL: 'strain3',
                                                              dc_constants.SBH_URI: 'https://hub.sd2e.org/user/sd2e/design/UWBF_7376/1'}])

        control2 = meas_result[1][dc_constants.CONTROLS][0]
        self.assertEqual(control2[dc_constants.TYPE], 'foo')
        self.assertListEqual(control2[dc_constants.STRAINS], [{dc_constants.LAB_ID: 'name.ip_admin.MG1655_LPV3',
                                                              dc_constants.LABEL: 'strain2',
                                                              dc_constants.SBH_URI: 'https://hub.sd2e.org/user/sd2e/design/MG1655_LPV3/1'}])
      
        
if __name__ == '__main__':
    unittest.main()