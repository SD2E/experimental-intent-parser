from intent_parser.intent_parser_exceptions import IntentParserException
import intent_parser.constants.sd2_datacatalog_constants as dc_constants

class ControlIntent(object):

    def __init__(self):
        self.intent = {}
        self._channel = None
        self._control_type = None
        self._contents = []
        self._strains = []
        self._timepoints = []

    def add_content(self, value):
        self._contents.append(value)

    def add_strain(self, strain):
        self._strains.append(strain)

    def add_timepoint(self, timepoint):
        self._timepoints.append(timepoint)

    def is_empty(self):
        return (self._channel is None and
                self._control_type is None and
                len(self._contents) == 0 and
                len(self._strains) == 0 and
                len(self._timepoints) == 0)

    def set_channel(self, value: str):
        self._channel = value

    def set_control_type(self, value: str):
        if self._control_type:
            raise IntentParserException('Conflict setting control type %s. Current set value %s' % (value, self._control_type))
        self._control_type = value

    def to_sbol_for_measurement(self):
        pass


    def to_structure_request(self):
        if self._control_type is None:
            raise IntentParserException('control-type is not set.')

        structure_request = {dc_constants.TYPE: self._control_type}
        if len(self._strains) > 0:
            structure_request[dc_constants.STRAINS] = [strain.to_structure_request() for strain in self._strains]
        if self._channel:
            structure_request[dc_constants.CHANNEL] = self._channel
        if len(self._contents) > 0:
            structure_request[dc_constants.CONTENTS] = [content.to_structure_request() for content in self._contents]
        if len(self._timepoints) > 0:
            structure_request[dc_constants.TIMEPOINTS] = [timepoint.to_structure_request() for timepoint in self._timepoints]
        return structure_request
