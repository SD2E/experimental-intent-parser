import intent_parser.protocols.opil_parameter_utils as opil_utils
import logging

from intent_parser.intent.experimental_request_intent import ExperimentalRequestIntent
from intent_parser.table.table_processor.processor import Processor

class ExperimentalRequestProcessor(Processor):
    """
    Intent Parser's representation of an experimental request
    """

    logger = logging.getLogger('experimental_request')

    def __init__(self):
        self._experiment_request_intents = []

    def get_intent(self):
        pass

    def process_opil_experimental_requst(self, opil_document):
        experimental_requests = opil_utils.get_opil_experimental_request(opil_document)
        if len(experimental_requests) == 0:
            self.validation_errors.append('No experimental request found')
            return

        for experiment_request in experimental_requests:
            self._process_experiment_request(experiment_request)

    def _process_experiment_request(self, experiment_request):
        pass