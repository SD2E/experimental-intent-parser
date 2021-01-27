from intent_parser.intent_parser_exceptions import IntentParserException
from typing import List
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.constants.intent_parser_constants as ip_constants

class ProtocolFactory(object):

    def __init__(self, transcriptic_accessor):
        self._selected_lab_name = None
        self._lab_accessors = {ip_constants.LAB_TRANSCRIPTIC: transcriptic_accessor}

    def set_selected_lab(self, lab_name: str):
        self._selected_lab_name = lab_name

    def support_lab(self, lab_name):
        return lab_name in self._lab_accessors

    def load_protocols_from_lab(self) -> List:
        if self._selected_lab_name is not None and self._selected_lab_name in self._lab_accessors:
            lab_accessor = self._lab_accessors[self._selected_lab_name]
            return lab_accessor.get_list_of_protocol_interface()
        else:
            raise IntentParserException('%s is not a supported lab for fetching protocols.' % self._selected_lab_name)

    def get_protocol_id(self, protocol_name):
        if self._selected_lab_name is not None and self._selected_lab_name in self._lab_accessors:
            lab_accessor = self._lab_accessors[self._selected_lab_name]
            return lab_accessor.get_protocol_id(protocol_name)
        else:
            raise IntentParserException('%s is not a supported lab for fetching protocol ids.' % self._selected_lab_name)

    def get_protocol_fields(self, protocol_name):
        if self._selected_lab_name is not None and self._selected_lab_name in self._lab_accessors:
            lab_accessor = self._lab_accessors[self._selected_lab_name]
            return lab_accessor.get_protocol_parameter_fields(protocol_name)
        else:
            raise IntentParserException('%s is not a supported lab for fetching parameters for protocol %s.' % (self._selected_lab_name, protocol_name))

    def get_protocol_interface(self, protocol_name):
        if self._selected_lab_name is not None and self._selected_lab_name in self._lab_accessors:
            lab_accessor = self._lab_accessors[self._selected_lab_name]
            protocol = lab_accessor.get_protocol_interface(protocol_name)
            return protocol
        else:
            raise IntentParserException('%s is not a supported lab for fetching protocol %s' % (self._selected_lab_name, protocol_name))

    def load_parameter_values_from_protocol(self, protocol_name):
        if self._selected_lab_name is not None and self._selected_lab_name in self._lab_accessors:
            lab_accessor = self._lab_accessors[self._selected_lab_name]
            return lab_accessor.get_protocol_parameter_values(protocol_name)
        else:
            raise IntentParserException('%s is not a supported lab for fetching protocol values for %s' % (self._selected_lab_name, protocol_name))

