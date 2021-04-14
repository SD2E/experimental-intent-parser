from intent_parser.intent.lab_intent import LabIntent
from intent_parser.intent.measure_property_intent import NamedLink, ReagentIntent, MeasuredUnit, MediaIntent, \
    TemperatureIntent
from intent_parser.intent.measurement_intent import MeasurementIntent, ContentIntent
from intent_parser.intent.parameter_intent import ParameterIntent
from intent_parser.intent.strain_intent import StrainIntent
from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.protocols.templates.experimental_request_template import OpilDocumentTemplate
from intent_parser.table.table_creator import TableCreator
from intent_parser.table.table_processor.processor import Processor
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.utils.opil_utils as opil_utils
import intent_parser.utils.sbol3_utils as sbol3_utils
import logging

class ExperimentalProtocolProcessor(Processor):
    """
    Generate an experiment from a protocol request
    """

    logger = logging.getLogger('experimental_protocol_processor')

    def __init__(self, opil_document_template: OpilDocumentTemplate, lab_name: str):
        super().__init__()
        self._opil_document_template = opil_document_template
        self._lab_intent = LabIntent()
        self._lab_intent.set_lab_id(lab_name)
        self._measurement_intents = []
        self._parameter_intent = ParameterIntent()
        self._experimental_protocol_intent = {}

    def get_intent(self):
        return self._experimental_protocol_intent

    def process_protocol_interface(self):
        protocol_interfaces = self._opil_document_template.get_protocol_interfaces()
        if not protocol_interfaces:
            raise IntentParserException('No ProtocolInterface found for lab: %s' % self._lab_intent.get_lab_name())
        if len(protocol_interfaces) > 1:
            raise IntentParserException('Expecting 1 ProtocolInterface but %d were found' % len(protocol_interfaces))

        protocol_interface = protocol_interfaces[0]
        if protocol_interface.name:
            self._parameter_intent.set_protocol_name(protocol_interface.name)
        self._process_protocol_measurement_type(protocol_interface.protocol_measurement_type)
        self._process_parameters(protocol_interface.has_parameter)
        self._process_sample_set(self._get_samplesets(protocol_interface.allowed_samples))
        self._process_output()

    def _get_samplesets(self, sampleset_uris):
        uris_to_samplesets = {}
        for sample in self._opil_document_template.get_sample_sets():
            uris_to_samplesets[sample.identity] = sample

        samplesets = []
        for uri in sampleset_uris:
            uri_string = str(uri)
            if uri_string not in uris_to_samplesets:
                raise IntentParserException('Unable to locate SampleSet with identity: %s' % uri_string)
            samplesets.append(uris_to_samplesets[uri_string])
        return samplesets

    def _process_output(self):
        table_creator = TableCreator()
        lab_table = table_creator.create_lab_table_from_intent(self._lab_intent)
        self._experimental_protocol_intent['labTable'] = lab_table
        if len(self._measurement_intents) > 0:
            measurement_table = table_creator.create_measurement_table_from_intents(self._measurement_intents)
            self._experimental_protocol_intent['measurementTable'] = measurement_table
        if self._parameter_intent.size_of_default_parameters() > 0:
            parameter_table = table_creator.create_parameter_table_from_intent(self._parameter_intent)
            self._experimental_protocol_intent['parameterTable'] = parameter_table


    def _process_protocol_measurement_type(self, measurement_types):
        for opil_measurement_type in measurement_types:
            measurement_intent = MeasurementIntent()
            if opil_measurement_type.type == ip_constants.NCIT_FLOW_URI:
                measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_FLOW)
            elif opil_measurement_type.type == ip_constants.NCIT_RNA_SEQ_URI:
                measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_RNA_SEQ)
            elif opil_measurement_type.type == ip_constants.NCIT_DNA_SEQ_URI:
                measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_DNA_SEQ)
            elif opil_measurement_type.type == ip_constants.NCIT_PROTEOMICS_URI:
                measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_PROTEOMICS)
            elif opil_measurement_type.type == ip_constants.NCIT_SEQUENCING_CHROMATOGRAM_URI:
                measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_SEQUENCING_CHROMATOGRAM)
            elif opil_measurement_type.type == ip_constants.SD2_AUTOMATED_TEST_URI:
                measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_AUTOMATED_TEST)
            elif opil_measurement_type.type == ip_constants.NCIT_CFU_URI:
                measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_CFU)
            elif opil_measurement_type.type == ip_constants.NCIT_PLATE_READER_URI:
                measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_PLATE_READER)
            elif opil_measurement_type.type == ip_constants.SD2_CONDITION_SPACE_URI:
                measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE)
            elif opil_measurement_type.type == ip_constants.SD2_EXPERIMENTAL_DESIGN_URI:
                measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_EXPERIMENTAL_DESIGN)
            elif opil_measurement_type.type == ip_constants.NCIT_FLUORESCENCE_MICROSCOPY:
                measurement_intent.set_measurement_type(ip_constants.MEASUREMENT_TYPE_FLUOESCENE_MICROSCOPY)
            else:
                raise IntentParserException('Measurement-type %s not supported in Intent parser'
                                            % opil_measurement_type.type)
            self._measurement_intents.append(measurement_intent)

    def _process_parameters(self, parameters):
        parameter_id_to_param_value = {}
        for opil_parameter_value in self._opil_document_template.get_parameter_values():
            if not opil_parameter_value.value_of:
                raise IntentParserException('No value assigned to ParameterValue %s' % opil_parameter_value.identity)
            parameter_id_to_param_value[opil_parameter_value.value_of] = opil_parameter_value

        for opil_parameter in parameters:
            if not opil_parameter.name:
                raise IntentParserException('No name assigned to Parameter %s.' % opil_parameter.identity)
            parameter_name = opil_parameter.name

            if opil_parameter.identity in parameter_id_to_param_value:
                opil_parameter_value = parameter_id_to_param_value[opil_parameter.identity]
                string_parameter_value = opil_utils.get_param_value_as_string(opil_parameter_value)
                self._parameter_intent.add_parameter(parameter_name, string_parameter_value)
            else:
                self._parameter_intent.add_parameter(parameter_name, ' ')

    def _process_sample_set(self, samplesets):
        uris_to_components = {}
        # collect components
        for component in self._opil_document_template.get_components():
            if component.identity not in uris_to_components:
                uris_to_components[component.identity] = component
            else:
                if uris_to_components[component.identity]:
                    raise IntentParserException('conflict mapping opil.Components with same identity.')
        if len(samplesets) > len(self._measurement_intents):
            raise IntentParserException('Number of SampleSets must be less than or equal to number of '
                                        'IP measurement-intent: %d > %d'
                                        % (len(samplesets), len(self._measurement_intents)))

        uris_to_local_and_subcomponents = self._process_sampleset_templates(samplesets, uris_to_components)
        for index in range(len(samplesets)):
            sample = samplesets[index]
            measurement_intent = self._measurement_intents[index]
            # todo: replicate not supported in opil
            # if sample.replicates:
            #     measurement_intent.add_replicate(int(sample.replicates[0]))

            self._process_variable_features(sample.variable_features,
                                            uris_to_local_and_subcomponents,
                                            uris_to_components,
                                            measurement_intent)

    def _process_sampleset_templates(self, samplesets, uris_to_components):
        uris_to_template = {}
        for sample in samplesets:
            str_template = str(sample.template)
            if not sample.template:
                raise IntentParserException('A SampleSet must have a template but none was set: %s' % sample.identity)
            if str_template not in uris_to_components:
                raise IntentParserException('No Component found for SampleSet.template: %s' % str_template)
            uris_to_template[str_template] = uris_to_components[str_template]

        if len(uris_to_template) != 1:
            raise IntentParserException('Expecting one unique SampleSet.template but %d found' % len(uris_to_template))

        uris_to_local_and_subcomponents = {}
        for template in uris_to_template.values():
            for feature in template.features:
                uris_to_local_and_subcomponents[feature.identity] = feature
        return uris_to_local_and_subcomponents

    def _process_variable_features(self, variable_features, uris_to_localsubcomponents, uris_to_components, measurement_intent):
        for variable_feature in variable_features:
            if not variable_feature.variable:
                raise IntentParserException('No variable set to VariableFeature %s' % variable_feature.identity)
            str_variable = str(variable_feature.variable)
            if str_variable not in uris_to_localsubcomponents:
                raise IntentParserException('No LocalSubComponent found with id: %s' % str_variable)

            content_intent = ContentIntent()
            local_or_subcomponent_template = uris_to_localsubcomponents[str_variable]
            if ip_constants.NCIT_STRAIN_URI in local_or_subcomponent_template.roles:
                self._process_variants_as_strain_values(variable_feature.variants,
                                                        measurement_intent,
                                                        uris_to_components)
            elif ip_constants.NCIT_MEDIA_URI in local_or_subcomponent_template.roles:
                if variable_feature.variant_measures:
                    self._add_temperature_values_from_variant_measures(variable_feature.variant_measure,
                                                                       measurement_intent)
                media_name = NamedLink(local_or_subcomponent_template.name)
                media_intent = MediaIntent(media_name)
                if variable_feature.variants:
                    self._add_media_values_from_variants(variable_feature.variants,
                                                         media_intent,
                                                         uris_to_components)
                content_intent.add_media(media_intent)
                measurement_intent.add_content(content_intent)
            elif (ip_constants.NCIT_INDUCER_URI in local_or_subcomponent_template.roles
                  or ip_constants.NCIT_REAGENT_URI in local_or_subcomponent_template.roles):
                # process as reagent
                reagent_name = NamedLink(local_or_subcomponent_template.name)
                reagent_intent = ReagentIntent(reagent_name)
                self._add_reagent_values_from_variant_measures(variable_feature.variant_measures,
                                                               reagent_intent)
                content_intent.add_reagent(reagent_intent)
                measurement_intent.add_content(content_intent)
            else:
                # process unidentified opil.LocalSubComponent as reagent or media base of of its value encoding
                if variable_feature.variant_measures:
                    reagent_name = NamedLink(local_or_subcomponent_template.name)
                    reagent_intent = ReagentIntent(reagent_name)
                    self._add_reagent_values_from_variant_measures(variable_feature.variant_measures,
                                                                   reagent_intent)
                    content_intent.add_reagent(reagent_intent)
                    measurement_intent.add_content(content_intent)
                elif variable_feature.variants:
                    media_name = NamedLink(local_or_subcomponent_template.name)
                    media_intent = MediaIntent(media_name)
                    self._add_media_values_from_variants(variable_feature.variants,
                                                         media_intent,
                                                         uris_to_components)
                    content_intent.add_media(media_intent)
                    measurement_intent.add_content(content_intent)

    def _process_variants_as_strain_values(self, variants, measurement_intent, uris_to_components):
        # no default values provided for strains
        if not variants:
            strain_name = NamedLink(' ')
            strain_intent = StrainIntent(strain_name)
            measurement_intent.add_strain(strain_intent)
            return
        # strains were provided in template
        for variant in variants:
            if variant not in uris_to_components:
                raise IntentParserException('Strain variant not found: %s' % variant)
            strain_component = uris_to_components[variant]
            strain_name = NamedLink(strain_component.name)
            strain_intent = StrainIntent(strain_name)
            measurement_intent.add_strain(strain_intent)

    def _add_media_values_from_variants(self, variants, media_intent, uris_to_components):
        for variant in variants:
            if variant not in uris_to_components:
                raise IntentParserException('No Component found for Media variant: %s' % variant)
            media_component = uris_to_components[variant]
            media_value = NamedLink(media_component.name)
            media_intent.add_media_value(media_value)

    def _add_reagent_values_from_variant_measures(self, variant_measures, reagent_intent):
        for variant_measure in variant_measures:
            unit_name = sbol3_utils.get_unit_name_from_uri(variant_measure.unit)
            measured_unit = MeasuredUnit(variant_measure.value, unit_name)
            reagent_intent.add_reagent_value(measured_unit)

    def _add_temperature_values_from_variant_measures(self, variant_measures, measurement_intent):
        for variant_measure in variant_measures:
            unit_name = sbol3_utils.get_unit_name_from_uri(variant_measure.unit)
            measured_unit = MeasuredUnit(variant_measure.value, unit_name)
            timepoint_intent = TemperatureIntent(measured_unit)
            measurement_intent.add_timepoint(timepoint_intent)

