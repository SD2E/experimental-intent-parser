from datetime import timedelta
from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.protocols.labs.opil_lab_accessor import OpilLabAccessors
from intent_parser.protocols.templates.experimental_request_template import OpilDocumentTemplate
from transcriptic import Connection
import intent_parser.constants.intent_parser_constants as ip_constants
import logging
import opil
import time
import threading
import sbol3

class StrateosAccessor(OpilLabAccessors):
    """
    Retrieve protocols from Strateos
    """
    SYNC_PERIOD = timedelta(minutes=60)
    logger = logging.getLogger('intent_parser_strateos_accessor')

    def __init__(self, credential_path=None, use_cache=True):
        super().__init__()
        if credential_path:
            self.strateos_api = Connection.from_file(credential_path)
        else:
            self.strateos_api = Connection.from_default_config()

        self._use_cache = use_cache
        self.protocol_lock = threading.Lock()
        self._name_to_json = {}
        self._protocol_thread = threading.Thread(target=self._periodically_fetch_protocols)

    def get_experimental_protocol(self, experimental_request_name):
        if experimental_request_name not in self._name_to_json:
            raise IntentParserException('Protocol not supported by Strateos: %s' % experimental_request_name)
        protocol = self._name_to_json[experimental_request_name]
        return self._convert_protocol_to_opil(protocol)

    def get_experimental_protocol_names(self):
        return list(self._name_to_json.keys())

    def start_synchronize_protocols(self):
        self._fetch_protocols()
        self._protocol_thread.start()

    def stop_synchronizing_protocols(self):
        self._protocol_thread.join()

    def _convert_protocol_to_opil(self, protocol):
        protocol_name = protocol['name']
        sg = opil.StrateosOpilGenerator()
        opil_doc = sg.parse_strateos_json(ip_constants.STRATEOS_NAMESPACE,
                                          protocol_name,
                                          protocol['id'],
                                          protocol['inputs'])

        template = OpilDocumentTemplate()
        template.load_from_template(opil_doc)
        return template

    def _fetch_protocols(self):
        self.logger.info('Fetching strateos')
        protocol_list = self.strateos_api.get_protocols()

        self.protocol_lock.acquire()
        for protocol in protocol_list:
            self.logger.info('Fetching protocol %s' % protocol['name'])
            protocol_name = protocol['name']
            self._name_to_json[protocol_name] = protocol
        self.protocol_lock.release()

    def _periodically_fetch_protocols(self):
        while True:
            time.sleep(self.SYNC_PERIOD.total_seconds())
            self._fetch_protocols()