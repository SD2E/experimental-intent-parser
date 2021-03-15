from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.protocols.templates.experimental_request_template import OpilDocumentTemplate
import intent_parser.utils.intent_parser_utils as ip_utils
import intent_parser.utils.opil_utils as opil_utils
import logging
import os


class AquariumOpilAccessor(object):
    """
    Retrieve experimental request from Aquarium-opil.
    Refer to link for getting aquarium-opil file:
    https://github.com/aquariumbio/aquarium-opil
    """

    logger = logging.getLogger('aqurium_opil_accessor')
    _SUPPORTED_PROTOCOLS = {'jellyfish': 'jellyfish_htc.xml'}

    def __init__(self):
       self.cached_protocols = {}

    def get_experimental_protocol(self, experimental_request_name):
        if experimental_request_name in self._SUPPORTED_PROTOCOLS:
            if experimental_request_name not in self.cached_protocols:
                file_name = self._SUPPORTED_PROTOCOLS[experimental_request_name]
                curr_path = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(curr_path, file_name)
                opil_doc = ip_utils.load_opil_xml_file(file_path)
                template = OpilDocumentTemplate()
                template.load_from_template(opil_doc)
                self.cached_protocols[experimental_request_name] = template
            return self.cached_protocols[experimental_request_name]

        raise IntentParserException('Aquarium does not support %s as an experimental request' % experimental_request_name)

    def get_protocol_interface(self, protocol_name):
        opil_doc = self.get_experimental_protocol(protocol_name)
        protocol_interfaces = opil_utils.get_protocol_interfaces_from_sbol_doc(opil_doc)
        if len(protocol_interfaces) == 0:
            raise IntentParserException('No opil protocol interface found from aquarium')

        if len(protocol_interfaces) > 1:
            raise IntentParserException('Expected to find one opil protocol interface for %s but more than one was found' % protocol_name)

        return protocol_interfaces[0]