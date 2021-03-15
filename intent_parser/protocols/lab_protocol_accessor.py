from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.protocols.parameter_field import ParameterField
from typing import List
import intent_parser.constants.intent_parser_constants as ip_constants
import opil

class LabProtocolAccessor(object):

    def __init__(self, transcriptic_accessor, aquarium_accessor):
        self._selected_lab_name = None
        self._lab_accessors = {ip_constants.LAB_TRANSCRIPTIC: transcriptic_accessor,
                               ip_constants.LAB_DUKE_HASE: aquarium_accessor}

    def set_selected_lab(self, lab_name: str):
        self._selected_lab_name = lab_name

    def support_lab(self, lab_name):
        return lab_name in self._lab_accessors

    def load_experimental_protocol_from_lab(self, experiment_name):
        if self._selected_lab_name is not None and self._selected_lab_name in self._lab_accessors:
            lab_accessor = self._lab_accessors[self._selected_lab_name]
            return lab_accessor.get_experimental_protocol(experiment_name)
        else:
            raise IntentParserException('%s not supported in Intent Parser for getting experimental protocol' % experiment_name)

    def load_protocol_interfaces_from_lab(self) -> List:
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

    def map_parameter_values(self, protocol_name):
        protocol_field_mapping = self.get_protocol_fields(protocol_name)
        parameters = {}
        for parameter_name, parameter in protocol_field_mapping.items():
            possible_values = []
            if parameter.default_value:
                possible_values.append(parameter.default_value)

            if type(parameter) is opil.EnumeratedParameter and parameter.allowed_value:
                possible_values.extend(parameter.allowed_value)

            if not parameter.required:
                ip_parameter_field = ParameterField(parameter_name, parameter, valid_values=possible_values)
                parameters[parameter_name] = ip_parameter_field
                if parameter.description:
                    ip_parameter_field.set_description(parameter.description)
            else:
                ip_parameter_field = ParameterField(parameter_name, parameter, required=True, valid_values=possible_values)
                parameters[parameter_name] = ip_parameter_field
                if parameter.description:
                    ip_parameter_field.set_description(parameter.description)

        return parameters

    def load_parameter_values_from_protocol(self, protocol_name):
        if self._selected_lab_name is not None and self._selected_lab_name in self._lab_accessors:
            lab_accessor = self._lab_accessors[self._selected_lab_name]
            return lab_accessor.get_protocol_parameter_values(protocol_name)
        else:
            raise IntentParserException('%s is not a supported lab for fetching protocol values for %s' % (self._selected_lab_name, protocol_name))

