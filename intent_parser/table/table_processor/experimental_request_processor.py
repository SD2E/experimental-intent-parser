from intent_parser.intent.measure_property_intent import MeasuredUnit, ReagentIntent, NamedLink, MediaIntent
from intent_parser.intent.measurement_intent import MeasurementIntent
from intent_parser.intent.parameter_intent import ParameterIntent
from intent_parser.intent.strain_intent import StrainIntent
from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.table.table_processor.processor import Processor
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.utils.sbol3_utils as sbol3_utils
import intent_parser.utils.opil_parameter_utils as opil_utils
import logging


class ExperimentalRequestProcessor(Processor):
    """
    Generate an experiment from a protocol request
    """

    logger = logging.getLogger('protocol_request')

    def __init__(self, opil_document, lab_name):
        super().__init__()
        self._opil_document = opil_document
        self._lab_name = lab_name

    def get_intent(self):
        return None

    def process_protocol(self):
        combinatorial_derivations = sbol3_utils.get_combinatorial_derivations(self._opil_document)
        measurement_intents = self._convert_combinatorial_derivations_to_measurement_intents(combinatorial_derivations)

        experimental_requests = opil_utils.get_opil_experimental_requests(self._opil_document)
        if len(experimental_requests) == 0:
            self.validation_errors.append('No experimental request found from opil document.')
            return
        elif len(experimental_requests) > 1:
            self.validation_errors.append(
                'Expected to get one ExperimentRequests per opil document but more than one were found.')
            return

        experiment_request = experimental_requests[-1]
        if experiment_request.measurements:
            if len(experiment_request.measurements) != len(measurement_intents):
                raise IntentParserException('length of opil.Measurements does not match length of '
                                            'sbol3.CombinatorialDerivations: %d != %d'
                                            % (len(experiment_request.measurements), len(measurement_intents)))
            self._process_opil_measurements(experiment_request.measurements, measurement_intents)

        protocol_interfaces = opil_utils.get_protocol_interfaces_from_sbol_doc(self._opil_document)
        if experiment_request.has_parameter_value:
            self._process_opil_parameters(protocol_interfaces, experiment_request.has_parameter_value)

    def _convert_combinatorial_derivations_to_measurement_intents(self, combinatorial_derivations):
        measurement_intents = []
        # each combinatorial_derivation corresponds to a measurement row in a measurement table
        for combinatorial_derivation in combinatorial_derivations:
            experiment_template = combinatorial_derivation.template
            # features assigned to an experimental_template corresponds to measurement table headers
            experiment_features = experiment_template.features

            # variable_features are values assigned under a measurement header
            for variable_feature in combinatorial_derivation.variable_features:
                measurement_intent = self._convert_variable_feature_to_measurement_intent(variable_feature)
                measurement_intents.append(measurement_intent)

        return measurement_intents

    def _convert_variable_feature_to_measurement_intent(self, variable_feature):
        measurement_intent = MeasurementIntent()
        measurement_header_component = variable_feature.variable

        if measurement_header_component.type == ip_constants.NCIT_INDUCER_URI or measurement_header_component.type == ip_constants.NCIT_REAGENT_URI:
            inducer_or_reagent_header_name = self._create_measurement_header_name(measurement_header_component)
            self._add_inducer_or_reagent_to_measurement(measurement_intent,
                                                        inducer_or_reagent_header_name,
                                                        variable_feature.variant_measures)
        elif measurement_header_component.type == ip_constants.NCIT_MEDIA_URI:
            media_header_name = self._create_measurement_header_name(measurement_header_component)
            self._add_media_to_measurement(measurement_intent,
                                           media_header_name,
                                           variable_feature.variants)
        elif measurement_header_component.type == ip_constants.NCIT_STRAIN_URI:
            self._add_strain_to_measurement(measurement_intent,
                                            variable_feature.variants)
        else:
            self.validation_errors.append('%s is not a supported measurement field' % measurement_header_component.type)

        return measurement_intent

    def _create_measurement_header_name(self, measurement_header_component):
        if measurement_header_component.features:
            # if there is a link referencing this media, record it.
            measurement_header_subcomponents = measurement_header_component.features
            measurement_header_link = measurement_header_subcomponents[0].instance_of
            measurement_header_name = NamedLink(measurement_header_component.name,
                                                link=measurement_header_link)
            return measurement_header_name

        return NamedLink(measurement_header_component.name)

    def _add_inducer_or_reagent_to_measurement(self, measurement_intent, inducer_name, sbol_variant_measures):
        inducer_intent = ReagentIntent(inducer_name)
        for opil_measure in sbol_variant_measures:
            inducer_value = opil_measure.value
            if opil_measure.unit == ip_constants.OTU_MICROLITRE:
                measured_unit = MeasuredUnit(inducer_value,
                                             ip_constants.FLUID_UNIT_MICROLITRE,
                                             unit_type=ip_constants.UNIT_TYPE_FLUID)
                inducer_intent.add_reagent_value(measured_unit)
            elif opil_measure.unit == ip_constants.NCIT_CONCENTRATION_ENTITY_POOL:
                # todo: unit not supported for structured request
                measured_unit = MeasuredUnit(inducer_value,
                                             'entity per unit of volume',
                                             unit_type=ip_constants.UNIT_TYPE_FLUID)
                inducer_intent.add_reagent_value(measured_unit)
        measurement_intent.add_content(inducer_intent)

    def _add_media_to_measurement(self, measurement_intent, media_name, sbol_variants):
        media_intent = MediaIntent(media_name)
        for media_component in sbol_variants:
            if media_component.features:
                media_subcomponents = media_component.features
                # media can only have one sbh link assigned to its value
                media_link = media_subcomponents[0].instance_of
                media_value = NamedLink(media_component.name, link=media_link)
                media_intent.add_media_value(media_value)
            else:
                media_value = NamedLink(media_component.name)
                media_intent.add_media_value(media_value)

        measurement_intent.add_content(media_intent)

    def _add_strain_to_measurement(self, measurement_intent, sbol_variants):
        for strain_component in sbol_variants:
            if strain_component.features:
                strain_subcomponents = strain_component.features
                strain_link = strain_subcomponents[0].instance_of
                strain_name = NamedLink(strain_component.name, link=strain_link)
                strain_intent = StrainIntent(strain_name)
                measurement_intent.add_strain(strain_intent)
            else:
                strain_name = NamedLink(strain_component.name)
                strain_intent = StrainIntent(strain_name)
                measurement_intent.add_strain(strain_intent)

    def _process_opil_measurements(self, opil_measurements, measurement_intents):
        for opil_measurement_index in range(len(opil_measurements)):
            # IP creates opil custom annotation for the following fields:
            #    - file-type
            #    - controls
            #    - column_ids, dna_reaction_concentrations, lab_ids, num_neg_controls, rna_inhibitor_reaction_flags
            #    - row_ids, template_dna_values
            # These fields do not appear in other opil lab document so skip.
            # The remaining fields map to a measurement intent.
            # opil does not reference each opil_measurement object to an sbol3
            # CombinatorialDerivation so map by order that these objects are encountered in a list to its
            # measurement_intent created from parsing sbol3.CombinatorialDerivations.
            opil_measurement = opil_measurements[opil_measurement_index]
            measurement_intent = measurement_intents[opil_measurement_index]
            if opil_measurement.time:
                self._convert_opil_measurement_time_to_timepoints(opil_measurement.time, measurement_intent)

            if opil_measurement.instance_of:
                self._convert_opil_measurement_type_to_measurement_type(opil_measurement.instance_of, measurement_intent)

    def _convert_opil_measurement_type_to_measurement_type(self, opil_measurement_type, measurement_intent):
        opil_measurement_type_uri = opil_measurement_type.type
        for measurement_type, measurement_type_uri in ip_constants.MEASUREMENT_TYPE_MAPPINGS.items():
            if opil_measurement_type_uri == measurement_type_uri:
                measurement_intent.set_measurement_type(measurement_type)
                return

    def _convert_opil_measurement_time_to_timepoints(self, opil_times, measurement_intent):
        for opil_measure in opil_times:
            value = opil_measure.has_measure.value
            unit_uri = opil_measure.has_measure.unit
            unit = sbol3_utils.get_unit_name_from_timepoint_uri(unit_uri)
            if unit:
                timepoint = MeasuredUnit(value, unit, unit_type=ip_constants.UNIT_TYPE_TIMEPOINTS)
                measurement_intent.add_timepoint(timepoint)
            else:
                self.validation_errors.append('timepoint unit not supported in Intent Parser: %s' % unit_uri)

    def _process_opil_parameters(self, protocol_interfaces, opil_parameter_values):
        parameter_intent = ParameterIntent()
        opil_parameter_fields = protocol_interfaces.has_parameter
        for parameter_value in opil_parameter_values:
            parameter_field = parameter_value.value_of
            parameter_intent.add_parameter(parameter_field.name, parameter_value.value)


