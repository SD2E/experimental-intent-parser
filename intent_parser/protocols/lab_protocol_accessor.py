from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.protocols.parameter_field import ParameterField
import intent_parser.constants.intent_parser_constants as ip_constants
import opil


class LabProtocolAccessor(object):
    def __init__(self, transcriptic_accessor, aquarium_accessor):
        self._lab_accessors = {ip_constants.LAB_TRANSCRIPTIC: transcriptic_accessor,
                               ip_constants.LAB_DUKE_HASE: aquarium_accessor}

    def map_name_to_experimental_protocols(self):
        """
        Get name of lab and their supporting protocol interface.
        """
        experimental_protocols = {}
        for lab_name, lab_accessor in self._lab_accessors.items():
            experimental_protocols[lab_name] = self.get_protocol_names_from_lab(lab_name)
        return experimental_protocols

    def get_experiment_from_lab_protocol(self, lab_name, protocol_name):
        lab_accessor = self._get_lab_accessor(lab_name)
        return lab_accessor.get_experiment_id_from_protocol(protocol_name)

    def get_protocol_names_from_lab(self, lab_name):
        """
        Retrieve protocol names supported in a lab.
        Args:
            lab_name: name of lab
        Returns:
            list of protocol names
        """
        lab_accessor = self._get_lab_accessor(lab_name)
        return lab_accessor.get_experimental_protocol_names()

    def load_protocol_interface_from_lab(self, protocol_interface_name, lab_name):
        """
        Retrieve protocol interface.
        Args:
            protocol_interface_name: name of protocol interface
            lab_name: name of lab that supports the protocol interface
        Returns:
            an Intent Parser OpilDocumentTemplate
        """
        lab_accessor = self._get_lab_accessor(lab_name)
        return lab_accessor.get_experimental_protocol(protocol_interface_name)

    def get_protocol_id(self, protocol_name, lab_name):
        """
        Get id for a lab protocol.
        Args:
             protocol_name: name of protocol
             lab_name: name of lab
        Returns:
            A string representing a protocol ID. An empty string is returned if no protocol ID is assigned.
        """
        lab_accessor = self._get_lab_accessor(lab_name)
        opil_document_template = lab_accessor.get_experimental_protocol(protocol_name)
        protocol_interfaces = opil_document_template.get_protocol_interfaces()
        if not protocol_interfaces:
            raise IntentParserException('No lab ProtocolInterface found with protocol name: %s' % protocol_name)
        if len(protocol_interfaces) > 1:
            raise IntentParserException('Expecting 1 ProtocolInterface but %d were found' % len(protocol_interfaces))

        protocol_interface = protocol_interfaces[0]
        if lab_name == ip_constants.LAB_TRANSCRIPTIC:
            return protocol_interface.strateos_id
        return ''

    def map_name_to_parameters(self, protocol_name, lab_name):
        """
        Get parameters from a lab protocol.
        Args:
            protocol_name: name of protocol
            lab_name: name of lab
        Returns:
            a dictionary mapping name to its parameter
        """
        lab_accessor = self._get_lab_accessor(lab_name)
        opil_document_template = lab_accessor.get_experimental_protocol(protocol_name)
        protocol_interfaces = opil_document_template.get_protocol_interfaces()
        if not protocol_interfaces:
            raise IntentParserException('No lab ProtocolInterface found with protocol name: %s' % protocol_name)
        if len(protocol_interfaces) > 1:
            raise IntentParserException('Expecting 1 ProtocolInterface but %d were found' % len(protocol_interfaces))

        parameters = {}
        protocol_interface = protocol_interfaces[0]
        for opil_parameter in protocol_interface.has_parameter:
            parameter_name = opil_parameter.name
            possible_values = []
            if opil_parameter.default_value:
                possible_values.append(opil_parameter.default_value)

            if type(opil_parameter) is opil.EnumeratedParameter and opil_parameter.allowed_value:
                possible_values.extend(opil_parameter.allowed_value)

            if not opil_parameter.required:
                ip_parameter_field = ParameterField(parameter_name,
                                                    opil_parameter,
                                                    valid_values=possible_values)
                parameters[parameter_name] = ip_parameter_field
                if opil_parameter.description:
                    ip_parameter_field.set_description(opil_parameter.description)
            else:
                ip_parameter_field = ParameterField(parameter_name,
                                                    opil_parameter,
                                                    required=True,
                                                    valid_values=possible_values)
                parameters[parameter_name] = ip_parameter_field
                if opil_parameter.description:
                    ip_parameter_field.set_description(opil_parameter.description)
        return parameters

    def _get_lab_accessor(self, lab_name):
        if lab_name not in self._lab_accessors:
            raise IntentParserException(
                'Lab not supported: %s' % lab_name)
        lab_accessor = self._lab_accessors[lab_name]
        return lab_accessor
