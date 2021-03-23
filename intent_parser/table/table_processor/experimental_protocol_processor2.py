from intent_parser.intent.measurement_intent import MeasurementIntent
from intent_parser.intent.parameter_intent import ParameterIntent
from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.protocols.templates.experimental_request_template import OpilDocumentTemplate
from intent_parser.table.table_processor.processor import Processor
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.utils.opil_utils as opil_utils
import logging

class ExperimentalProtocolProcessor2(Processor):
    """
    Generate an experiment from a protocol request
    """

    logger = logging.getLogger('experimental_protocol_processor')

    def __init__(self, opil_document_template: OpilDocumentTemplate, lab_name: str, lab_protocol: str):
        super().__init__()
        self._opil_document_template = opil_document_template
        self._lab_name = lab_name
        self._lab_protocol = lab_protocol
        self._measurement_intents = []
        self._parameter_intent = None

    def get_intent(self):
        pass

    def process_protocol_interface(self):
        protocol_interfaces = self._opil_document_template.get_protocol_interfaces()
        if not protocol_interfaces:
            raise IntentParserException('No lab ProtocolInterface found.' % protocol_interfaces[0].identity)
        if len(protocol_interfaces) > 1:
            raise IntentParserException('Expecting 1 ProtocolInterface but %d were found' % len(protocol_interfaces))

        protocol_interface = protocol_interfaces[0]
        self._process_protocol_measurement_type(protocol_interface.protocol_measurement_type)
        self._process_parameters(protocol_interface.has_parameter)
        self._process_sample_set(protocol_interface.allowed_samples)

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
            parameter_intent = ParameterIntent()
            if not opil_parameter.name:
                raise IntentParserException('No name assigned to Parameter %s.' % opil_parameter.identity)
            parameter_name = opil_parameter.name

            if opil_parameter.identity in parameter_id_to_param_value:
                opil_parameter_value = parameter_id_to_param_value[opil_parameter.identity]
                string_parameter_value = opil_utils.get_param_value_as_string(opil_parameter_value)
                parameter_intent.add_parameter(parameter_name, string_parameter_value)
            else:
                parameter_intent.add_parameter(parameter_name, ' ')
            self._parameter_intent.append(parameter_intent)

    def _process_sample_set(self, samplesets):
        uris_to_components = {}
        unique_sample_templates = {}
        # collect components
        for component in self._opil_document_template.get_components():
            if component.identity not in uris_to_components:
                uris_to_components[component.identity] = component
            else:
                if uris_to_components[component.identity]:
                    raise IntentParserException('conflict mapping opil.Components with same identity.')
        # sort sampleset by unique templates
        for sample in samplesets:
            sample.template # uri to a component
            sample.variable_features # objects
            if sample.template not in unique_sample_templates:
                unique_sample_templates[sample.template] = []
            unique_sample_templates[sample.template].append(sample)
        if len(unique_sample_templates) != 1:
            raise IntentParserException('Intent Parser limits 1 measurement table template but %d were found.'
                                        % len(unique_sample_templates))
        table_template = list(unique_sample_templates.keys())[0]
        self._process_variable_features(samplesets)


    def _process_variable_features(self, variable_features):
        for variable_feature in variable_features:
            variable_feature.variable # get header name
            variable_feature.variant
            variable_feature.variant_measure
            variable_feature.variant_derivation
