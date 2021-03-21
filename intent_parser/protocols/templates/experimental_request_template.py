from intent_parser.intent.measure_property_intent import ReagentIntent, MediaIntent
from intent_parser.intent.parameter_intent import ParameterIntent
from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.table.controls_table import ControlsTable
from intent_parser.table.measurement_table import MeasurementTable
from intent_parser.table.parameter_table import ParameterTable
from intent_parser.utils.id_provider import IdProvider
from sbol3 import SubComponent, TextProperty, LocalSubComponent
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.utils.opil_utils as opil_utils
import opil
import sbol3.constants as sbol_constants
import tyto

class OpilDocumentTemplate(object):
    def __init__(self):
        self.opil_components = []
        self.opil_sample_sets = []
        self.opil_experimental_requests = []
        self.opil_protocol_interfaces = []

    def get_components(self):
        return self.opil_components

    def get_sample_sets(self):
        return self.opil_sample_sets

    def get_experimental_requests(self):
        return self.opil_experimental_requests

    def get_protocol_interfaces(self):
        return self.opil_protocol_interfaces

    def load_from_template(self, template: opil.Document):
        for top_level in template.objects:
            if type(top_level) == opil.Component:
                self.opil_components.append(top_level)
            elif type(top_level) == opil.SampleSet:
                self.opil_sample_sets.append(top_level)
            elif type(top_level) == opil.ExperimentalRequest:
                self.opil_experimental_requests.append(top_level)
            elif type(top_level) == opil.ProtocolInterface:
                self.opil_protocol_interfaces.append(top_level)

class OpilParameterTemplate(object):
    def __init__(self):
        self.parameter = None
        self.parameter_value = None

class OpilControlTemplate(object):
    def __init__(self):
        self.strains_template = None
        self.contents_template = None

    def load_from_control_table(self, control_table: ControlsTable):
        if control_table.has_contents():
            self.contents_template = ip_constants.HEADER_CONTENTS_VALUE
        if control_table.has_strains():
            self.strains_template = ip_constants.HEADER_STRAINS_VALUE

class OpilMeasurementTemplate(object):
    def __init__(self):
        self.batch_template = None
        self.column_id_template = None
        self.control_template = None
        self.dna_reaction_concentration_template = None
        self.lab_id_template = None
        self.media_and_reagent_templates = []
        self.num_neg_control_template = None
        self.ods_template = None
        self.replicate_template = None
        self.row_id_template = None
        self.strains_template = None
        self.template_dna_template = None
        self.use_rna_inhib_template = None

    def load_from_measurement_table(self, measurement_table: MeasurementTable):
        if measurement_table.has_batch():
            self.batch_template = ip_constants.HEADER_BATCH_VALUE
        if measurement_table.has_column_id():
            self.column_id_template = ip_constants.HEADER_COLUMN_ID_VALUE
        if measurement_table.has_control():
            self.control_template = ip_constants.HEADER_CONTROL_TYPE_VALUE
        if measurement_table.has_dna_reaction_concentration():
            self.dna_reaction_concentration_template = ip_constants.HEADER_DNA_REACTION_CONCENTRATION_VALUE
        if measurement_table.has_lab_id():
            self.lab_id_template = ip_constants.HEADER_LAB_ID_VALUE
        if measurement_table.has_medias_and_reagents():
            self.media_and_reagent_templates.extend(measurement_table.get_processed_reagents_and_medias())
        if measurement_table.has_number_of_negative_controls():
            self.num_neg_control_template = ip_constants.HEADER_NUMBER_OF_NEGATIVE_CONTROLS_VALUE
        if measurement_table.has_ods():
            self.ods_template = ip_constants.HEADER_ODS_VALUE
        if measurement_table.has_replicate():
            self.replicate_template = ip_constants.HEADER_REPLICATE_VALUE
        if measurement_table.has_row_id():
            self.row_id_template = ip_constants.HEADER_ROW_ID_VALUE
        if measurement_table.has_rna_inhibitor():
            self.use_rna_inhib_template = ip_constants.HEADER_USE_RNA_INHIBITOR_IN_REACTION_VALUE
        if measurement_table.has_strains():
            self.strains_template = ip_constants.HEADER_STRAINS_VALUE
        if measurement_table.has_template_dna():
            self.template_dna_template = ip_constants.HEADER_TEMPLATE_DNA_VALUE


class ExperimentalRequest(object):
    """An experimental request is ..."""
    def __init__(self,
                 lab_namespace: str,
                 template: OpilDocumentTemplate,
                 experiment_id: str,
                 experiment_ref: str,
                 experiment_ref_url: str):
        self.opil_components = [component.copy() for component in template.get_components()]
        self.opil_sample_sets = [component.copy() for component in template.get_sample_sets()]
        self.opil_experimental_requests = [component.copy() for component in template.get_experimental_requests()]
        self.opil_protocol_interfaces = [component.copy() for component in template.get_protocol_interfaces()]
        self._experiment_id = experiment_id
        self._experiment_ref = experiment_ref
        self._experiment_ref_url = experiment_ref_url
        self._lab_namespace = lab_namespace
        self._opil_component_template = OpilMeasurementTemplate()
        self._id_provider = IdProvider()

        self.batch_template = None
        self.column_id_template = None
        self.control_template = None
        self.dna_reaction_concentration_template = None
        self.lab_id_template = None
        self.media_template = None
        self.num_neg_control_template = None
        self.ods_template = None
        self.replicate_template = None
        self.row_id_template = None
        self.strain_template = None
        self.template_dna_template = None
        self.use_rna_inhib_template = None
        self.media_and_reagents_templates = {}
        self.sample_template = None
        self.lab_field_id_to_values = {}

    def add_variable_features_from_measurement_intents(self, measurement_intents):
        for index in range(len(measurement_intents)):
            measurement_intent = measurement_intents[index]
            sample_set = self.opil_sample_sets[index]
            all_sample_variables = self._create_sample_variables_from_measurement_intent(measurement_intent)
            sample_set.variable_features = all_sample_variables

    def add_new_parameters(self, run_parameter_fields, run_parameter_values):
        if not self.opil_protocol_interfaces:
            self.opil_protocol_interfaces.append(opil.ProtocolInterface(identity=self._id_provider.get_unique_sd2_id()))
        elif len(self.opil_protocol_interfaces) > 1:
            raise IntentParserException('expecting 1 but got %d opil.ProtocolInterface.' % len(self.opil_protocol_interfaces))

        if len(self.opil_experimental_requests) != 1:
            raise IntentParserException(
                'expecting 1 but got %d opil.ExperimentalRequest.' % len(self.opil_experimental_requests))

        opil_protocol_inteface = self.opil_protocol_interfaces[0]
        opil_experimental_request = self.opil_experimental_requests[0]
        opil_protocol_inteface.parameter.has_parameter.extend(run_parameter_fields)
        opil_experimental_request.has_parameter_value.extend(run_parameter_values)

    def create_components_from_control_template(self, control_template: OpilControlTemplate):
        if control_template.contents_template:
            content_template = self._create_opil_local_subcomponent(control_template.contents_template)
        if control_template.strains_template:
            strain_template = self._create_opil_local_subcomponent(control_template.strains_template)

    def create_components_from_template(self):
        if self._opil_component_template.batch_template:
            self.batch_template = self._create_opil_local_subcomponent(self._opil_component_template.batch_template)
        if self._opil_component_template.column_id_template:
            self.col_id_template = self._create_opil_local_subcomponent(self._opil_component_template.column_id_template)
        if self._opil_component_template.control_template:
            self.control_template = self._create_opil_local_subcomponent(self._opil_component_template.control_template)
        if self._opil_component_template.dna_reaction_concentration_template:
            self.dna_reaction_concentration_template = self._create_opil_local_subcomponent(self._opil_component_template.dna_reaction_concentration_template)
        if self._opil_component_template.lab_id_template:
            self.lab_id_template = self._create_opil_local_subcomponent(self._opil_component_template.lab_id_template)
        if self._opil_component_template.num_neg_control_template:
            self.num_neg_control_template = self._create_opil_local_subcomponent(self._opil_component_template.num_neg_control_template)
        if self._opil_component_template.ods_template:
            self.ods_template = self._create_opil_local_subcomponent(self._opil_component_template.ods_template)
        if self._opil_component_template.replicate_template:
            self.replicate_template = self._create_opil_local_subcomponent(self._opil_component_template.replicate_template)
        if self._opil_component_template.row_id_template:
            self.row_id_template = self._create_opil_local_subcomponent(self._opil_component_template.row_id_template)
        if self._opil_component_template.use_rna_inhib_template:
            self.use_rna_inhib_template = self._create_opil_local_subcomponent(self._opil_component_template.use_rna_inhib_template)
        if self._opil_component_template.template_dna_template:
            self.template_dna_template = self._create_opil_local_subcomponent(self._opil_component_template.template_dna_template)

        self._load_strain_template()
        self._load_reagent_and_media_templates()

    def load_lab_parameters(self):
        if not self.opil_protocol_interfaces:
            raise IntentParserException('ExperimentalRequest does not a opil ProtocolInterface.')
        elif len(self.opil_protocol_interfaces) > 1:
            raise IntentParserException('expecting 1 but got %d opil ProtocolInterface.' % len(self.opil_protocol_interfaces))

        if len(self.opil_experimental_requests) != 1:
            raise IntentParserException(
                'expecting 1 but got %d opil.ExperimentalRequest.' % len(self.opil_experimental_requests))

        opil_protocol_interface = self.opil_protocol_interfaces[0]
        opil_experimental_request = self.opil_experimental_requests[0]
        for parameter in opil_protocol_interface.parameter.has_parameter:
            opil_parameter_template = OpilParameterTemplate()
            opil_parameter_template.parameter = parameter
            self.lab_field_id_to_values[parameter.identity] = opil_parameter_template

        for parameter_value in opil_experimental_request.has_parameter_value:
            parameter_id = parameter_value.value_of
            if parameter_id not in self.lab_field_id_to_values:
                raise IntentParserException('opil.ParameterValue %s points to an unknown parameter %s'
                                            % (parameter_value.identity, parameter_id))
            self.lab_field_id_to_values[parameter_id].parameter_value = parameter_value

    def load_experimental_request(self):
        if len(self.opil_experimental_requests) == 0:
            self.opil_experimental_requests.append(opil.ExperimentalRequest(self._id_provider.get_unique_sd2_id()))
        elif len(self.opil_experimental_requests) > 1:
            raise IntentParserException('expecting 1 but got %d opil.ExperimentalRequest.' % len(self.opil_experimental_requests))
        opil_experimental_request = self.opil_experimental_requests[0]
        self._annotate_experimental_id(opil_experimental_request)
        self._annotate_experimental_reference(opil_experimental_request)
        self._annotate_experimental_reference_url(opil_experimental_request)

    def load_from_measurement_table(self, measurement_table):
        self._opil_component_template.load_from_measurement_table(measurement_table)

    def load_measurement(self, measurement_intents):
        if not self.opil_experimental_requests:
            raise IntentParserException('No experimental request found.')
        opil_experimental_request = self.opil_experimental_requests[0]
        if len(opil_experimental_request.measurements) == 0:
            # create opil
            opil_measurement = opil.Measurement(self._id_provider.get_unique_sd2_id())
        elif len(opil_experimental_request.measurements) == len(measurement_intents):
            pass

    def load_sample_set(self, number_of_sample_sets):
        sample_set = None
        if len(self.opil_sample_sets) == 1:
            sample_set = self.opil_sample_sets[0]
        elif len(self.opil_sample_sets) == 0:
            sample_set = opil.SampleSet(identity=self._id_provider.get_unique_sd2_id(),
                                        template=self.sample_template)
        else:
            raise IntentParserException('More than one SampleSet found from lab protocol.')

        while len(self.opil_sample_sets) < number_of_sample_sets:
            self.opil_sample_sets.append(sample_set.copy())

    def load_sample_template_from_experimental_request(self):
        if not self.opil_experimental_requests:
            raise IntentParserException('No experimental request found.')

        unique_templates = {sample_set.template for sample_set in self.opil_sample_sets if sample_set.template}
        if not unique_templates:
            self.sample_template = opil.Component(identity=self._id_provider.get_unique_sd2_id(),
                                                  component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            self.sample_template.features = self._get_opil_features()
        else:
            # Assume only one per request.
            self.sample_template = unique_templates.pop()

    def to_opil(self):
        opil_doc = opil.Document()
        for component in self.opil_components:
            opil_doc.add(component)
        for component in self.opil_sample_sets:
            opil_doc.add(component)
        for component in self.opil_experimental_requests:
            opil_doc.add(component)
        for component in self.opil_protocol_interfaces:
            opil_doc.add(component)
        return opil_doc

    def update_parameter_values(self, document_parameter_names_to_values):
        name_to_parameter = {parameter.name: parameter for parameter in self.lab_field_id_to_values.values()}
        for parameter_name, parameter_value in document_parameter_names_to_values.items():
            if parameter_name in name_to_parameter:
                opil_parameter_template = name_to_parameter[parameter_name]
                opil_parameter_value = opil_parameter_template.parameter_value
                opil_parameter_value.value = parameter_value


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

    def _create_sample_variables_from_measurement_intent(self, measurement_intent):
        all_sample_variables = []
        if measurement_intent.size_of_batches() > 0 and self.batch_template:
            batch_measures = measurement_intent.batch_values_to_opil_measures()
            batch_variable = self._create_variable_feature_with_variant_measures(self.batch_template,
                                                                                 batch_measures)
            all_sample_variables.append(batch_variable)

        if not measurement_intent.contents_is_empty():
            measurement_contents = measurement_intent.get_contents()
            for content in measurement_contents.get_contents():
                # column_id
                if content.size_of_column_id() > 0 and self.column_id_template:
                    col_id_components = content.col_id_values_to_opil_components()
                    self.opil_components.extend(col_id_components)
                    col_id_variable = self._create_variable_feature_with_variants(self.col_id_template,
                                                                                  col_id_components)
                    all_sample_variables.append(col_id_variable)
                # dna_reaction_concentration
                if content.size_of_dna_reaction_concentrations() > 0 and self.dna_reaction_concentration_template:
                    dna_reaction_concentration_components = content.dna_reaction_concentration_values_to_opil_components()
                    self.opil_components.extend(dna_reaction_concentration_components)
                    dna_reaction_concentration_variable = self._create_variable_feature_with_variants(self.dna_reaction_concentration_template,
                                                                                                      dna_reaction_concentration_components)
                    all_sample_variables.append(dna_reaction_concentration_variable)
                # lab_id
                if content.size_of_lab_ids() > 0 and self.lab_id_template:
                    lab_id_components = content.lab_id_values_to_opil_components()
                    self.opil_components.extend(lab_id_components)
                    lab_id_variable = self._create_variable_feature_with_variants(self.lab_id_template,
                                                                                  lab_id_components)
                    all_sample_variables.append(lab_id_variable)
                # media
                if content.size_of_medias() > 0:
                    for media in content.get_medias():
                        if media.get_name() in self.media_and_reagents_templates:
                            media_template = self.media_and_reagents_templates[media.get_name()]
                            media_components = media.values_to_opil_components()
                            self.opil_components.extend(media_components)
                            media_variable = self._create_variable_feature_with_variants(media_template,
                                                                                         media_components)
                            all_sample_variables.append(media_variable)
                # number_of_negative_controls
                if content.size_of_num_of_neg_controls() > 0 and self.num_neg_control_template:
                    num_neg_control_components = content.number_of_negative_control_values_to_opil_components()
                    self.opil_components.extend(num_neg_control_components)
                    num_neg_control_variable = self._create_variable_feature_with_variants(self.num_neg_control_template,
                                                                                           num_neg_control_components)
                    all_sample_variables.append(num_neg_control_variable)
                # row_id
                if content.size_of_row_ids() > 0 and self.row_id_template:
                    row_id_components = content.row_id_values_to_sbol_variable_feature()
                    self.opil_components.extend(row_id_components)
                    row_id_variable = self._create_variable_feature_with_variants(self.row_id_template,
                                                                                  row_id_components)
                    all_sample_variables.append(row_id_variable)
                # rna_inhibitor
                if content.size_of_rna_inhibitor_flags() > 0 and self.use_rna_inhib_template:
                    use_rna_inhib_components = content.use_rna_inhibitor_values_to_opil_components()
                    self.opil_components.extend(use_rna_inhib_components)
                    use_rna_inhib_variable = self._create_variable_feature_with_variants(self.use_rna_inhib_template,
                                                                                         use_rna_inhib_components)
                    all_sample_variables.append(use_rna_inhib_variable)
                # template_dna
                if content.size_of_template_dna_values() > 0 and self.template_dna_template:
                    template_dna_components = content.template_dna_values_to_opil_components()
                    self.opil_components.extend(template_dna_components)
                    template_dna_variable = self._create_variable_feature_with_variants(self.template_dna_template,
                                                                                        template_dna_components)
                    all_sample_variables.append(template_dna_variable)
                # reagent
                if content.size_of_reagents() > 0:
                    for reagent in content.get_reagents():
                        if reagent.get_name() in self.media_and_reagents_templates:
                            reagent_template = self.media_and_reagents_templates[reagent.get_name()]
                            reagent_measures = reagent.reagent_values_to_opil_measures()
                            reagent_variable = self._create_variable_feature_with_variant_measures(reagent_template,
                                                                                                   reagent_measures)
                            all_sample_variables.append(reagent_variable)

        # control
        if measurement_intent.size_of_controls() > 0 and self.control_template:
            control_samplesets = None # todo
            control_variable = self._create_variable_feature_with_variant_derivation(self.control_template,
                                                                                     control_samplesets)
            all_sample_variables.append(control_variable)
        # ods
        if measurement_intent.size_of_optical_density() > 0 and self.ods_template:
            optical_density_measures = measurement_intent.optical_density_values_to_opil_measures()
            optical_density_variable = self._create_variable_feature_with_variant_measures(self.ods_template,
                                                                                           optical_density_measures)
            all_sample_variables.append(optical_density_variable)
        # replicates
        if measurement_intent.size_of_replicates() > 0 and self.replicate_template:
            replicate_measures = measurement_intent.replicate_values_to_opil_measure()
            replicate_variable = self._create_variable_feature_with_variant_measures(self.replicate_template,
                                                                                     replicate_measures)
            all_sample_variables.append(replicate_variable)
        # strains
        if measurement_intent.size_of_strains() > 0 and self.strains_template:
            strain_components = measurement_intent.strain_values_to_opil_components()
            self.opil_components.extend(strain_components)
            strains_variables = self._create_variable_feature_with_variants(self.strain_template,
                                                                            strain_components)
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

    def _create_opil_local_subcomponent(self, template_name):
        component_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                               types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        component_template.name = template_name
        self.opil_components.append(component_template)
        return component_template

    def _create_variable_feature_with_variants(self, variable, variants):
        variable_feature = opil.VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                                cardinality=sbol_constants.SBOL_ONE)
        variable_feature.variable = variable
        variable_feature.variant = variants
        return variable_feature

    def _create_variable_feature_with_variant_derivation(self, variable, variant_derivations):
        variable_feature = opil.VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                                cardinality=sbol_constants.SBOL_ONE)
        variable_feature.variable = variable
        variable_feature.variant_derivation = variant_derivations
        return variable_feature

    def _create_variable_feature_with_variant_measures(self, variable, variant_measures):
        variable_feature = opil.VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                                cardinality=sbol_constants.SBOL_ONE)
        variable_feature.variable = variable
        variable_feature.variant_measure = variant_measures
        return variable_feature

    def _create_media_template(self, ip_media):
        media_name = ip_media.get_media_name()
        media_component = opil.Component(identity=self._id_provider.get_unique_sd2_id(),
                                         component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        media_component.name = media_name.get_name()
        media_component.roles = [ip_constants.NCIT_MEDIA_URI]
        if media_name.get_link() is None:
            media_template = SubComponent(media_component)
            media_component.features = [media_template]
        else:
            media_template = SubComponent(media_name.get_link())
            media_component.features = [media_template]

        if ip_media.get_timepoint():
            media_timepoint_measure = ip_media.get_timepoint().to_opil_measure()
            media_template.measures = [media_timepoint_measure]
        self.opil_components.append(media_component)
        return media_component

    def _create_reagent_template(self, ip_reagent):
        reagent_name = ip_reagent.get_reagent_name()
        reagent_component = opil.Component(identity=self._id_provider.get_unique_sd2_id(),
                                      component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        reagent_component.roles = [ip_constants.NCIT_REAGENT_URI]
        reagent_component.name = reagent_name.get_name()
        if reagent_name.get_link() is None:
            reagent_template = SubComponent(reagent_component)
            reagent_component.features = [reagent_template]
        else:
            reagent_template = SubComponent(reagent_name.get_link())
            reagent_component.features = [reagent_template]

        if ip_reagent.get_timepoint():
            reagent_timepoint_measure = ip_reagent.get_timepoint().to_opil_measure()
            reagent_template.measures = [reagent_timepoint_measure]

        self.opil_components.append(reagent_component)
        return reagent_component

    def _get_opil_features(self):
        all_sample_templates = []
        if self.batch_template:
            all_sample_templates.append(self.batch_template)
        if self.col_id_template:
            all_sample_templates.append(self.col_id_template)
        if self.control_template:
            all_sample_templates.append(self.control_template)
        if self.dna_reaction_concentration_template:
            all_sample_templates.append(self.dna_reaction_concentration_template)
        if self.lab_id_template:
            all_sample_templates.append(self.lab_id_template)
        if self.num_neg_control_template:
            all_sample_templates.append(self.num_neg_control_template)
        if self.ods_template:
            all_sample_templates.append(self.ods_template)
        if self.row_id_template:
            all_sample_templates.append(self.row_id_template)
        if self.use_rna_inhib_template:
            all_sample_templates.append(self.use_rna_inhib_template)
        if self.template_dna_template:
            all_sample_templates.append(self.template_dna_template)
        if self.strain_template:
            all_sample_templates.append(self.strain_template)
        for media_or_reagent_template in self.media_and_reagents_templates.values():
            all_sample_templates.append(media_or_reagent_template)
        return all_sample_templates

    def _filter_components_by_role(self, role_name):
        return [opil_component for opil_component in self.opil_components if tyto.NCIT.get_uri_by_term(role_name)]

    def _filter_sampleset_for_unique_templates(self):
        unique_templates = {sample_set.template for sample_set in self.opil_sample_sets if sample_set.template}
        if not unique_templates:
            raise IntentParserException('No sample set template found.')
        # Assume only one per request.
        return unique_templates.pop()

    def _load_strain_template(self):
        strain = self._filter_components_by_role(ip_constants.NCIT_STRAIN_NAME)
        if len(strain) > 1:
            raise IntentParserException('Expected one strain but %d were found in experimental request %s'
                                        % (len(strain), self.opil_experimental_requests[0].name))
        elif len(strain) == 0:
            self.strain_template = self._create_opil_local_subcomponent(self._opil_component_template.strains_template)
            self.opil_components.append(strain)
        else:
            self.strain_template = strain[0]

    def _load_reagent_and_media_templates(self):
        for opil_component in self.opil_components:
            if tyto.NCIT.get_uri_by_term(ip_constants.NCIT_REAGENT_NAME) in opil_component.roles:
                self.media_and_reagents_templates[opil_component.name] = opil_component
            elif tyto.NCIT.get_uri_by_term(ip_constants.NCIT_MEDIA_NAME) in opil_component.roles:
                self.media_and_reagents_templates[opil_component.name] = opil_component
            elif tyto.NCIT.get_uri_by_term(ip_constants.NCIT_INDUCER_NAME) in opil_component.roles:
                self.media_and_reagents_templates[opil_component.name] = opil_component

        for ip_component in self._opil_component_template.media_and_reagent_templates:
            if isinstance(ip_component, ReagentIntent):
                reagent_name = ip_component.get_reagent_name()
                if reagent_name.get_name() not in self.media_and_reagents_templates:
                    reagent_component = self._create_reagent_template(ip_component)
                    self.media_and_reagents_templates[reagent_component.name] = reagent_component
            elif isinstance(ip_component, MediaIntent):
                media_name = ip_component.get_media_name()
                if media_name.get_name() not in self.media_and_reagents_templates:
                    media_component = self._create_media_template(ip_component)
                    self.media_and_reagents_templates[media_component.name] = media_component