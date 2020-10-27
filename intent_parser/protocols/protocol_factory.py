from intent_parser.intent_parser_exceptions import IntentParserException
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
from typing import List

class ProtocolFactory(object):

    def __init__(self, lab_name, transcriptic_accessor):
        self.lab_name = lab_name
        self.transcriptic_accessor = transcriptic_accessor

    def load_protocols_from_lab(self) -> List:
        if self.lab_name == dc_constants.LAB_TRANSCRIPTIC:
            return self.transcriptic_accessor.get_list_of_protocol_interface()
        else:
            raise IntentParserException('Intent Parser does not support fetching protocols from lab: %s.' % self.lab_name)

    def get_protocol_id(self, protocol_name):
        if self.lab_name == dc_constants.LAB_TRANSCRIPTIC:
            return self.transcriptic_accessor.get_protocol_id(protocol_name)
        else:
            raise IntentParserException('Intent Parser unable to get protocol id for %s.' % self.lab_name)

    def get_protocol_interface(self, selected_protocol):
        if self.lab_name == dc_constants.LAB_TRANSCRIPTIC:
            protocol = self.transcriptic_accessor.get_protocol_interface(selected_protocol)
            return protocol
        else:
            raise IntentParserException('Unable to get protocol interface from %s: %s is not a supported protocol' % (self.lab_name, selected_protocol))

    def load_parameter_values_from_protocol(self, protocol_name):
        if self.lab_name == dc_constants.LAB_TRANSCRIPTIC:
            return self.transcriptic_accessor.get_protocol_parameter_values(protocol_name)
        else:
            raise IntentParserException('Unable to get protocol values from %s: %s is not a supported protocol' % (self.lab_name, protocol_name))

    def get_optional_parameter_fields(self, protocol):
        parameters = []
        for parameter in protocol.has_parameter:
            if not parameter.required:
                parameters.append(parameter)

        return parameters