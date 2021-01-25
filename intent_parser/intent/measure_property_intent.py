from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.utils.id_provider import IdProvider
from sbol3 import Component, Measure, SubComponent
from typing import Union
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.constants.intent_parser_constants as ip_constants
import opil
import sbol3.constants as sbol_constants

class MeasuredUnit(object):

    def __init__(self, value: Union[float, int], unit: str, unit_type=None):
        self._value = value
        self._unit = unit
        self._unit_type = unit_type

    def get_unit(self):
        return self._unit

    def get_value(self):
        return self._value

    def to_sbol(self):
        if self._unit_type == ip_constants.UNIT_TYPE_FLUID:
            return self._encode_fluid_using_sbol()
        elif self._unit_type == ip_constants.UNIT_TYPE_TIMEPOINT:
            return self._encode_timepoint_using_sbol()
        elif self._unit_type == ip_constants.UNIT_TYPE_TEMPERATURE:
            return self._encode_temperature_using_sbol()
        else:
            raise IntentParserException('%s measurement type not supported' % self._unit_type)

    def to_structure_request(self):
        return {dc_constants.VALUE: float(self._value),
                dc_constants.UNIT: self._unit}

    def _encode_fluid_using_sbol(self):
        if self._unit == '%':
            measure = Measure(self._value, ip_constants.NCIT_CONCENTRATION)
            measure.name = 'concentration'
            return measure
        elif self._unit == 'M':
            return Measure(self._value, ip_constants.UO_MOLAR)
        elif self._unit == 'mM':
            return Measure(self._value, ip_constants.UO_MILLI_MOLAR)
        elif self._unit == 'X':
            return Measure(self._value, ip_constants.NCIT_FOLD_CHANGE)
        elif self._unit == 'g/L':
            return Measure(self._value, ip_constants.UO_GRAM_PER_LITER)
        elif self._unit == 'ug/ml':
            return Measure(self._value, ip_constants.NCIT_MICROGRAM_PER_MILLILITER)
        elif self._unit == 'micromole':
            return Measure(self._value, ip_constants.NCIT_MICROMOLE)
        elif self._unit == 'nM':
            return Measure(self._value, ip_constants.NCIT_NANOMOLE)
        elif self._unit == 'uM':
            return Measure(self._value, ip_constants.NCIT_MICROMOLE)
        elif self._unit == 'mg/ml':
            return Measure(self._value, ip_constants.UO_MILLIGRAM_PER_MILLILITER)
        elif self._unit == 'ng/ul':
            return Measure(self._value, ip_constants.UO_NANO_GRAM_PER_LITER)
        else:
            raise IntentParserException('unit %s not supported.' % self._unit)

    def _encode_temperature_using_sbol(self):
        if self._unit == 'celsius':
            return Measure(self._value, ip_constants.NCIT_CELSIUS)
        elif self._unit == 'fahrenheit':
            return Measure(self._value, ip_constants.NCIT_FAHRENHEIT)
        else:
            raise IntentParserException('unit %s not supported.' % self._unit)

    def _encode_timepoint_using_sbol(self):
        if self._unit == 'day':
            return Measure(self._value, ip_constants.NCIT_MONTH)
        elif self._unit == 'hour':
            return Measure(self._value, ip_constants.NCIT_HOUR)
        elif self._unit == 'femtosecond':
            return Measure(self._value, 'http://www.ontology-of-units-of-measure.org/resource/om-2/femtosecond-Time')
        elif self._unit == 'microsecond':
            return Measure(self._value, ip_constants.NCIT_MICROSECOND)
        elif self._unit == 'millisecond':
            return Measure(self._value, ip_constants.NCIT_MILLISECOND)
        elif self._unit == 'minute':
            return Measure(self._value, ip_constants.NCIT_MINUTE)
        elif self._unit == 'month':
            return Measure(self._value, ip_constants.NCIT_MONTH)
        elif self._unit == 'nanosecond':
            return Measure(self._value, ip_constants.NCIT_NANOSECOND)
        elif self._unit == 'picosecond':
            return Measure(self._value, ip_constants.NCIT_PICOSECOND)
        elif self._unit == 'second':
            return Measure(self._value, ip_constants.NCIT_SECOND)
        elif self._unit == 'week':
            return Measure(self._value, ip_constants.NCIT_WEEK)
        elif self._unit == 'year':
            return Measure(self._value, ip_constants.NCIT_YEAR)
        else:
            raise IntentParserException('unit %s not supported.' % self._unit)

class TemperatureIntent(MeasuredUnit):

    def __init__(self, value: float, unit: str):
        super().__init__(value, unit, ip_constants.UNIT_TYPE_TEMPERATURE)

class TimepointIntent(MeasuredUnit):

    def __init__(self, value: Union[float, int], unit: str):
        super().__init__(value, unit, ip_constants.UNIT_TYPE_TIMEPOINT)

class NamedLink(object):

    def __init__(self, name, link=None):
        self._name = name
        self._link = link

    def get_name(self):
        return self._name

    def get_link(self):
        return self._link

    def to_structure_request(self):
        return {dc_constants.LABEL: self._name,
                dc_constants.SBH_URI: self._link if self._link else dc_constants.NO_PROGRAM_DICTIONARY}


class NamedBooleanValue(object):

    def __init__(self, named_link: NamedLink, value: bool):
        self._named_link = named_link
        self._value = value

    def get_value(self):
        return self._value

    def to_structure_request(self):
        return {dc_constants.NAME: self._named_link.to_structure_request(),
                dc_constants.VALUE: str(self._value)}

class NamedIntegerValue(object):

    def __init__(self, named_link: NamedLink, value: int):
        self._named_link = named_link
        self._value = value

    def get_value(self):
        return self._value

    def to_structure_request(self):
        return {dc_constants.NAME: self._named_link.to_structure_request(),
                dc_constants.VALUE: self._value}

class NamedStringValue(object):

    def __init__(self, named_link: NamedLink, value=''):
        self._named_link = named_link
        self._value = value

    def get_named_link(self):
        return self._named_link

    def get_value(self):
        return self._value

    def to_structure_request(self):
        result = {dc_constants.NAME: self._named_link.to_structure_request()}
        if self._value:
            result[dc_constants.VALUE] = self._value
        return result

class MediaIntent(object):

    def __init__(self, media_name: NamedLink, media_value: NamedLink):
        self._media_name = media_name
        self._media_value = media_value
        self._timepoint = None
        self._id_provider = IdProvider()

    def get_media_name(self) -> NamedLink:
        return self._media_name

    def get_timepoint(self) -> NamedLink:
        return self._timepoint

    def set_timepoint(self, timepoint: TimepointIntent):
        self._timepoint = timepoint

    def to_sbol(self):
        media_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                    component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        media_component.name = self._media_value.get_name()
        if self._media_value.get_link() is None:
            raise IntentParserException('media %s has invalid media value: no sbh link provided' % self._media_value.get_name())
        media_sub_component = SubComponent(self._media_value.get_link())
        media_component.features = [media_sub_component]

        return media_component

    def to_structure_request(self):
        media = {dc_constants.NAME: self._media_name.to_structure_request(),
                 dc_constants.VALUE: self._media_value.get_name()}

        if self._timepoint:
            media[dc_constants.TIMEPOINT] = self._timepoint.to_structure_request()

        return media



class ReagentIntent(MeasuredUnit):

    def __init__(self, reagent_name: NamedLink, value: float, unit: str):
        super().__init__(value, unit, 'fluid')
        self._reagent_name = reagent_name
        self._timepoint = None
        self._id_provider = IdProvider()

    def get_reagent_name(self):
        return self._reagent_name

    def get_timepoint(self):
        return self._timepoint

    def set_timepoint(self, timepoint: TimepointIntent):
        self._timepoint = timepoint

    def to_sbol(self):
        content_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                      component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        content_component.name = self._reagent_name.get_name()
        content_sub_component = SubComponent(self._reagent_name.get_link())
        content_component.features = [content_sub_component]

        return content_component

    def to_structure_request(self):
        reagent = {dc_constants.NAME: self._reagent_name.to_structure_request(),
                   dc_constants.VALUE: str(self._value),
                   dc_constants.UNIT: self._unit}
        if self._timepoint:
            reagent[dc_constants.TIMEPOINT] = self._timepoint.to_structure_request()

        return reagent
