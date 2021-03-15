from intent_parser.intent_parser_exceptions import DictionaryMaintainerException, IntentParserException, TableException
from intent_parser.protocols.templates.experimental_request_template import ExperimentalRequest, OpilComponentTemplate
from intent_parser.table.controls_table import ControlsTable
from intent_parser.table.lab_table import LabTable
from intent_parser.table.measurement_table import MeasurementTable
from intent_parser.table.parameter_table import ParameterTable
from intent_parser.table.table_processor.processor import Processor
from intent_parser.utils.id_provider import IdProvider
from sbol3 import CombinatorialDerivation, Component, TextProperty, LocalSubComponent
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.utils.opil_utils as opil_utils
import intent_parser.table.cell_parser as cell_parser
import logging
import opil
import sbol3.constants as sbol_constants


class OpilProcessor2(Processor):

    logger = logging.getLogger('opil_processor')
    _CONTROL_TYPES = ['HIGH_FITC',
                      'EMPTY_VECTOR',
                      'BASELINE',
                      'TREATMENT_1',
                      'TREATMENT_2',
                      'BASELINE_MEDIA_PR',
                      'CELL_DEATH_NEG_CONTROL',
                      'CELL_DEATH_POS_CONTROL']

    _FLUID_UNITS = ['%',
                    'M',
                    'mM',
                    'X',
                    'g/L',
                    'ug/ml',
                    'micromole',
                    'nM',
                    'uM',
                    'mg/ml',
                    'ng/ul']

    _TIME_UNITS = [ip_constants.TIME_UNIT_DAY,
                   ip_constants.TIME_UNIT_HOUR,
                   ip_constants.TIME_UNIT_FEMTOSECOND,
                   ip_constants.TIME_UNIT_MICROSECOND,
                   ip_constants.TIME_UNIT_MILLISECOND,
                   ip_constants.TIME_UNIT_MINUTE,
                   ip_constants.TIME_UNIT_MONTH,
                   ip_constants.TIME_UNIT_NANOSECOND,
                   ip_constants.TIME_UNIT_PICOSECOND,
                   ip_constants.TIME_UNIT_SECOND,
                   ip_constants.TIME_UNIT_WEEK,
                   ip_constants.TIME_UNIT_YEAR]

    _MEASUREMENT_TYPE = [ip_constants.MEASUREMENT_TYPE_FLOW,
                         ip_constants.MEASUREMENT_TYPE_RNA_SEQ,
                         ip_constants.MEASUREMENT_TYPE_DNA_SEQ,
                         ip_constants.MEASUREMENT_TYPE_PROTEOMICS,
                         ip_constants.MEASUREMENT_TYPE_SEQUENCING_CHROMATOGRAM,
                         ip_constants.MEASUREMENT_TYPE_AUTOMATED_TEST,
                         ip_constants.MEASUREMENT_TYPE_CFU,
                         ip_constants.MEASUREMENT_TYPE_PLATE_READER,
                         ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE,
                         ip_constants.MEASUREMENT_TYPE_EXPERIMENTAL_DESIGN]

    def __init__(self,
                 experiment_ref,
                 experiment_ref_url,
                 lab_protocol_accessor,
                 sbol_dictionary,
                 file_types=[],
                 lab_names=[]):
        super().__init__()
        self.processed_lab_name = ''
        self.processed_protocol_name = ''
        self.processed_controls = {}
        self.process_measurements = []
        self.processed_parameter = None
        self._experiment_id = None
        self._experiment_ref = experiment_ref
        self._experiment_ref_url = experiment_ref_url
        self._file_types = file_types
        self._sbol_dictionary = sbol_dictionary
        self._lab_protocol_accessor = lab_protocol_accessor
        self._lab_names = lab_names
        self._id_provider = IdProvider()

    def process_intent(self, lab_tables=[], control_tables=[], parameter_tables=[], measurement_tables=[]):
        self._process_tables(lab_tables, control_tables, parameter_tables, measurement_tables)
        self._process_opil()

    def _process_tables(self, lab_tables, control_tables, parameter_tables, measurement_tables):
        self._process_lab_tables(lab_tables)
        opil.set_namespace(self._get_namespace_from_lab())
        self._lab_protocol_accessor.set_selected_lab(self.processed_lab_name)
        strain_mapping = self._sbol_dictionary.get_mapped_strain(self.processed_lab_name)

        if len(control_tables) == 0:
            self.validation_warnings.append('No control tables to parse from document.')
        else:
            self._process_control_tables(control_tables, strain_mapping)

        if len(measurement_tables) == 0:
            self.validation_errors.append('Unable to generate opil: No measurement table to parse from document.')
        else:
            self._process_measurement_tables(measurement_tables, strain_mapping)

        if len(parameter_tables) == 0:
            self.validation_errors.append('Unable to generate opil: No parameter table to parse from document.')
        else:
            self._process_parameter_tables(parameter_tables)

    def _process_opil(self):
        opil_component_template = OpilComponentTemplate()
        opil_component_template.load_from_measurement_table(self.measurement_table)

        opil_lab_template = self._lab_protocol_accessor.load_experimental_protocol_from_lab(self.processed_protocol_name)
        experimental_request = ExperimentalRequest(self._get_namespace_from_lab(),
                                                   opil_lab_template,
                                                   opil_component_template)
        opil_experimental_request = experimental_request.get_or_add_experimental_request()
        self._annotate_experimental_id(opil_experimental_request)
        self._annotate_experimental_reference(opil_experimental_request)
        self._annotate_experimental_reference_url(opil_experimental_request)

        experimental_request.create_components_from_template()
        sample_template = Component(identity=self._id_provider.get_unique_sd2_id(),
                                    component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        sample_template.features = all_sample_templates
        for measurement_intent in self.measurement_table.get_intents():
            sample_combinations = CombinatorialDerivation(identity=self._id_provider.get_unique_sd2_id(),
                                                          template=sample_template)
            all_sample_variables = self._create_combinatorial_derivation_from_measurement_intent(measurement_intent,)
            sample_combinations.variable_features = all_sample_variables
            self.opil_document.add(sample_combinations)

    def _annotate_experimental_id(self, opil_experimental_result):
        opil_experimental_result.experiment_id = TextProperty(opil_experimental_result,
                                                  '%s#%s' % (ip_constants.SD2E_NAMESPACE, dc_constants.EXPERIMENT_ID),
                                                  0,
                                                  1)
        opil_experimental_result.experiment_id = self._experiment_id

    def _annotate_experimental_reference(self, opil_experimental_result):
        opil_experimental_result.experiment_reference = TextProperty(opil_experimental_result,
                                                  '%s#%s' % (ip_constants.SD2E_NAMESPACE, dc_constants.EXPERIMENT_REFERENCE),
                                                  0,
                                                  1)
        opil_experimental_result.experiment_reference = self._experiment_ref

    def _annotate_experimental_reference_url(self, opil_experimental_result):
        opil_experimental_result.experiment_reference_url = TextProperty(opil_experimental_result,
                                                  '%s#%s' % (ip_constants.SD2E_NAMESPACE, dc_constants.EXPERIMENT_REFERENCE_URL),
                                                  0,
                                                  1)
        opil_experimental_result.experiment_reference_url = self._experiment_ref_url

    def _create_combinatorial_derivation_from_measurement_intent(self,
                                                                 measurement_intent,
                                                                 sbol_measurement_template,
                                                                 batch_template=None,
                                                                 column_id_template=None,
                                                                 control_template=None,
                                                                 dna_reaction_concentration_template=None,
                                                                 lab_id_template=None,
                                                                 media_template=None,
                                                                 num_neg_control_template=None,
                                                                 ods_template=None,
                                                                 row_id_template=None,
                                                                 strains_template=None,
                                                                 template_dna_template=None,
                                                                 use_rna_inhib_template=None):
        all_sample_variables = []
        if measurement_intent.size_of_batches() > 0 and batch_template:
            batch_variable = measurement_intent.batch_values_to_sbol_variable_feature(batch_template)
            all_sample_variables.append(batch_variable)

        if not measurement_intent.contents_is_empty():
            measurement_contents = measurement_intent.get_contents()
            for content in measurement_contents.get_contents():
                # column_id
                if content.size_of_column_id() > 0 and column_id_template:
                    col_id_variable = content.col_id_values_to_sbol_variable_feature(self.opil_document,
                                                                                     column_id_template)
                    all_sample_variables.append(col_id_variable)
                # dna_reaction_concentration
                if content.size_of_dna_reaction_concentrations() > 0 and dna_reaction_concentration_template:
                    dna_reaction_concentration_variable = content.dna_reaction_concentration_values_to_sbol_variable_feature(self.opil_document,
                                                                                                                             dna_reaction_concentration_template)
                    all_sample_variables.append(dna_reaction_concentration_variable)
                # lab_id
                if content.size_of_lab_ids() > 0 and lab_id_template:
                    lab_id_variable = content.lab_id_values_to_sbol_variable_feature(self.opil_document,
                                                                                     lab_id_template)
                    all_sample_variables.append(lab_id_variable)
                # media
                if content.size_of_medias() > 0:
                    pass # todo
                # number_of_negative_controls
                if content.size_of_num_of_neg_controls() > 0 and num_neg_control_template:
                    num_neg_control_variable = content.number_of_negative_control_values_to_sbol_variable_feature(self.opil_document,
                                                                                                                  num_neg_control_template)
                    all_sample_variables.append(num_neg_control_variable)
                # row_id
                if content.size_of_row_ids() > 0 and row_id_template:
                    row_id_variable = content.row_id_values_to_sbol_variable_feature(self.opil_document,
                                                                                     row_id_template)
                    all_sample_variables.append(row_id_variable)
                # rna_inhibitor
                if content.size_of_rna_inhibitor_flags() > 0 and use_rna_inhib_template:
                    use_rna_inhib_variable = content.use_rna_inhibitor_values_to_sbol_variable_feature(self.opil_document,
                                                                                                       use_rna_inhib_template)
                    all_sample_variables.append(use_rna_inhib_variable)
                # template_dna
                if content.size_of_template_dna_values() > 0 and template_dna_template:
                    template_dna_variable = content.template_dna_values_to_sbol_variable_feature(self.opil_document,
                                                                                                 template_dna_template)
                    all_sample_variables.append(template_dna_variable)
                # reagent
                if content.size_of_reagents() > 0:
                    pass # todo
        # control
        if measurement_intent.size_of_controls() > 0 and control_template:
            control_variable = measurement_intent.control_to_sbol_variable_feature(self.opil_document, control_template)
            all_sample_variables.append(control_variable)

        # ods
        if measurement_intent.size_of_optical_density() > 0 and ods_template:
            optical_density_variable = measurement_intent.optical_density_values_to_sbol_variable_feature(ods_template)
            all_sample_variables.append(optical_density_variable)
        # strains
        if measurement_intent.size_of_strains() > 0 and strains_template:
            strains_variables = measurement_intent.strain_values_to_sbol_variable_feature(strains_template)
            all_sample_variables.append(strains_variables)
        # temperature
        if measurement_intent.size_of_temperatures() > 0:
            if media_template:
                temperature_variable = measurement_intent.temperature_values_to_sbol_variable_feature(media_template)
                all_sample_variables.append(temperature_variable)
            else:
                self.validation_warnings.append('Skip opil encoding for temperatures since no media template to assign '
                                                'temperature values to.')
        return all_sample_variables

    def _get_namespace_from_lab(self):
        if self.processed_lab_name == dc_constants.LAB_TRANSCRIPTIC:
            return ip_constants.STRATEOS_NAMESPACE
        elif self.processed_lab_name == dc_constants.LAB_DUKE_HAASE:
            return 'http://aquarium.bio/'

        return ip_constants.SD2E_NAMESPACE

    def _process_opil_output(self, opil):
        pass

    def _process_control_tables(self, control_tables, strain_mapping):
        if not control_tables:
            self.validation_errors.append('No control tables to parse from document.')
            return
        try:
            for table in control_tables:
                controls_table = ControlsTable(table,
                                               control_types=self._CONTROL_TYPES,
                                               fluid_units=self._FLUID_UNITS,
                                               timepoint_units=self._TIME_UNITS,
                                               strain_mapping=strain_mapping)
                controls_table.process_table()
                table_caption = controls_table.get_table_caption()
                control_intents = controls_table.get_intents()
                if table_caption:
                    self.processed_controls[table_caption] = control_intents

                self.validation_errors.extend(controls_table.get_validation_errors())
                self.validation_warnings.extend(controls_table.get_validation_warnings())
        except IntentParserException as err:
            self.validation_errors.extend([err.get_message()])

    def _process_lab_tables(self, lab_tables):
        if len(lab_tables) == 0:
            message = 'No lab table specified in this experiment. Generated default values for lab contents.'
            self.logger.warning(message)
            lab_table = LabTable()
        else:
            if len(lab_tables) > 1:
                message = ('There are more than one lab table specified in this experiment.'
                           'Only the last lab table identified in the document will be used for generating a request.')
                self.validation_warnings.extend([message])

            table = lab_tables[-1]
            lab_table = LabTable(intent_parser_table=table,
                                 lab_names=self._lab_names)
            lab_table.process_table()

        processed_lab = lab_table.get_intent()
        self.processed_lab_name = processed_lab.get_lab_name()
        self._experiment_id = processed_lab.to_structured_request()[dc_constants.EXPERIMENT_ID]
        self.validation_errors.extend(lab_table.get_validation_errors())
        self.validation_warnings.extend(lab_table.get_validation_warnings())

    def _process_measurement_tables(self, measurement_tables, strain_mapping):
        if len(measurement_tables) > 1:
            message = ('There are more than one measurement table specified in this experiment.'
                       'Only the last measurement table identified in the document will be used for generating a request.')
            self.validation_warnings.extend([message])
        try:
            table = measurement_tables[-1]
            measurement_table = MeasurementTable(table,
                                                 temperature_units=list(ip_constants.TEMPERATURE_UNIT_MAP.keys()),
                                                 timepoint_units=list(ip_constants.TIME_UNIT_MAP.keys()),
                                                 fluid_units=list(ip_constants.FLUID_UNIT_MAP.keys()),
                                                 measurement_types=self._MEASUREMENT_TYPE,
                                                 file_type=self._file_types,
                                                 strain_mapping=strain_mapping)

            measurement_table.process_table(control_data=self.processed_controls)

            self.measurement_table = measurement_table
            self.validation_warnings.extend(measurement_table.get_validation_warnings())
            self.validation_errors.extend(measurement_table.get_validation_errors())

        except (DictionaryMaintainerException, TableException, IntentParserException) as err:
            self.validation_errors.extend([err.get_message()])

    def _process_parameter_tables(self, parameter_tables):
        if len(parameter_tables) > 1:
            message = ('There are more than one parameter table specified in this experiment.'
                       'Only the last parameter table identified in the document will be used for generating opil.')
            self.validation_warnings.extend([message])
        try:
            table = parameter_tables[-1]
            parameter_table = ParameterTable(table, run_as_opil=True)
            parameter_table.process_table()

            self.validation_warnings.extend(parameter_table.get_validation_warnings())
            self.validation_errors.extend(parameter_table.get_validation_errors())
            processed_parameter_intent = parameter_table.get_parameter_intent()
            self.processed_parameter = processed_parameter_intent
            self.processed_protocol_name = processed_parameter_intent.get_protocol_name()

        except (DictionaryMaintainerException, IntentParserException, TableException) as err:
            self.validation_errors.extend([err.get_message()])


