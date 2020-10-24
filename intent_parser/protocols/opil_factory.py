from intent_parser.intent_parser_exceptions import IntentParserException
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import opil

class OpilFactory(object):

    def __init__(self, transcriptic_accessor):
        self.transcriptic_accessor = transcriptic_accessor

    def load_protocol_interface_from_lab(self, lab_name: str, protocol_name: str) -> list:
        if lab_name == dc_constants.LAB_TRANSCRIPTIC:
            return self._get_opil_from_transcriptic(protocol_name)
        else:
            raise IntentParserException('Intent Parser does not support fetching protocols from lab: %s.' % lab_name)

    def _get_opil_from_transcriptic(self, protocol_name):
        selected_protocol = self.transcriptic_accessor.get_protocol_as_schema(protocol_name)
        strateos_namespace = 'http://strateos.com/'
        sg = opil.StrateosOpilGenerator()
        sbol_doc = sg.parse_strateos_json(strateos_namespace, protocol_name, selected_protocol)
        targeted_interface = None
        for obj in sbol_doc.objects:
            if type(obj) is opil.opil_factory.ProtocolInterface:
                targeted_interface = obj

        if not targeted_interface:
            raise IntentParserException('Unable to locate OPIL protocol interface when converting transcriptic protocols to OPIL')

        return targeted_interface

