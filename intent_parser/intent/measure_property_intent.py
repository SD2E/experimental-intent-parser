from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.utils.id_provider import IdProvider
from sbol3 import Component, Measure, SubComponent
from typing import Union
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.constants.intent_parser_constants as ip_constants
import sbol3.constants as sbol_constants

class MeasuredUnit(object):
    _FLUID_UNIT_MAP = {'%': ip_constants.NCIT_CONCENTRATION,
                       'M': ip_constants.UO_MOLAR,
                       'mM': ip_constants.UO_MILLI_MOLAR,
                       'X': ip_constants.NCIT_FOLD_CHANGE,
                       'g/L': ip_constants.UO_GRAM_PER_LITER,
                       'ug/ml': ip_constants.NCIT_MICROGRAM_PER_MILLILITER,
                       'micromole': ip_constants.NCIT_MICROMOLE,
                       'nM': ip_constants.NCIT_NANOMOLE,
                       'uM': ip_constants.NCIT_MICROMOLE,
                       'mg/ml': ip_constants.UO_MILLIGRAM_PER_MILLILITER,
                       'ng/ul': ip_constants.UO_NANO_GRAM_PER_LITER,
                       'microlitre': ip_constants.OTU_MICROLITRE}

    _TEMPERATURE_UNIT_MAP = {'celsius': ip_constants.NCIT_CELSIUS,
                             'fahrenheit': ip_constants.NCIT_FAHRENHEIT}

    _TIME_UNIT_MAP = {'day': ip_constants.NCIT_MONTH,
                      'hour': ip_constants.NCIT_HOUR,
                      'femtosecond': ip_constants.OTU_FEMTOSECOND,
                      'microsecond': ip_constants.NCIT_MICROSECOND,
                      'millisecond': ip_constants.NCIT_MILLISECOND,
                      'minute': ip_constants.NCIT_MINUTE,
                      'month': ip_constants.NCIT_MONTH,
                      'nanosecond': ip_constants.NCIT_NANOSECOND,
                      'picosecond': ip_constants.NCIT_PICOSECOND,
                      'second': ip_constants.NCIT_SECOND,
                      'week': ip_constants.NCIT_WEEK,
                      'year': ip_constants.NCIT_YEAR}

    def __init__(self, value: Union[float, int], unit: str, unit_type=None):
        self._value = value
        self._unit = unit
        self._unit_type = unit_type

    def get_unit(self):
        return self._unit

    def get_unit_name_from_uri(self, unit_uri: str):
        """
        Get unit name from an measurement unit uri.
        Args:
            unit_uri: unit uri
        Returns:
            a string representing the unit name of the given unit uri.
            An empty string is returned if no unit name is found for the given uri.
        """
        for key, value in self._FLUID_UNIT_MAP.items():
            if value == unit_uri:
                return key

        for key, value in self._TEMPERATURE_UNIT_MAP.items():
            if value == unit_uri:
                return key

        for key, value in self._TIME_UNIT_MAP.items():
            if value == unit_uri:
                return key

        if unit_uri == ip_constants.OTU_NANOMETER:
            return 'nanometer'

        if unit_uri == ip_constants.OTU_HOUR:
            return 'hour'

        return ''

    def get_value(self):
        return self._value

    def to_sbol(self):
        if self._unit_type is not None:
            return self._get_sbol_measure_by_unit_type()
        else:
            if self._unit in self._FLUID_UNIT_MAP:
                return self._encode_fluid_using_sbol()
            elif self._unit in self._TEMPERATURE_UNIT_MAP:
                return self._encode_temperature_using_sbol()
            elif self._unit in self._TIME_UNIT_MAP:
                return self._encode_timepoint_using_sbol()
            else:
                return Measure(self._value, ip_constants.NCIT_NOT_APPLICABLE)

    def to_structure_request(self):
        return {dc_constants.VALUE: float(self._value),
                dc_constants.UNIT: self._unit}

    def _get_sbol_measure_by_unit_type(self):
        if self._unit_type == ip_constants.UNIT_TYPE_FLUID:
            return self._encode_fluid_using_sbol()
        elif self._unit_type == ip_constants.UNIT_TYPE_TIMEPOINT:
            return self._encode_timepoint_using_sbol()
        elif self._unit_type == ip_constants.UNIT_TYPE_TEMPERATURE:
            return self._encode_temperature_using_sbol()
        else:
            raise IntentParserException('%s measurement type not supported' % self._unit_type)

    def _encode_fluid_using_sbol(self):
        if self._unit == '%':
            measure = Measure(self._value, ip_constants.NCIT_CONCENTRATION)
            return measure
        elif self._unit == 'M':
            measure = Measure(self._value, ip_constants.UO_MOLAR)
            return measure
        elif self._unit == 'mM':
            measure = Measure(self._value, ip_constants.UO_MILLI_MOLAR)
            return measure
        elif self._unit == 'X':
            measure = Measure(self._value, ip_constants.NCIT_FOLD_CHANGE)
            return measure
        elif self._unit == 'g/L':
            measure = Measure(self._value, ip_constants.UO_GRAM_PER_LITER)
            return measure
        elif self._unit == 'ug/ml':
            measure = Measure(self._value, ip_constants.NCIT_MICROGRAM_PER_MILLILITER)
            return measure
        elif self._unit == 'micromole':
            measure = Measure(self._value, ip_constants.NCIT_MICROMOLE)
            return measure
        elif self._unit == 'nM':
            measure = Measure(self._value, ip_constants.NCIT_NANOMOLE)
            return measure
        elif self._unit == 'uM':
            measure = Measure(self._value, ip_constants.NCIT_MICROMOLE)
            return measure
        elif self._unit == 'mg/ml':
            measure = Measure(self._value, ip_constants.UO_MILLIGRAM_PER_MILLILITER)
            return measure
        elif self._unit == 'ng/ul':
            measure = Measure(self._value, ip_constants.UO_NANO_GRAM_PER_LITER)
            return measure
        else:
            raise IntentParserException('%s is not a supported unit.' % self._unit)

    def _encode_temperature_using_sbol(self):
        if self._unit == 'celsius':
            measure = Measure(self._value, ip_constants.NCIT_CELSIUS)
            measure.name = 'celsius'
            return measure
        elif self._unit == 'fahrenheit':
            measure = Measure(self._value, ip_constants.NCIT_FAHRENHEIT)
            measure.name = 'fahrenheit'
            return measure
        else:
            raise IntentParserException('%s is not a supported unit.' % self._unit)

    def _encode_timepoint_using_sbol(self):
        if self._unit == 'day':
            measure = Measure(self._value, ip_constants.NCIT_DAY)
            measure.name = 'day'
            return measure
        elif self._unit == 'hour':
            measure = Measure(self._value, ip_constants.NCIT_HOUR)
            measure.name = 'hour'
            return measure
        elif self._unit == 'femtosecond':
            measure = Measure(self._value, ip_constants.OTU_FEMTOSECOND)
            measure.name = 'femtosecond'
            return measure
        elif self._unit == 'microsecond':
            measure = Measure(self._value, ip_constants.NCIT_MICROSECOND)
            measure.name = 'microsecond'
            return measure
        elif self._unit == 'millisecond':
            measure = Measure(self._value, ip_constants.NCIT_MILLISECOND)
            measure.name = 'millisecond'
            return measure
        elif self._unit == 'minute':
            measure = Measure(self._value, ip_constants.NCIT_MINUTE)
            measure.name = 'minute'
            return measure
        elif self._unit == 'month':
            measure = Measure(self._value, ip_constants.NCIT_MONTH)
            measure.name = 'month'
            return measure
        elif self._unit == 'nanosecond':
            measure = Measure(self._value, ip_constants.NCIT_NANOSECOND)
            measure.name = 'nanosecond'
            return measure
        elif self._unit == 'picosecond':
            measure = Measure(self._value, ip_constants.NCIT_PICOSECOND)
            measure.name = 'picosecond'
            return measure
        elif self._unit == 'second':
            measure = Measure(self._value, ip_constants.NCIT_SECOND)
            measure.name = 'second'
            return measure
        elif self._unit == 'week':
            measure = Measure(self._value, ip_constants.NCIT_WEEK)
            measure.name = 'week'
            return measure
        elif self._unit == 'year':
            measure = Measure(self._value, ip_constants.NCIT_YEAR)
            measure.name = 'year'
            return measure
        else:
            raise IntentParserException('%s is not a supported unit.' % self._unit)

class TemperatureIntent(MeasuredUnit):

    def __init__(self, value: float, unit: str):
        super().__init__(value, unit, unit_type=ip_constants.UNIT_TYPE_TEMPERATURE)

class TimepointIntent(MeasuredUnit):

    def __init__(self, value: Union[float, int], unit: str):
        super().__init__(value, unit, unit_type=ip_constants.UNIT_TYPE_TIMEPOINT)

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

    def to_sbol(self, sbol_document):
        media_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                    component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        media_component.name = self._media_value.get_name()

        if self._media_value.get_link() is None:
            raise IntentParserException('media %s has invalid media value: no sbh link provided' % self._media_value.get_name())

        media_sub_component = SubComponent(self._media_value.get_link())
        media_component.features = [media_sub_component]
        sbol_document.add(media_component)
        return media_component

    def to_structure_request(self):
        media = {dc_constants.NAME: self._media_name.to_structure_request(),
                 dc_constants.VALUE: self._media_value.get_name()}

        if self._timepoint:
            media[dc_constants.TIMEPOINT] = self._timepoint.to_structure_request()

        return media



class ReagentIntent(MeasuredUnit):

    def __init__(self, reagent_name: NamedLink, value: float, unit: str):
        super().__init__(value, unit, unit_type='fluid')
        self._reagent_name = reagent_name
        self._timepoint = None
        self._id_provider = IdProvider()

    def get_reagent_name(self):
        return self._reagent_name

    def get_timepoint(self):
        return self._timepoint

    def set_timepoint(self, timepoint: TimepointIntent):
        self._timepoint = timepoint

    def to_sbol(self, sbol_document):
        content_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                      component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        content_component.name = self._reagent_name.get_name()
        content_sub_component = SubComponent(self._reagent_name.get_link())
        content_component.features = [content_sub_component]
        sbol_document.add(content_component)
        return content_component

    def to_structure_request(self):
        reagent = {dc_constants.NAME: self._reagent_name.to_structure_request(),
                   dc_constants.VALUE: str(self._value),
                   dc_constants.UNIT: self._unit}
        if self._timepoint:
            reagent[dc_constants.TIMEPOINT] = self._timepoint.to_structure_request()

        return reagent
