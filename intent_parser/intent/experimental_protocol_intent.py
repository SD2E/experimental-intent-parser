from intent_parser.intent.control_intent import ControlIntent
from intent_parser.intent.lab_intent import LabIntent
from intent_parser.intent.parameter_intent import ParameterIntent
import logging

class ExperimentalProtocolIntent(object):
    """
    Intent Parser's representation of an experimental protocol
    """

    logger = logging.getLogger('experimental_request_intent')

    def __init__(self, lab_intent: LabIntent, parameter_intent: ParameterIntent, measurement_intents: list):
        self._lab_intent = lab_intent
        self._measurement_intents = measurement_intents
        self._control_intent = ControlIntent()
        self._parameter_intent = parameter_intent
