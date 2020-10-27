from datetime import timedelta
from intent_parser.intent_parser_exceptions import IntentParserException
from transcriptic import Connection
import intent_parser.constants.intent_parser_constants as ip_constants
import logging
import opil
import time
import threading

class StrateosAccessor(object):
    """
    Retrieve protocols from Strateos
    """
    SYNC_PERIOD = timedelta(minutes=60)
    logger = logging.getLogger('intent_parser_strateos_accessor')

    def __init__(self, credential_path=None, use_cache=True):
        if credential_path:
            self.strateos_api = Connection.from_file(credential_path)
        else:
            self.strateos_api = Connection.from_default_config()

        self._use_cache = use_cache

        self.protocol_lock = threading.Lock()
        self._map_name_protocol_docs = {}
        self._map_name_to_protocol_interface = {}
        self._map_name_to_protocol_id = {}
        self._protocol_thread = threading.Thread(target=self._periodically_fetch_protocols)

    def get_list_of_protocol_interface(self):
        return self._map_name_to_protocol_interface.values()

    def get_protocol_parameter_values(self, protocol_name):
        if protocol_name not in self._map_name_to_protocol_interface:
            raise IntentParserException('Unable to identify %s as a protocol supported from Strateos' % protocol_name)

        parameter_values = []
        sbol_doc = self._map_name_protocol_docs[protocol_name]
        for obj in sbol_doc.objects:
            if type(obj) is opil.opil_factory.ProtocolInterface:
                continue
            parameter_values.append(obj)

        return parameter_values

    def get_protocol_id(self, protocol_name):
        if protocol_name not in self._map_name_to_protocol_id:
            raise IntentParserException('Unable to get protocol id: %s is not a supported protocol in Strateos.' % protocol_name)
        return self._map_name_to_protocol_id[protocol_name]

    def get_protocol_interface(self, protocol_name):
        if not self._use_cache:
            self._fetch_protocols()
            return self._map_name_to_protocol_interface[protocol_name]

        if protocol_name not in self._map_name_to_protocol_interface:
            raise IntentParserException('Unable to identify %s as a protocol supported from Strateos' % protocol_name)

        return self._map_name_to_protocol_interface[protocol_name]

    def get_protocol_as_schema(self, protocol):
        """
        Get default parameter values for a given protocol.

        Args:
            protocol: name of protocol

        Return:
            A dictionary. The key represent a parameter.
                The value represents a parameter's default value.

        Raises:
            An Exception to indicate if a given protocol does not exist when calling the Strateos API.
        """
        self.protocol_lock.acquire()
        if protocol not in self._map_name_protocol_docs:
            raise Exception('Unable to get %s from Strateos' % protocol)

        selected_protocol = self._map_name_protocol_docs[protocol]
        self.protocol_lock.release()
        return selected_protocol

    def start_synchronize_protocols(self):
        self._fetch_protocols()
        self._protocol_thread.start()

    def stop_synchronizing_protocols(self):
        self._protocol_thread.join()

    def _periodically_fetch_protocols(self):
        while True:
            time.sleep(self.SYNC_PERIOD.total_seconds())
            self._fetch_protocols()

    def _fetch_protocols(self):
        self.logger.info('Fetching strateos')
        protocol_list = self.strateos_api.get_protocols()

        self.protocol_lock.acquire()
        supported_protocols = [ip_constants.CELL_FREE_RIBO_SWITCH_PROTOCOL,
                               ip_constants.GROWTH_CURVE_PROTOCOL,
                               ip_constants.OBSTACLE_COURSE_PROTOCOL,
                               ip_constants.TIME_SERIES_HTP_PROTOCOL]
        for protocol in protocol_list:
            if protocol['name'] not in supported_protocols:
                continue

            self.logger.info('Fetching protocol %s' % protocol['name'])
            protocol_interface, sbol_doc = self._convert_protocol_as_opil(protocol)
            self._map_name_to_protocol_id[protocol['name']] = protocol['id']
            self._map_name_to_protocol_interface[protocol['name']] = protocol_interface
            self._map_name_protocol_docs[protocol['name']] = sbol_doc
        self.protocol_lock.release()

    def _convert_protocol_as_opil(self, protocol):
        strateos_namespace = 'http://strateos.com/'
        sg = opil.StrateosOpilGenerator()
        sbol_doc = sg.parse_strateos_json(strateos_namespace,
                                          protocol['name'],
                                          protocol['id'],
                                          protocol['inputs'])
        protocol_interface = None
        for obj in sbol_doc.objects:
            if type(obj) is opil.opil_factory.ProtocolInterface:
                protocol_interface = obj

        if not protocol_interface:
            raise IntentParserException('Unable to locate OPIL protocol interface when converting transcriptic protocols to OPIL')

        return protocol_interface, sbol_doc

