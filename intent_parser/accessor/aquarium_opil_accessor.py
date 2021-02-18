import intent_parser.utils.intent_parser_utils as ip_utils
import intent_parser.protocols.opil_parameter_utils as opil_utils
import logging

from intent_parser.intent_parser_exceptions import IntentParserException


class AquariumOpilAccessor(object):
    """
    Retrieve experimental request from Aquarium-opil.
    Refer to link for getting aquarium-opil file:
    https://github.com/aquariumbio/aquarium-opil
    """

    logger = logging.getLogger('aqurium_opil_accessor')
    _SUPPORTED_PROTOCOLS = {'jellyfish': 'jellyfish_htc.xml'
                            }

    def __init__(self):
        pass

    def get_experimental_request_as_opil_doc(self, experimental_request_name):
        if experimental_request_name in self._SUPPORTED_PROTOCOLS:
            opil_doc = ip_utils.load_sbol_xml_file(self._SUPPORTED_PROTOCOLS[experimental_request_name])
            return opil_doc

        raise IntentParserException('Aquarium does not support %s as an experimental request' % experimental_request_name)

    def get_protocol_interface(self, protocol_name):
        opil_doc = self.get_experimental_request_as_opil_doc(protocol_name)
        protocol_interfaces = opil_utils.get_protocol_interfaces_from_sbol_doc(opil_doc)
        if len(protocol_interfaces) == 0:
            raise IntentParserException('No opil protocol interface found from aquarium protocol %s' % protocol_name)

        if len(protocol_interfaces) > 1:
            raise IntentParserException('Expected to find one opil protocol interface for %s but more than one was found' % protocol_name)

        return protocol_interfaces[0]