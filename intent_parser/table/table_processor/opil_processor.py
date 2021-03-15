from intent_parser.intent_parser_exceptions import DictionaryMaintainerException, IntentParserException, TableException
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

class OPILProcessor(Processor):
    """
    Generates opil from Intent Parser table templates.
    """

    logger = logging.getLogger('opil_processor')


    # units supported for opil conversion
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
                 protocol_factory,
                 sbol_dictionary,
                 file_types=[],
                 lab_names=[]):
        super().__init__()
        self._lab_names = lab_names
        self._protocol_factory = protocol_factory
        self._file_types = file_types
        self._sbol_dictionary = sbol_dictionary
        self._id_provider = IdProvider()

        self._experiment_ref = experiment_ref
        self._experiment_ref_url = experiment_ref_url
        self._experiment_id = None

        self.processed_lab_name = ''
        self.processed_protocol_name = ''
        self.processed_controls = {}
        self.process_measurements = []
        self.processed_parameter = None

        self.opil_document = opil.Document()

    def get_processed_controls(self, control_table_index):
        return self.processed_controls[control_table_index]

    def get_intent(self):
        return self.opil_document

    def process_intent(self, lab_tables=[], control_tables=[], parameter_tables=[], measurement_tables=[]):
        self._process_lab_tables(lab_tables)
        opil.set_namespace(self._get_namespace_from_lab())
        self._protocol_factory.set_selected_lab(self.processed_lab_name)
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

        try:
            self._process_opil_output()
        except IntentParserException as err:
            self.validation_errors.append(err.get_message())

    def _get_namespace_from_lab(self):
        if self.processed_lab_name == dc_constants.LAB_TRANSCRIPTIC:
            return ip_constants.STRATEOS_NAMESPACE

        return ip_constants.SD2E_NAMESPACE

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
            lab_table = LabTable(intent_parser_table=table, lab_names=self._lab_names)
            lab_table.process_table()

        processed_lab = lab_table.get_intent()
        self.processed_lab_name = processed_lab.get_lab_name()
        self._experiment_id = processed_lab.to_structured_request()[dc_constants.EXPERIMENT_ID]
        self.validation_errors.extend(lab_table.get_validation_errors())
        self.validation_warnings.extend(lab_table.get_validation_warnings())

    def _process_opil_output(self):
        if not self._protocol_factory.support_lab(self.processed_lab_name):
            raise IntentParserException('lab %s not supported for exporting opil metadata.' % self.processed_lab_name)

        opil_experimental_result = opil.ExperimentalRequest(self._id_provider.get_unique_sd2_id())
        opil_experimental_result.name = 'Experimental Request'
        self._annotate_experimental_id(opil_experimental_result)
        self._annotate_experimental_reference(opil_experimental_result)
        self._annotate_experimental_reference_url(opil_experimental_result)

        opil_measurements = []
        opil_measurement_types = []

        for measurement_intent in self.process_measurements:
            opil_measurement, measurement_type = measurement_intent.to_opil()
            opil_measurement_types.append(measurement_type)
            opil_measurements.append(opil_measurement)
            measurement_intent.to_sbol_combinatorial_derivation(self.opil_document)

        if len(opil_measurements) > 0:
            opil_experimental_result.measurements = opil_measurements

        if self.processed_parameter:
            if self.processed_parameter.get_protocol_name() is None:
                raise IntentParserException('Unable to process parameter for opil: missing protocol name')
            parameter_fields_from_lab = self._protocol_factory.map_parameter_values(self.processed_parameter.get_protocol_name())

            run_param_fields, run_param_values = self.processed_parameter.to_opil_for_experiment()
            default_param_fields, default_param_values = self._process_default_parameters_as_opil(self.processed_parameter.get_default_parameters(),
                                                                                                  parameter_fields_from_lab,
                                                                                                  self.opil_document)

            all_param_values = run_param_values + default_param_values
            if len(all_param_values) > 0:
                opil_experimental_result.has_parameter_value = all_param_values

            all_param_fields = run_param_fields + default_param_fields
            opil_protocol_interface = self._protocol_factory.get_protocol_interface(self.processed_parameter.get_protocol_name())
            copied_protocol_interface = opil_protocol_interface.copy(self.opil_document)
            if len(all_param_fields) > 0:
                copied_protocol_interface.has_parameter = all_param_fields
            if len(opil_measurement_types) > 0:
                copied_protocol_interface.protocol_measurement_type = opil_measurement_types

        self.opil_document.add(opil_experimental_result)
        validation_report = self.opil_document.validate()
        if not validation_report.is_valid:
            raise IntentParserException(validation_report.message)

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

        sample_combinations = CombinatorialDerivation(identity=self._id_provider.get_unique_sd2_id(),
                                                      template=sbol_measurement_template)
        sample_combinations.variable_features = all_sample_variables
        self.opil_document.add(sample_combinations)
        return sample_combinations

    def _validate_parameters_from_lab(self, parameter_fields_from_document, parameter_fields_from_lab):
        # Check for required fields.
        is_valid = True
        for field in parameter_fields_from_lab.values():
            if field.is_required() and field.get_field_name() not in parameter_fields_from_document:
                self.validation_errors.append('missing required parameter field %s' % field.get_field_name())
                is_valid = False
        # Check for valid values.
        for name, value in parameter_fields_from_document.items():
            if name not in parameter_fields_from_lab:
                is_valid = False
                self.validation_errors.append('%s is not a supported parameter field for protocol %s' %(name, self.processed_parameter.get_protocol_name()))
            elif not parameter_fields_from_lab[name].is_valid_value(value):
                is_valid = False
                self.validation_errors.append('%s is not a valid parameter value for parameter field %s' % (
                                                value, name))
        return is_valid

    def _process_default_parameters_as_opil(self,
                                            parameter_fields_from_document,
                                            parameter_fields_from_lab,
                                            opil_document):
        opil_param_values = []
        opil_param_fields = []
        if not self._validate_parameters_from_lab(parameter_fields_from_document, parameter_fields_from_lab):
            raise IntentParserException('Failed to validate parameters for protocol.')

        for param_key, param_value in parameter_fields_from_document.items():
            param_field = parameter_fields_from_lab[param_key].get_opil_template()

            value_id = self._id_provider.get_unique_sd2_id()
            opil_param_field = param_field.copy(opil_document)
            opil_param_fields.append(opil_param_field)
            if type(param_field) is opil.BooleanParameter:
                boolean_value = cell_parser.PARSER.process_boolean_flag(param_value)
                opil_value = opil_utils.create_opil_boolean_parameter_value(value_id, boolean_value[0])
                opil_value.value_of = opil_param_field
                opil_param_values.append(opil_value)

            elif type(param_field) is opil.EnumeratedParameter:
                opil_value = opil_utils.create_opil_enumerated_parameter_value(value_id, param_value)
                opil_value.value_of = param_field
                opil_param_values.append(opil_value)

            elif type(param_field) is opil.IntegerParameter:
                int_value = cell_parser.PARSER.process_numbers(param_value)
                opil_value = opil_utils.create_opil_integer_parameter_value(value_id, int(int_value[0]))
                opil_value.value_of = opil_param_field
                opil_param_values.append(opil_value)

            elif type(param_field) is opil.MeasureParameter:
                if cell_parser.PARSER.is_number(param_value):
                    value = cell_parser.PARSER.process_numbers(param_value)
                    opil_value = opil_utils.create_opil_measurement_parameter_value(value_id, float(value[0]))
                    opil_value.value_of = opil_param_field
                    opil_param_values.append(opil_value)
                elif cell_parser.PARSER.is_valued_cell(param_value):
                    value, unit = cell_parser.PARSER.process_value_unit_without_validation(param_value)
                    opil_value = opil_utils.create_opil_measurement_parameter_value(value_id, float(value), unit)
                    opil_value.value_of = opil_param_field
                    opil_param_values.append(opil_value)
                else:
                    self.validation_errors.append('Unable to create an OPIL Measurement ParameterValue. '
                                                  'Expecting to get a  numerical value or a numerical value '
                                                  'followed by a unit but got %s' % param_value)

            elif type(param_field) is opil.StringParameter:
                opil_value = opil_utils.create_opil_string_parameter_value(value_id, param_value)
                opil_value.value_of = opil_param_field
                opil_param_values.append(opil_value)

            elif type(param_field) is opil.URIParameter:
                opil_value = opil_utils.create_opil_URI_parameter_value(value_id, param_value)
                opil_value.value_of = opil_param_field
                opil_param_values.append(opil_value)

        return opil_param_fields, opil_param_values

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
            self._encode_measurement_table(measurement_table)

            self.process_measurements.append(measurement_table)
            self.validation_warnings.extend(measurement_table.get_validation_warnings())
            self.validation_errors.extend(measurement_table.get_validation_errors())

        except (DictionaryMaintainerException, TableException, IntentParserException) as err:
            self.validation_errors.extend([err.get_message()])

    def _encode_measurement_table(self, measurement_table):
        batch_template = None
        col_id_template = None
        control_template = None
        dna_reaction_concentration_template = None
        lab_id_template = None
        media_template = None
        num_neg_control_template = None
        ods_template = None
        row_id_template = None
        strains_template = None
        template_dna_template = None
        use_rna_inhib_template = None

        all_sample_templates = []
        if measurement_table.has_batch():
            batch_template = self._create_batch_template()
            all_sample_templates.append(batch_template)
        if measurement_table.has_column_id():
            col_id_template = self._create_column_id_template()
            all_sample_templates.append(col_id_template)
        if measurement_table.has_control():
            control_template = self._create_control_template()
            all_sample_templates.append(control_template)
        if measurement_table.has_dna_reaction_concentration():
            dna_reaction_concentration_template = self._create_dna_reaction_concentration_template()
            all_sample_templates.append(dna_reaction_concentration_template)
        if measurement_table.has_lab_id():
            lab_id_template = self._create_lab_id_template()
            all_sample_templates.append(lab_id_template)
        if measurement_table.has: # todo
            media_template = self._create_media_template(measurement_table.get_processed_reagents_and_medias())
            all_sample_templates.append(media_template)
        if measurement_table.has_number_of_negative_controls():
            num_neg_control_template = self._create_num_neg_control_template()
            all_sample_templates.append(num_neg_control_template)
        if measurement_table.has_ods():
            ods_template = self._create_ods_template()
            all_sample_templates.append(ods_template)
        if measurement_table.has_row_id():
            row_id_template = self._create_row_id_template()
            all_sample_templates.append(row_id_template)
        if measurement_table.has_rna_inhibitor():
            use_rna_inhib_template = self._create_use_rna_inhib_template()
            all_sample_templates.append(use_rna_inhib_template)
        if measurement_table.has_strains():
            strains_template = self._get_or_create_strains_template()
            all_sample_templates.append(strains_template)
        if measurement_table.has_template_dna():
            template_dna_template = self._create_template_dna_template()
            all_sample_templates.append(template_dna_template)

        sample_template = Component(identity=self._id_provider.get_unique_sd2_id(),
                                    component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        sample_template.features = all_sample_templates
        for measurement_intent in measurement_table.get_intents():
            measurement_combinatorial_derivation = self._create_combinatorial_derivation_from_measurement_intent(measurement_intent,
                                                                          sample_template,
                                                                          batch_template=batch_template,
                                                                          column_id_template=col_id_template,
                                                                          control_template=control_template,
                                                                          dna_reaction_concentration_template=dna_reaction_concentration_template,
                                                                          lab_id_template=lab_id_template,
                                                                          media_template=media_template,
                                                                          num_neg_control_template=num_neg_control_template,
                                                                          ods_template=ods_template,
                                                                          row_id_template=row_id_template,
                                                                          strains_template=strains_template,
                                                                          template_dna_template=template_dna_template,
                                                                          use_rna_inhib_template=use_rna_inhib_template)
            # todo
            # file_types -> opil.Measurement
            # measurement_type -> opil.MeasurementType
            # replicates -> opil.SampleSet
            # timepoints -> opil.Measure
        self.opil_document.add(sample_template)


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

            self.processed_parameter = parameter_table.get_parameter_intent()

        except (DictionaryMaintainerException, IntentParserException, TableException) as err:
            self.validation_errors.extend([err.get_message()])

