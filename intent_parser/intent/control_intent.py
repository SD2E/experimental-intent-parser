from intent_parser.intent_parser_exceptions import IntentParserException
import intent_parser.constants.sd2_datacatalog_constants as dc_constants

class Control(object):

    def __init__(self):
        self.intent = {}
        self._channel = None
        self._control_type = None
        self._contents = []
        self._strains = []
        self._timepoints = []

    def add_field(self, field, value):
        self.intent[field] = value

    def add_content(self, value: dict):
        self._contents.append(value)

    def add_strain(self, value: dict):
        self._strains.append(value)

    def add_timepoint(self, value: dict):
        self._timepoints.append(value)

    def set_channel(self, value: str):
        self._channel = value

    def set_control_type(self, value: str):
        if self._control_type:
            raise IntentParserException('Conflict setting control type %s. Current set value %s' % (value, self._control_type))
        self._control_type = value

    def to_structured_request(self):
        sr = {dc_constants.TYPE, self._control_type}
        return self.intent
