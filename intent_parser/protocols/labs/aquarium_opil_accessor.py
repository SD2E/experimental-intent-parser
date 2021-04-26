from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.protocols.labs.opil_lab_accessor import OpilLabAccessors
from intent_parser.protocols.templates.experimental_request_template import OpilDocumentTemplate
import intent_parser.utils.intent_parser_utils as ip_utils
import intent_parser.utils.opil_utils as opil_utils
import logging
import os


class AquariumOpilAccessor(OpilLabAccessors):
    """
    Retrieve experimental request from Aquarium-opil.
    Refer to link for getting aquarium-opil file:
    https://github.com/aquariumbio/aquarium-opil
    """

    logger = logging.getLogger('aquarium_opil_accessor')
    _SUPPORTED_PROTOCOLS = {'High-Throughput Culturing': 'jellyfish_htc.xml'}

    def __init__(self):
       super().__init__()
       self.cached_protocols = {}

    def get_experiment_id_from_protocol(self, protocol_name):
        if protocol_name not in self._SUPPORTED_PROTOCOLS:
            raise IntentParserException('Protocol not supported by Aquarium: %s' % protocol_name)
        return 'TBA'

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

    def get_experimental_protocol_names(self):
        return list(self._SUPPORTED_PROTOCOLS.keys())
