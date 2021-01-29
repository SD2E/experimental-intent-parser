from datetime import timedelta
from intent_parser.intent_parser_exceptions import IntentParserException
from transcriptic import Connection
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.protocols.opil_parameter_utils as opil_utils
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
            raise IntentParserException('%s is not an identified protocol at Strateos' % protocol_name)

        parameter_values = []
        sbol_doc = self._map_name_protocol_docs[protocol_name]
        for obj in sbol_doc.objects:
            if type(obj) is opil.opil_factory.ProtocolInterface:
                continue
            parameter_values.append(obj)

        return parameter_values

    def get_protocol_parameter_fields(self, protocol_name):
        """
        Retreive parameter fields supported for a given protocol
        Args:
            protocol_name: name of protocol
        Returns:
            Protocol fields returned as a dict.
            The key represents a protocol field name, the value represents an opil object of the parameter field.
        """
        protocol_fields = {}
        protocol_interface = self.get_protocol_interface(protocol_name)
        for opil_param in protocol_interface.has_parameter:
            if opil_param.dotname:
                protocol_fields[opil_param.dotname] = opil_param
        return protocol_fields

    def get_protocol_id(self, protocol_name) -> str:
        if protocol_name not in self._map_name_to_protocol_id:
            raise IntentParserException(
                'Unable to get protocol id: %s is not a supported protocol in Strateos.' % protocol_name)
        return self._map_name_to_protocol_id[protocol_name]

    def get_protocol_interface(self, protocol_name):
        if not self._use_cache:
            self._fetch_protocols()
            return self._map_name_to_protocol_interface[protocol_name]

        if protocol_name not in self._map_name_to_protocol_interface:
            raise IntentParserException('Unable to identify %s as a protocol supported from Strateos' % protocol_name)

        return self._map_name_to_protocol_interface[protocol_name]

    def get_protocol_as_schema(self, protocol_name):
        protocol_list = self.strateos_api.get_protocols()
        selected_protocol = None
        for protocol in protocol_list:
            if protocol['name'] == protocol_name:
                selected_protocol = protocol

        if not selected_protocol:
            raise IntentParserException('Strateos does not support %s as a protocol' % protocol_name)

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
            protocol_interface, sbol_doc = self.convert_protocol_to_opil(protocol)
            self._map_name_to_protocol_id[protocol['name']] = protocol['id']
            self._map_name_to_protocol_interface[protocol['name']] = protocol_interface
            self._map_name_protocol_docs[protocol['name']] = sbol_doc
        self.protocol_lock.release()

    def convert_protocol_to_opil(self, protocol):
        strateos_namespace = 'http://strateos.com/'
        protocol_name = protocol['name']
        sg = opil.StrateosOpilGenerator()
        sbol_doc = sg.parse_strateos_json(strateos_namespace,
                                          protocol_name,
                                          protocol['id'],
                                          protocol['inputs'])
        protocol_interfaces = opil_utils.get_protocol_interfaces_from_sbol_doc(sbol_doc)
        if len(protocol_interfaces) == 0:
            raise IntentParserException('Unable to locate OPIL protocol interface when converting transcriptic protocol for %s ' % protocol_name)
        if len(protocol_interfaces) > 1:
            raise IntentParserException(
                'Expected to find one opil protocol interface for %s but more than one was found' % protocol_name)

        return protocol_interfaces[0], sbol_doc

