from intent_parser.intent.experimental_request_intent import ExperimentalRequestIntent
from intent_parser.intent.measure_property_intent import MeasuredUnit
from intent_parser.intent.measurement_intent import MeasurementIntent
from intent_parser.table.table_processor.processor import Processor

import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.utils.sbol3_utils as sbol3_utils
import intent_parser.protocols.opil_parameter_utils as opil_utils
import logging

class ExperimentalRequestProcessor(Processor):
    """
    Intent Parser's representation of generating an experiment from protocol request
    """

    logger = logging.getLogger('protocol_request')

    def __init__(self, opil_document):
        super().__init__()
        self._opil_document = opil_document
        self._protocol_intent = None

    def get_intent(self):
        return self._protocol_intent

    def process_protocol(self):
        self._process_combinatorial_derivations()
        experimental_requests = opil_utils.get_opil_experimental_request(self._opil_document)
        protocol_interfaces = opil_utils.get_protocol_interfaces_from_sbol_doc(self._opil_document)
        if len(experimental_requests) == 0:
            self.validation_errors.append('No experimental request found from opil document.')
            return
        elif len(experimental_requests) > 1:
            self.validation_errors.append('Expected to get one ExperimentRequests per opil document but more than one were found.')
            return

        self._process_experiment_request(experimental_requests[-1], protocol_interfaces)

    def _process_combinatorial_derivations(self):
        combinatorial_derivations = sbol3_utils.get_combinatorial_derivations(self._opil_document)
        for combinatorial_derivation in combinatorial_derivations:
            combinatorial_derivation.template
            combinatorial_derivation.variable_features

    def _process_experiment_request(self, experiment_request, protocol_interfaces):
        if experiment_request.name:
            self._protocol_intent = ExperimentalRequestIntent(experiment_request.name)
        else:
            self._protocol_intent = ExperimentalRequestIntent()

        if experiment_request.measurements:
            self._process_opil_measurements(experiment_request.measurements)

        if experiment_request.has_parameter_value:
            self._process_opil_parameters(protocol_interfaces, experiment_request.has_parameter_value)


    def _process_opil_measurements(self, opil_measurements):
        measurement_intents = []
        for opil_measurement in opil_measurements:
            # opil custom annotation created for IP:
            #    - file-type
            #    - controls
            #    - column_ids, dna_reaction_concentrations, lab_ids, num_neg_controls, rna_inhibitor_reaction_flags
            #    - row_ids, template_dna_values
            # This does not appear in other opil lab document so skip.
            measurement_intent = MeasurementIntent()

            if opil_measurement.time:
                self._process_opil_timepoints(opil_measurement.time, measurement_intent)

            if opil_measurement.instance_of:
                measurement_type = self._process_opil_measurement_type(opil_measurement.instance_of)
                if measurement_type:
                    measurement_intent.set_measurement_type(measurement_type)

            measurement_intents.append(measurement_intent)

        return measurement_intents

    def _process_opil_measurement_type(self, opil_measurement_type):
        measurement_type = ''
        opil_measurement_type_uri = opil_measurement_type.type
        for measurement_type, measurement_type_uri in ip_constants.MEASUREMENT_TYPE_MAPPINGS.items():
            if opil_measurement_type_uri == measurement_type_uri:
                measurement_type = measurement_type
        return measurement_type

    def _process_opil_timepoints(self, opil_times, measurement_intent):
        for opil_measure in opil_times:
            value = opil_measure.has_measure.value
            # TODO: convert unit_uri to unit name that IP supports from Google doc.
            unit_uri = opil_measure.has_measure.unit
            timepoint = MeasuredUnit(value, '', unit_type=ip_constants.UNIT_TYPE_TIMEPOINT)
            measurement_intent.add_timepoint(timepoint)

    def _process_opil_parameters(self, protocol_interfaces, opil_parameter_values):
        pass