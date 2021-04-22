import sbol3

from intent_parser.intent.measure_property_intent import ReagentIntent, MediaIntent, NamedStringValue
from intent_parser.intent.parameter_intent import ParameterIntent
from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.table.controls_table import ControlsTable
from intent_parser.table.measurement_table import MeasurementTable
from intent_parser.utils.id_provider import IdProvider
from sbol3 import Component, SubComponent, LocalSubComponent, TextProperty, VariableFeature
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.utils.opil_utils as opil_utils
import logging
import opil
import sbol3.constants as sbol_constants


class OpilDocumentTemplate(object):

    _LOGGER = logging.getLogger('OpilDocumentTemplate')

    def __init__(self):
        self.opil_components = []
        self.opil_sample_sets = []
        self.opil_experimental_requests = []
        self.opil_protocol_interfaces = []
        self.opil_unidentifieds = []

    def get_components(self):
        return self.opil_components

    def get_sample_sets(self):
        return self.opil_sample_sets

    def get_experimental_requests(self):
        return self.opil_experimental_requests

    def get_protocol_interfaces(self):
        return self.opil_protocol_interfaces

    def get_unidentifieds(self):
        return self.opil_unidentifieds

    def load_from_template(self, template: opil.Document):
        for top_level in template.objects:
            if isinstance(top_level, Component):
                self.opil_components.append(top_level)
            elif isinstance(top_level, opil.SampleSet):
                self.opil_sample_sets.append(top_level)
            elif isinstance(top_level, opil.ExperimentalRequest):
                self.opil_experimental_requests.append(top_level)
            elif isinstance(top_level, opil.ProtocolInterface):
                self.opil_protocol_interfaces.append(top_level)
            else:
                self.opil_unidentifieds.append(top_level)

class OpilParameterTemplate(object):

    _LOGGER = logging.getLogger('OpilParameterTemplate')

    def __init__(self):
        self.parameter = None
        self.parameter_value = None

class OpilControlTemplate(object):

    _LOGGER = logging.getLogger('OpilControlTemplate')

    def __init__(self):
        self.strains_template = None
        self.contents_template = None
        self.template = None
        self.opil_components = []
        self.opil_sample_sets = []
        self._id_provider = IdProvider()

    def add_opil_components(self, opil_components):
        self.opil_components.extend(opil_components)

    def add_sample_set(self, sample_set):
        self.opil_sample_sets.append(sample_set)

    def get_template(self):
        return self.template

    def load_from_control_table(self, control_table: ControlsTable):
        table_header_templates = []
        if control_table.has_contents():
            self.contents_template = self._create_opil_local_subcomponent(ip_constants.HEADER_CONTENTS_VALUE)
            table_header_templates.append(self.contents_template)

        if control_table.has_strains():
            self.strains_template = self._create_opil_local_subcomponent(ip_constants.HEADER_STRAINS_VALUE)
            table_header_templates.append(self.strains_template)
        self.template = Component(self._id_provider.get_unique_sd2_id(),
                                  types=sbol_constants.SBO_FUNCTIONAL_ENTITY)

        if len(table_header_templates) == 0:
            raise IntentParserException('Unable to create control templates because Control Table missing table headers.')
        self.template.features = table_header_templates

    def _create_opil_local_subcomponent(self, template_name):
        component_template = LocalSubComponent(types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        component_template.name = template_name
        return component_template

class OpilMeasurementTemplate(object):

    _LOGGER = logging.getLogger('OpilMeasurementTemplate')

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

    _LOGGER = logging.getLogger('ExperimentalRequest')

    def __init__(self,
                 lab_namespace: str,
                 template: OpilDocumentTemplate,
                 experiment_id: str,
                 experiment_ref: str,
                 experiment_ref_url: str):
        self.opil_components = [component.copy() for component in template.get_components()]
        self.opil_sample_sets = [component.copy() for component in template.get_sample_sets()]
        self.opil_experimental_requests = [component.copy() for component in template.get_experimental_requests()]
        self.opil_measurements = []
        self.opil_protocol_interfaces = [component.copy() for component in template.get_protocol_interfaces()]
        self.opil_parameter_values = []
        self._experiment_id = experiment_id
        self._experiment_ref = experiment_ref
        self._experiment_ref_url = experiment_ref_url
        self._lab_namespace = lab_namespace
        self._opil_measurement_template = OpilMeasurementTemplate()
        self._opil_control_templates = {}
        self._id_provider = IdProvider()

        self.batch_template = None
        self.column_id_template = None
        self.control_template = None
        self.dna_reaction_concentration_template = None
        self.lab_id_template = None
        self.media_template = None
        self.num_neg_control_template = None
        self.ods_template = None
        self.row_id_template = None
        self.strain_template = None
        self.template_dna_template = None
        self.use_rna_inhib_template = None
        self.media_and_reagents_templates = {}
        self.sample_template = None
        self.lab_parameter_field_id_to_values = {}

    def add_variable_features_from_measurement_intents(self, measurement_intents):
        for index in range(len(measurement_intents)):
            measurement_intent = measurement_intents[index]
            sample_set = self.opil_sample_sets[index]
            all_sample_variables = self._create_sample_variables_from_measurement_intent(measurement_intent)
            sample_set.variable_features = all_sample_variables

    def add_run_parameters(self, parameter_intent: ParameterIntent):
        """Adds run configurations for experiment as a parameter to a ProtocolInterface.
        Note: In opil, protocol name is not encoded as a run parameter but rather as a ProtocolInterface
              Similarly, protocol_id is represented as a custom annotation and not as parameters
        Args:
            parameter_intent: refer to parameters processed from a paramater table
        """
        if len(self.opil_protocol_interfaces) != 1:
            raise IntentParserException('Expecting 1 but got %d opil.ProtocolInterface(s).' % len(self.opil_protocol_interfaces))
        opil_protocol_interface = self.opil_protocol_interfaces[0]

        if parameter_intent.get_xplan_base_dir() is None:
            raise IntentParserException('%s is missing a value' % ip_constants.PARAMETER_BASE_DIR)
        base_dir = self._create_opil_string_parameter_field(ip_constants.PARAMETER_BASE_DIR)
        opil_protocol_interface.has_parameter.append(base_dir)
        base_dir_value = self._create_opil_string_parameter_value(parameter_intent.get_xplan_base_dir())
        base_dir_value.value_of = base_dir
        self.opil_parameter_values.append(base_dir_value)

        xplan_reactor = self._create_opil_string_parameter_field(ip_constants.PARAMETER_XPLAN_REACTOR)
        opil_protocol_interface.has_parameter.append(xplan_reactor)
        xplan_reactor_value = self._create_opil_string_parameter_value(parameter_intent.get_xplan_reactor())
        xplan_reactor_value.value_of = xplan_reactor
        self.opil_parameter_values.append(xplan_reactor_value)

        if parameter_intent.get_plate_size() is None:
            raise IntentParserException('%s is missing a value' % ip_constants.PARAMETER_PLATE_SIZE)
        plate_size = self._create_opil_integer_parameter_field(ip_constants.PARAMETER_PLATE_SIZE)
        opil_protocol_interface.has_parameter.append(plate_size)
        plate_size_value = self._create_opil_integer_parameter_value(parameter_intent.get_plate_size())
        plate_size_value.value_of = plate_size
        self.opil_parameter_values.append(plate_size_value)

        if parameter_intent.get_plate_number() is None:
            raise IntentParserException('%s is missing a value' % ip_constants.PARAMETER_PLATE_NUMBER)
        plate_number = self._create_opil_integer_parameter_field(ip_constants.PARAMETER_PLATE_NUMBER)
        opil_protocol_interface.has_parameter.append(plate_number)
        plate_number_value = self._create_opil_integer_parameter_value(parameter_intent.get_plate_number())
        plate_number_value.value_of = plate_number
        self.opil_parameter_values.append(plate_number_value)

        container_search_string = self._create_opil_string_parameter_field(ip_constants.PARAMETER_CONTAINER_SEARCH_STRING)
        opil_protocol_interface.has_parameter.append(container_search_string)
        if parameter_intent.get_container_search_string() == dc_constants.GENERATE:
            container_search_string_value = self._create_opil_string_parameter_value(parameter_intent.get_container_search_string())
            container_search_string_value.value_of = container_search_string
            self.opil_parameter_values.append(container_search_string_value)
        else:
            for value in parameter_intent.get_container_search_string():
                container_search_string_value = self._create_opil_string_parameter_value(value)
                container_search_string_value.value_of = container_search_string
                self.opil_parameter_values.append(container_search_string_value)

        if parameter_intent.get_strain_property() is None:
            raise IntentParserException('%s is missing a value' % ip_constants.PARAMETER_STRAIN_PROPERTY)
        strain_property = self._create_opil_string_parameter_field(ip_constants.PARAMETER_STRAIN_PROPERTY)
        opil_protocol_interface.has_parameter.append(strain_property)
        strain_property_value = self._create_opil_string_parameter_value(parameter_intent.get_strain_property())
        strain_property_value.value_of = strain_property
        self.opil_parameter_values.append(strain_property_value)

        if parameter_intent.get_xplan_path() is None:
            raise IntentParserException('%s is missing a value' % ip_constants.PARAMETER_XPLAN_PATH)
        xplan_path = self._create_opil_string_parameter_field(ip_constants.PARAMETER_XPLAN_PATH)
        opil_protocol_interface.has_parameter.append(xplan_path)
        xplan_path_value = self._create_opil_string_parameter_value(parameter_intent.get_xplan_path())
        xplan_path_value.value_of = xplan_path
        self.opil_parameter_values.append(xplan_path_value)

        submit = self._create_opil_boolean_parameter_field(ip_constants.PARAMETER_SUBMIT)
        opil_protocol_interface.has_parameter.append(submit)
        submit_value = self._create_opil_boolean_parameter_value(parameter_intent.get_submit_flag())
        submit_value.value_of = submit
        self.opil_parameter_values.append(submit_value)

        test_mode = self._create_opil_boolean_parameter_field(ip_constants.PARAMETER_TEST_MODE)
        opil_protocol_interface.has_parameter.append(test_mode)
        test_mode_value = self._create_opil_boolean_parameter_value(parameter_intent.get_submit_flag())
        test_mode_value.value_of = test_mode
        self.opil_parameter_values.append(test_mode_value)

        if parameter_intent.get_experiment_ref_url() is None:
            raise IntentParserException('%s is missing a value' % ip_constants.PARAMETER_EXPERIMENT_REFERENCE_URL_FOR_XPLAN)
        experiment_ref_url = self._create_opil_string_parameter_field(ip_constants.PARAMETER_EXPERIMENT_REFERENCE_URL_FOR_XPLAN)
        opil_protocol_interface.has_parameter.append(experiment_ref_url)
        experiment_ref_url_value = self._create_opil_string_parameter_value(parameter_intent.get_experiment_ref_url())
        experiment_ref_url_value.value_of = experiment_ref_url
        self.opil_parameter_values.append(experiment_ref_url_value)

    def _create_opil_boolean_parameter_field(self, field: str):
        parameter_field = opil.BooleanParameter()
        parameter_field.name = field
        return parameter_field

    def _create_opil_boolean_parameter_value(self, value: bool):
        parameter_value = opil.BooleanValue()
        parameter_value.value = value
        return parameter_value

    def _create_opil_integer_parameter_field(self, field: str):
        parameter_field = opil.IntegerParameter()
        parameter_field.name = field
        return parameter_field

    def _create_opil_integer_parameter_value(self, value: int):
        parameter_value = opil.IntegerValue()
        parameter_value.value = value
        return parameter_value

    def _create_opil_string_parameter_field(self, field: str):
        parameter_field = opil.StringParameter()
        parameter_field.name = field
        return parameter_field

    def _create_opil_string_parameter_value(self, value: str):
        parameter_value = opil.StringValue()
        parameter_value.value = value
        return parameter_value

    def connect_properties(self):
        if len(self.opil_experimental_requests) != 1:
            raise IntentParserException('Expecting 1 ExperimentalRequest but %d were found'
                                        % len(self.opil_experimental_requests))
        experimental_request = self.opil_experimental_requests[0]
        experimental_request.measurements = self.opil_measurements
        experimental_request.sample_set = self.opil_sample_sets
        # protocol_interface.allowed_samples.append(sample_set)
        if len(self.opil_protocol_interfaces) != 1:
            raise IntentParserException('Expecting 1 ProtocolInterface but %d were found.' % len(self.opil_protocol_interfaces))
        experimental_request.instance_of = self.opil_protocol_interfaces[0].identity
        experimental_request.has_parameter_value = self.opil_parameter_values

    def create_subcomponents_from_template(self):
        if not self.sample_template:
            raise IntentParserException('Expecting value set for SampleSet.template but none was found.')
        local_sub_components = self.sample_template.features
        if self._opil_measurement_template.batch_template:
            self.batch_template = self._create_opil_local_subcomponent(self._opil_measurement_template.batch_template)
        if self._opil_measurement_template.column_id_template:
            self.column_id_template = self._create_opil_local_subcomponent(self._opil_measurement_template.column_id_template)
        if self._opil_measurement_template.control_template:
            self.control_template = self._create_opil_local_subcomponent(self._opil_measurement_template.control_template)
        if self._opil_measurement_template.dna_reaction_concentration_template:
            self.dna_reaction_concentration_template = self._create_opil_local_subcomponent(self._opil_measurement_template.dna_reaction_concentration_template)
        if self._opil_measurement_template.lab_id_template:
            self.lab_id_template = self._create_opil_local_subcomponent(self._opil_measurement_template.lab_id_template)
        if self._opil_measurement_template.num_neg_control_template:
            self.num_neg_control_template = self._create_opil_local_subcomponent(self._opil_measurement_template.num_neg_control_template)
        if self._opil_measurement_template.ods_template:
            self.ods_template = self._create_opil_local_subcomponent(self._opil_measurement_template.ods_template)
        if self._opil_measurement_template.row_id_template:
            self.row_id_template = self._create_opil_local_subcomponent(self._opil_measurement_template.row_id_template)
        if self._opil_measurement_template.use_rna_inhib_template:
            self.use_rna_inhib_template = self._create_opil_local_subcomponent(self._opil_measurement_template.use_rna_inhib_template)
        if self._opil_measurement_template.template_dna_template:
            self.template_dna_template = self._create_opil_local_subcomponent(self._opil_measurement_template.template_dna_template)

        self._load_strain_template(local_sub_components)
        self._load_reagent_and_media_templates(local_sub_components)
        self.sample_template.features = self._get_opil_features()

    def load_lab_parameters(self):
        if not self.opil_protocol_interfaces:
            raise IntentParserException('ExperimentalRequest does not a opil ProtocolInterface.')
        elif len(self.opil_protocol_interfaces) > 1:
            raise IntentParserException('expecting 1 but got %d opil ProtocolInterface.' % len(self.opil_protocol_interfaces))

        opil_protocol_interface = self.opil_protocol_interfaces[0]
        for parameter in opil_protocol_interface.has_parameter:
            opil_parameter_template = OpilParameterTemplate()
            opil_parameter_template.parameter = parameter
            self.lab_parameter_field_id_to_values[parameter.identity] = opil_parameter_template

        for parameter_value in self.opil_parameter_values:
            parameter_id = str(parameter_value.value_of)
            if parameter_id not in self.lab_parameter_field_id_to_values:
                raise IntentParserException('opil.ParameterValue %s points to an unknown parameter %s'
                                            % (parameter_value.identity, parameter_id))
            self.lab_parameter_field_id_to_values[parameter_id].parameter_value = parameter_value

    def load_experimental_request(self):
        if len(self.opil_experimental_requests) == 0:
            self.opil_experimental_requests.append(opil.ExperimentalRequest(self._id_provider.get_unique_sd2_id()))
        else:
            raise IntentParserException('expecting 0 but got %d opil.ExperimentalRequest.' % len(self.opil_experimental_requests))
        opil_experimental_request = self.opil_experimental_requests[0]
        self._annotate_experimental_id(opil_experimental_request)
        self._annotate_experimental_reference(opil_experimental_request)
        self._annotate_experimental_reference_url(opil_experimental_request)

    def load_from_control_table(self, control_table: ControlsTable):
        opil_control_template = OpilControlTemplate()
        opil_control_template.load_from_control_table(control_table)
        self._opil_control_templates[control_table.get_table_caption()] = opil_control_template

        for control_intent in control_table.get_intents():
            sample_set = opil.SampleSet(identity=self._id_provider.get_unique_sd2_id(),
                                        template=opil_control_template.template)
            all_sample_variables = []
            if control_intent.size_of_contents() > 0 and opil_control_template.contents_template:
                content_variables = self._create_variable_features_from_control_contents(control_intent.get_contents(),
                                                                                         opil_control_template.contents_template)
                all_sample_variables.extend(content_variables)
            if control_intent.size_of_strains() > 0 and opil_control_template.strains_template:
                strain_components = control_intent.strain_values_to_opil_components()
                opil_control_template.add_opil_components(strain_components)
                strains_variables = self._create_variable_feature_with_variants(opil_control_template.strains_template,
                                                                                strain_components)
                all_sample_variables.append(strains_variables)
            sample_set.variable_features = all_sample_variables
            opil_control_template.add_sample_set(sample_set)

    def _create_variable_features_from_control_contents(self, control_contents, content_template):
        all_sample_variables = []
        for content in control_contents:
            if isinstance(content, ReagentIntent):
                reagent_measures = content.reagent_values_to_opil_measures()
                reagent_variable = self._create_variable_feature_with_variant_measures(content_template,
                                                                                       reagent_measures)
                all_sample_variables.append(reagent_variable)
            elif isinstance(content, NamedStringValue):
                content_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                              types=sbol_constants.SBO_FUNCTIONAL_ENTITY)
                content_component.name = content.get_named_link().get_name()
                self.opil_components.append(content_component)
                if content.get_named_link().get_link() is not None:
                    content_sub_component = SubComponent(content.get_named_link().get_link())
                    content_component.features = [content_sub_component]
                variants = [content_component]
                content_variable = self._create_variable_feature_with_variants(content_template,
                                                                               variants)
                all_sample_variables.append(content_variable)
        return all_sample_variables

    def load_from_measurement_table(self, measurement_table):
        self._opil_measurement_template.load_from_measurement_table(measurement_table)

    def load_and_update_measurement(self, measurement_intents):
        if not self.opil_protocol_interfaces:
            raise IntentParserException('No Protocol Interface found')
        if len(self.opil_protocol_interfaces) > 1:
            raise IntentParserException('Expecting 1 ProtocolInterface but %d were found.' % len(self.opil_protocol_interfaces))
        protocol_interface = self.opil_protocol_interfaces[0]
        opil_measurement_intent_pairs = self._map_opil_measurement_to_intent(measurement_intents,
                                                                             protocol_interface.protocol_measurement_type)
        for opil_measurement, intent in opil_measurement_intent_pairs:
            # self.opil_measurements.append(opil_measurement)
            if intent.size_of_file_types() > 0:
                intent.file_types_to_opil_measurement_annotation(opil_measurement)
            if intent.size_of_timepoints() > 0:
                timepoint_measures = intent.timepoint_values_to_opil_measures()
                opil_measurement.time = timepoint_measures

    def load_sample_set(self, number_of_sample_sets):
        protocol_interface = self.opil_protocol_interfaces[0]
        while len(self.opil_sample_sets) < number_of_sample_sets:
            sample_set = opil.SampleSet(identity=self._id_provider.get_unique_sd2_id(),
                                        template=self.sample_template)
            protocol_interface.allowed_samples.append(sample_set)
            self.opil_sample_sets.append(sample_set)

    def load_sample_template_from_protocol_interface(self):
        if len(self.opil_protocol_interfaces) != 1:
            raise IntentParserException(
                'Expecting 1 ProtocolInterface but found %d.' % len(self.opil_protocol_interfaces))

        uris_to_components = {}
        for component in self.opil_components:
            if component.identity not in uris_to_components:
                uris_to_components[component.identity] = component
            else:
                if uris_to_components[component.identity]:
                    raise IntentParserException('conflict mapping Components with same identity.')

        unique_templates = []
        for sample in self.opil_sample_sets:
            if sample.identity not in self.opil_protocol_interfaces[0].allowed_samples:
                raise IntentParserException('SampleSet not found in ProtocolInterface: %s' % sample.identity)
            str_template = str(sample.template)
            if not sample.template:
                raise IntentParserException('A SampleSet must have a template but none was set: %s' % sample.identity)
            if str_template not in uris_to_components:
                raise IntentParserException('No Component found for SampleSet.template: %s' % str_template)
            unique_templates.append(uris_to_components[str_template])

        if not unique_templates:
            self.sample_template = Component(identity=self._id_provider.get_unique_sd2_id(),
                                             types=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            self.opil_components.append(self.sample_template)
            return
        elif len(unique_templates) > 1:
            raise IntentParserException('Expecting 1 SampleSet.template but found %d.' % len(unique_templates))

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
        name_to_parameter = {}
        dotname_to_name = {}
        for opil_parameter_template in self.lab_parameter_field_id_to_values.values():
            opil_parameter = opil_parameter_template.parameter
            if not opil_parameter.name:
                raise IntentParserException('Opil Parameter missing a name: %s' % opil_parameter.identity)
            if opil_parameter.name in name_to_parameter:
                message = 'More than one opil Parameter with the same name: %s' % opil_parameter.name
                # raise IntentParserException(message)
                self._LOGGER.warning(message)
                continue
            try:
                opil_parameter.dotname = sbol3.TextProperty(opil_parameter, 'http://strateos.com/dotname', 0, 1)
                if opil_parameter.dotname:
                    dotname_to_name[opil_parameter.dotname] = opil_parameter.name
            except AttributeError:
                self._LOGGER.warning('Parameter does not have a dotname: %s' % opil_parameter.identity)
            name_to_parameter[opil_parameter.name] = opil_parameter_template

        for parameter_name, parameter_value in document_parameter_names_to_values.items():
            filtered_name = parameter_name
            if parameter_name in dotname_to_name:
                filtered_name = dotname_to_name[parameter_name]

            if filtered_name in name_to_parameter:
                opil_parameter_template = name_to_parameter[filtered_name]
                opil_parameter = opil_parameter_template.parameter
                opil_parameter_value = opil_parameter_template.parameter_value
                if not opil_parameter_value:
                    opil_parameter_value = opil_utils.create_parameter_value_from_parameter(opil_parameter,
                                                                                            parameter_value)
                    opil_parameter_value.value_of = opil_parameter
                    self.opil_parameter_values.append(opil_parameter_value)
                else:
                    opil_parameter_value.value = parameter_value
            # else:
            #     raise IntentParserException('Parameter not supported in protocol: %s' % filtered_name)

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
        last_encoded_media_template = None
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
                    col_id_variable = self._create_variable_feature_with_variants(self.column_id_template,
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
                        if media.get_media_name().get_name() in self.media_and_reagents_templates:
                            media_template = self.media_and_reagents_templates[media.get_media_name().get_name()]
                            last_encoded_media_template = media_template
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
                    row_id_components = content.row_id_values_to_opil_components()
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
                        if reagent.get_reagent_name().get_name() in self.media_and_reagents_templates:
                            reagent_template = self.media_and_reagents_templates[reagent.get_reagent_name().get_name()]
                            reagent_measures = reagent.reagent_values_to_opil_measures()
                            reagent_variable = self._create_variable_feature_with_variant_measures(reagent_template,
                                                                                                   reagent_measures)
                            all_sample_variables.append(reagent_variable)

        # control
        if measurement_intent.size_of_controls() > 0 and self.control_template:
            unique_control_templates = []
            for control_intent in measurement_intent.get_controls():
                table_caption = control_intent.get_table_caption()
                if table_caption in self._opil_control_templates and table_caption not in unique_control_templates:
                    unique_control_templates.append(self._opil_control_templates[table_caption])
            control_samplesets = [opil_control_template.opil_sample_sets for opil_control_template in unique_control_templates]
            control_variable = self._create_variable_feature_with_variant_derivation(self.control_template,
                                                                                     control_samplesets)
            all_sample_variables.append(control_variable)
        # ods
        if measurement_intent.size_of_optical_density() > 0 and self.ods_template:
            optical_density_measures = measurement_intent.optical_density_values_to_opil_measures()
            optical_density_variable = self._create_variable_feature_with_variant_measures(self.ods_template,
                                                                                           optical_density_measures)
            all_sample_variables.append(optical_density_variable)
        # strains
        if measurement_intent.size_of_strains() > 0 and self.strain_template:
            strain_components = measurement_intent.strain_values_to_opil_components()
            self.opil_components.extend(strain_components)
            strains_variables = self._create_variable_feature_with_variants(self.strain_template,
                                                                            strain_components)
            all_sample_variables.append(strains_variables)
        # temperature
        if measurement_intent.size_of_temperatures() > 0:
            if last_encoded_media_template:
                temperature_measures = measurement_intent.temperature_values_to_opil_measure()
                temperature_variable = self._create_variable_feature_with_variant_measures(last_encoded_media_template,
                                                                                           temperature_measures)
                all_sample_variables.append(temperature_variable)
            else:
                raise IntentParserException('Skip opil encoding for temperatures since no media template was created '
                                            'to assign temperature values.')
        return all_sample_variables

    def _create_opil_local_subcomponent(self, template_name):
        component_template = LocalSubComponent(types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        component_template.name = template_name
        return component_template

    def _create_variable_feature_with_variants(self, variable, variants):
        variable_feature = VariableFeature(cardinality=sbol_constants.SBOL_ONE,
                                           variable=variable)
        variable_feature.variants = variants
        return variable_feature

    def _create_variable_feature_with_variant_derivation(self, variable, variant_derivations):
        variable_feature = VariableFeature(cardinality=sbol_constants.SBOL_ONE,
                                           variable=variable)
        variable_feature.variant_derivations = variant_derivations
        return variable_feature

    def _create_variable_feature_with_variant_measures(self, variable, variant_measures):
        variable_feature = VariableFeature(cardinality=sbol_constants.SBOL_ONE,
                                           variable=variable)
        variable_feature.variant_measures = variant_measures
        return variable_feature

    def _create_media_template(self, ip_media):
        media_name = ip_media.get_media_name()
        media_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                    types=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        media_component.name = media_name.get_name()
        media_component.roles = [ip_constants.NCIT_MEDIA_URI]
        media_template = None
        if media_name.get_link() is None:
            media_template = SubComponent(media_component)
            media_template.name = media_name.get_name()
            # media_component.features = [media_template]
        else:
            media_template = SubComponent(media_name.get_link())
            media_template.name = media_name.get_name()
            # media_component.features = [media_template]

        if ip_media.get_timepoint():
            media_timepoint_measure = ip_media.get_timepoint().to_opil_measure()
            media_template.measures = [media_timepoint_measure]
        self.opil_components.append(media_component)
        return media_template

    def _create_reagent_template(self, ip_reagent):
        reagent_name = ip_reagent.get_reagent_name()
        reagent_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                      types=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        reagent_component.roles = [ip_constants.NCIT_REAGENT_URI]
        reagent_component.name = reagent_name.get_name()
        reagent_template = None
        if reagent_name.get_link() is None:
            reagent_template = SubComponent(reagent_component)
            reagent_template.name = reagent_name.get_name()
            # reagent_component.features = [reagent_template]
        else:
            reagent_template = SubComponent(reagent_name.get_link())
            reagent_template.name = reagent_name.get_name()
            # reagent_component.features = [reagent_template]

        if ip_reagent.get_timepoint():
            reagent_timepoint_measure = ip_reagent.get_timepoint().to_opil_measure()
            reagent_template.measures = [reagent_timepoint_measure]

        self.opil_components.append(reagent_component)
        return reagent_template

    def _get_opil_features(self):
        all_sample_templates = []
        if self.batch_template:
            all_sample_templates.append(self.batch_template)
        if self.column_id_template:
            all_sample_templates.append(self.column_id_template)
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

    def _filter_sampleset_for_unique_templates(self):
        unique_templates = {sample_set.template for sample_set in self.opil_sample_sets if sample_set.template}
        if not unique_templates:
            raise IntentParserException('No sample set template found.')
        # Assume only one per request.
        return unique_templates.pop()

    def _get_measurement_type_from_uri(self, opil_measurement_type):
        if opil_measurement_type == ip_constants.NCIT_FLOW_URI:
            return ip_constants.MEASUREMENT_TYPE_FLOW
        elif opil_measurement_type == ip_constants.NCIT_RNA_SEQ_URI:
            return ip_constants.MEASUREMENT_TYPE_RNA_SEQ
        elif opil_measurement_type == ip_constants.NCIT_DNA_SEQ_URI:
            return ip_constants.MEASUREMENT_TYPE_DNA_SEQ
        elif opil_measurement_type == ip_constants.NCIT_PROTEOMICS_URI:
            return ip_constants.MEASUREMENT_TYPE_PROTEOMICS
        elif opil_measurement_type == ip_constants.NCIT_SEQUENCING_CHROMATOGRAM_URI:
            return ip_constants.MEASUREMENT_TYPE_SEQUENCING_CHROMATOGRAM
        elif opil_measurement_type == ip_constants.SD2_AUTOMATED_TEST_URI:
            return ip_constants.MEASUREMENT_TYPE_AUTOMATED_TEST
        elif opil_measurement_type == ip_constants.NCIT_CFU_URI:
            return ip_constants.MEASUREMENT_TYPE_CFU
        elif opil_measurement_type == ip_constants.NCIT_PLATE_READER_URI:
            return ip_constants.MEASUREMENT_TYPE_PLATE_READER
        elif opil_measurement_type == ip_constants.SD2_CONDITION_SPACE_URI:
            return ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE
        elif opil_measurement_type == ip_constants.SD2_EXPERIMENTAL_DESIGN_URI:
            return ip_constants.MEASUREMENT_TYPE_EXPERIMENTAL_DESIGN
        elif opil_measurement_type == ip_constants.NCIT_FLUORESCENCE_MICROSCOPY:
            return ip_constants.MEASUREMENT_TYPE_FLUOESCENE_MICROSCOPY
        else:
            raise IntentParserException('opil.MeasurementType not supported in Intent parser: %s' % opil_measurement_type)

    def _load_strain_template(self, local_sub_components):
        strain = [component for component in local_sub_components if ip_constants.NCIT_STRAIN_URI in component.roles]
        if len(strain) > 1:
            raise IntentParserException('Expecting 1 strain template but found %d in ExperimentalProtocol'
                                        % len(strain))
        elif len(strain) == 0:
            self.strain_template = self._create_opil_local_subcomponent(self._opil_measurement_template.strains_template)
            self.strain_template.roles = [ip_constants.NCIT_STRAIN_URI]
        else:
            self.strain_template = strain[0]

    def _load_reagent_and_media_templates(self, local_sub_components):
        for opil_local_subcomponent in local_sub_components:
            if ip_constants.NCIT_REAGENT_URI in opil_local_subcomponent.roles:
                self.media_and_reagents_templates[opil_local_subcomponent.name] = opil_local_subcomponent
            elif ip_constants.NCIT_MEDIA_URI in opil_local_subcomponent.roles:
                self.media_and_reagents_templates[opil_local_subcomponent.name] = opil_local_subcomponent
            elif ip_constants.NCIT_INDUCER_URI in opil_local_subcomponent.roles:
                self.media_and_reagents_templates[opil_local_subcomponent.name] = opil_local_subcomponent

        for ip_component in self._opil_measurement_template.media_and_reagent_templates:
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

    def _map_opil_measurement_to_intent(self, measurement_intents, opil_measurement_types):
        measurement_type_to_intent = {}
        opil_measurement_intent_pairs = []
        protocol_interface = self.opil_protocol_interfaces[0]
        # Collect measurement intents by type
        for measurement_intent in measurement_intents:
            measurement_type = measurement_intent.get_measurement_type()
            if measurement_type:
                if measurement_type not in measurement_type_to_intent:
                    measurement_type_to_intent[measurement_type] = []
                measurement_type_to_intent[measurement_type].append(measurement_intent)
            else:
                raise IntentParserException('Measurement type is missing.')

        # Mapping existing opil objects to intent
        for opil_measurement_type in opil_measurement_types:
            if not opil_measurement_type.type:
                raise IntentParserException('A MeasurementType.type is required but none was found: s' % opil_measurement_type.identity)
            measurement_type = self._get_measurement_type_from_uri(opil_measurement_type.type)
            if measurement_type not in measurement_type_to_intent:
                raise IntentParserException('Invalid measurement type not used in document %s' % opil_measurement_type)
            if not measurement_type_to_intent[measurement_type]:
                raise IntentParserException('Unable to map opil to intent')
            opil_intent = measurement_type_to_intent[measurement_type].pop()
            new_opil_measurement = opil.Measurement()
            protocol_interface.protocol_measurement_type.append(opil_measurement_type)
            new_opil_measurement.instance_of = opil_measurement_type
            self.opil_measurements.append(new_opil_measurement)
            opil_measurement_intent_pairs.append((new_opil_measurement, opil_intent))

        # Collecting intents that are not mapped and need to be created.
        for intents in measurement_type_to_intent.values():
            for intent in intents:
                new_opil_measurement = opil.Measurement()
                new_opil_measurement_type = intent.measurement_type_to_opil_measurement_type()
                protocol_interface.protocol_measurement_type.append(new_opil_measurement_type)
                new_opil_measurement.instance_of = new_opil_measurement_type.identity
                self.opil_measurements.append(new_opil_measurement)
                opil_measurement_intent_pairs.append((new_opil_measurement, intent))

        return opil_measurement_intent_pairs

    def _validate_parameters_from_lab(self, parameter_fields_from_lab, parameter_fields_from_document):
        # todo
        # Check for required fields.
        is_valid = True
        # for field in parameter_fields_from_lab.values():
        #     if field.is_required() and field.get_field_name() not in parameter_fields_from_document:
        #         self.validation_errors.append('missing required parameter field %s' % field.get_field_name())
        #         is_valid = False
        # # Check for valid values.
        # for name, value in parameter_fields_from_document.items():
        #     if name not in parameter_fields_from_lab:
        #         is_valid = False
        #         self.validation_errors.append('%s is not a supported parameter field for protocol %s' % (name, self.processed_parameter.get_protocol_name()))
        #     elif not parameter_fields_from_lab[name].is_valid_value(value):
        #         is_valid = False
        #         self.validation_errors.append('%s is not a valid parameter value for parameter field %s' % (
        #             value, name))
        # return is_valid
