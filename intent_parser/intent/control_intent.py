from intent_parser.intent.strain_intent import StrainIntent
from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.utils.id_provider import IdProvider
from sbol3 import TextProperty
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.constants.intent_parser_constants as ip_constants

"""
Intent Parser's representation for a control.
"""
class ControlIntent(object):

    def __init__(self):
        self.intent = {}
        self._channel = None
        self._control_type = None
        self._contents = []
        self._strains = []
        self._timepoints = []
        self._id_provider = IdProvider()
        self._table_caption = ''

    def add_content(self, value):
        self._contents.append(value)

    def add_strain(self, strain: StrainIntent):
        self._strains.append(strain)

    def add_timepoint(self, timepoint):
        self._timepoints.append(timepoint)

    def get_contents(self):
        return self._contents

    def get_table_caption(self):
        return self._table_caption

    def is_empty(self):
        return (self._channel is None and
                self._control_type is None and
                len(self._contents) == 0 and
                len(self._strains) == 0 and
                len(self._timepoints) == 0)

    def size_of_strains(self):
        return len(self._strains)

    def size_of_contents(self):
        return len(self._contents)

    def set_channel(self, value: str):
        self._channel = value

    def set_control_type(self, value: str):
        if self._control_type:
            raise IntentParserException('Conflict setting control type %s. '
                                        'Current set value %s' % (value, self._control_type))
        self._control_type = value

    def set_table_caption(self, table_caption):
        self._table_caption = table_caption

    def to_opil(self, opil_measurement):
        if self._channel is not None:
            self._encode_channel_using_opil(opil_measurement)
        if self._control_type is not None:
            self._encode_control_type_using_opil(opil_measurement)
        if len(self._timepoints) > 0:
            self._encode_timepoints_using_opil(opil_measurement)

    def to_structured_request(self):
        if self._control_type is None:
            raise IntentParserException('control-type is not set.')

        structure_request = {dc_constants.TYPE: self._control_type}
        if len(self._strains) > 0:
            structure_request[dc_constants.STRAINS] = [strain.to_structured_request() for strain in self._strains]
        if self._channel:
            structure_request[dc_constants.CHANNEL] = self._channel
        if len(self._contents) > 0:
            structure_request[dc_constants.CONTENTS] = [content.to_structured_request() for content in self._contents]
        if len(self._timepoints) > 0:
            structure_request[dc_constants.TIMEPOINTS] = [timepoint.to_structured_request() for timepoint in self._timepoints]
        return structure_request

    def _encode_channel_using_opil(self, opil_measurement):
        opil_measurement.channel = TextProperty(opil_measurement,
                                                ip_constants.SD2E_NAMESPACE + 'channel',
                                                0,
                                                1)
        opil_measurement.channel = self._channel

    def _encode_control_type_using_opil(self, opil_measurement):
        opil_measurement.control_type = TextProperty(opil_measurement,
                                             self._id_provider.get_unique_sd2_id(),
                                             0,
                                             1)
        opil_measurement.control_type = self._control_type

    def _encode_timepoints_using_opil(self, opil_measurement):
        encoded_timepoints = []
        for timepoint in self._timepoints:
            encoded_timepoints.append(timepoint.to_opil_measure())
        opil_measurement.time = encoded_timepoints

    def strain_values_to_opil_components(self):
        return [strain.to_opil_component() for strain in self._strains]