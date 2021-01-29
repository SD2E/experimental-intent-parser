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

    def __init__(self):
        self._lab_intent = LabIntent()
        self._measurement_intent = MeasurementIntent()
        self._control_intent = ControlIntent()
        self._parameter_intent = ParameterIntent()