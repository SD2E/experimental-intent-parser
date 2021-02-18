from intent_parser.intent.control_intent import ControlIntent
from intent_parser.intent.lab_intent import LabIntent
from intent_parser.intent.measurement_intent import MeasurementIntent
from intent_parser.intent.parameter_intent import ParameterIntent
import logging

class ExperimentalRequestIntent(object):
    """
    Intent Parser's representation of an experimental request
    """

    logger = logging.getLogger('experimental_request_intent')

    def __init__(self, experimental_request_name=''):
        self._experimental_request_name = experimental_request_name
        self._lab_intent = LabIntent()
        self._measurement_intents = []
        self._control_intent = ControlIntent()
        self._parameter_intent = ParameterIntent()

    def add_measurement_intent(self, measurement_intent):
        self._measurement_intents.add(measurement_intent)