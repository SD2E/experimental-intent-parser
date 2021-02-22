from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.utils.id_provider import IdProvider
from sbol3 import Component, SubComponent, VariableFeature
from typing import Union
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.constants.intent_parser_constants as ip_constants
import opil
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

    def to_opil(self):
        if self._unit_type is not None:
            return self._get_sbol_measure_by_unit_type()
        else:
            if self._unit in self._FLUID_UNIT_MAP:
                return self._encode_fluid_using_opil()
            elif self._unit in self._TEMPERATURE_UNIT_MAP:
                return self._encode_temperature_using_opil()
            elif self._unit in self._TIME_UNIT_MAP:
                return self._encode_timepoint_using_opil()
            else:
                return opil.Measure(float(self._value), ip_constants.NCIT_NOT_APPLICABLE)

    def to_structure_request(self):
        return {dc_constants.VALUE: float(self._value),
                dc_constants.UNIT: self._unit}

    def _get_sbol_measure_by_unit_type(self):
        if self._unit_type == ip_constants.UNIT_TYPE_FLUID:
            return self._encode_fluid_using_opil()
        elif self._unit_type == ip_constants.UNIT_TYPE_TIMEPOINT:
            return self._encode_timepoint_using_opil()
        elif self._unit_type == ip_constants.UNIT_TYPE_TEMPERATURE:
            return self._encode_temperature_using_opil()
        else:
            raise IntentParserException('%s measurement type not supported' % self._unit_type)

    def _encode_fluid_using_opil(self):
        if self._unit == '%':
            measure = opil.Measure(self._value, ip_constants.NCIT_CONCENTRATION)
            return measure
        elif self._unit == 'M':
            measure = opil.Measure(self._value, ip_constants.UO_MOLAR)
            return measure
        elif self._unit == 'mM':
            measure = opil.Measure(self._value, ip_constants.UO_MILLI_MOLAR)
            return measure
        elif self._unit == 'X':
            measure = opil.Measure(self._value, ip_constants.NCIT_FOLD_CHANGE)
            return measure
        elif self._unit == 'g/L':
            measure = opil.Measure(self._value, ip_constants.UO_GRAM_PER_LITER)
            return measure
        elif self._unit == 'ug/ml':
            measure = opil.Measure(self._value, ip_constants.NCIT_MICROGRAM_PER_MILLILITER)
            return measure
        elif self._unit == 'micromole':
            measure = opil.Measure(self._value, ip_constants.NCIT_MICROMOLE)
            return measure
        elif self._unit == 'nM':
            measure = opil.Measure(self._value, ip_constants.NCIT_NANOMOLE)
            return measure
        elif self._unit == 'uM':
            measure = opil.Measure(self._value, ip_constants.NCIT_MICROMOLE)
            return measure
        elif self._unit == 'mg/ml':
            measure = opil.Measure(self._value, ip_constants.UO_MILLIGRAM_PER_MILLILITER)
            return measure
        elif self._unit == 'ng/ul':
            measure = opil.Measure(self._value, ip_constants.UO_NANO_GRAM_PER_LITER)
            return measure
        elif self._unit == 'microlitre':
            measure = opil.Measure(self._value, ip_constants.OTU_MICROLITRE)
            return measure
        else:
            raise IntentParserException('%s is not a supported unit.' % self._unit)

    def _encode_temperature_using_opil(self):
        if self._unit == 'celsius':
            measure = opil.Measure(self._value, ip_constants.NCIT_CELSIUS)
            return measure
        elif self._unit == 'fahrenheit':
            measure = opil.Measure(self._value, ip_constants.NCIT_FAHRENHEIT)
            return measure
        else:
            raise IntentParserException('%s is not a supported unit.' % self._unit)

    def _encode_timepoint_using_opil(self):
        if self._unit == 'day':
            measure = opil.Measure(self._value, ip_constants.NCIT_DAY)
            return measure
        elif self._unit == 'hour':
            measure = opil.Measure(self._value, ip_constants.NCIT_HOUR)
            return measure
        elif self._unit == 'femtosecond':
            measure = opil.Measure(self._value, ip_constants.OTU_FEMTOSECOND)
            return measure
        elif self._unit == 'microsecond':
            measure = opil.Measure(self._value, ip_constants.NCIT_MICROSECOND)
            return measure
        elif self._unit == 'millisecond':
            measure = opil.Measure(self._value, ip_constants.NCIT_MILLISECOND)
            return measure
        elif self._unit == 'minute':
            measure = opil.Measure(self._value, ip_constants.NCIT_MINUTE)
            return measure
        elif self._unit == 'month':
            measure = opil.Measure(self._value, ip_constants.NCIT_MONTH)
            return measure
        elif self._unit == 'nanosecond':
            measure = opil.Measure(self._value, ip_constants.NCIT_NANOSECOND)
            return measure
        elif self._unit == 'picosecond':
            measure = opil.Measure(self._value, ip_constants.NCIT_PICOSECOND)
            return measure
        elif self._unit == 'second':
            measure = opil.Measure(self._value, ip_constants.NCIT_SECOND)
            return measure
        elif self._unit == 'week':
            measure = opil.Measure(self._value, ip_constants.NCIT_WEEK)
            return measure
        elif self._unit == 'year':
            measure = opil.Measure(self._value, ip_constants.NCIT_YEAR)
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

    def __init__(self, media_name: NamedLink):
        self._media_name = media_name
        self._media_values = []
        self._timepoint = None
        self._id_provider = IdProvider()

    def add_media_value(self, value: NamedLink):
        self._media_values.append(value)

    def get_media_name(self) -> NamedLink:
        return self._media_name

    def get_timepoint(self) -> TimepointIntent:
        return self._timepoint

    def set_timepoint(self, timepoint: TimepointIntent):
        if self._timepoint is not None:
            new_value = '%d %s' % (timepoint.get_value(), timepoint.get_unit())
            curr_value = '%d %s' % (self._timepoint.get_value(), self._timepoint.get_unit())
            raise IntentParserException(
                'Unable to assign media timepoint value %s when it currently has %s assigned.' % (new_value, curr_value))

        self._timepoint = timepoint

    def to_sbol(self, sbol_document):
        media_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                    component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        media_component.name = self._media_name.get_name()
        if self._media_name.get_link() is None:
            media_template = SubComponent(media_component)
            media_component.features = [media_template]
            sbol_document.add(media_component)
        else:
            media_template = SubComponent(self._media_name.get_link())
            media_component.features = [media_template]
            sbol_document.add(media_component)

        if self._timepoint is not None:
            media_timepoint_measure = self._timepoint.to_opil()
            media_template.measures = [media_timepoint_measure]

        media_variable = VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                         cardinality=sbol_constants.SBOL_ONE)
        media_variable.variable = media_template

        media_variants = []
        for media_value in self._media_values:
            media_value_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                              component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            media_value_component.name = media_value.get_name()

            if media_value.get_link() is not None:
                media_value_sub_component = SubComponent(media_value.get_link())
                media_value_component.features = [media_value_sub_component]
            media_variants.append(media_value_component)

        media_variable.variants = media_variants
        return media_template, media_variable

    def to_structure_request(self):
        sr_media = []
        for value in self._media_values:
            media = {dc_constants.NAME: self._media_name.to_structure_request(),
                     dc_constants.VALUE: value.get_name()}
            if self._timepoint:
                media[dc_constants.TIMEPOINT] = self._timepoint.to_structure_request()
            sr_media.append(media)
        return sr_media


class ReagentIntent(object):

    def __init__(self, reagent_name: NamedLink):
        self._reagent_name = reagent_name
        self._reagent_values = []
        self._timepoint = None
        self._id_provider = IdProvider()

    def add_reagent_value(self, value: MeasuredUnit):
        self._reagent_values.append(value)

    def get_reagent_name(self):
        return self._reagent_name

    def get_timepoint(self):
        return self._timepoint

    def get_reagent_values(self):
        return self._reagent_values

    def set_timepoint(self, timepoint: TimepointIntent):
        if self._timepoint is not None:
            new_value = '%d %s' % (timepoint.get_value(), timepoint.get_unit())
            curr_value = '%d %s' % (self._timepoint.get_value(), self._timepoint.get_unit())
            raise IntentParserException(
                'Unable to assign reagent timepoint value %s when it currently has %s assigned.' % (new_value, curr_value))

        self._timepoint = timepoint

    def to_sbol(self, sbol_document):
        reagent_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                      component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        reagent_component.name = self._reagent_name.get_name()
        if self._reagent_name.get_link() is None:
            reagent_template = SubComponent(reagent_component)
            reagent_component.features = [reagent_template]
            sbol_document.add(reagent_component)
        else:
            reagent_template = SubComponent(self._reagent_name.get_link())
            reagent_component.features = [reagent_template]
            sbol_document.add(reagent_component)

        if self._timepoint is not None:
            reagent_timepoint_measure = self._timepoint.to_opil()
            reagent_template.measures = [reagent_timepoint_measure]

        reagent_variable = VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                           cardinality=sbol_constants.SBOL_ONE)
        reagent_variable.variable = reagent_template

        reagent_variant_measures = [reagent_value.to_opil() for reagent_value in self._reagent_values]
        if len(reagent_variant_measures) > 0:
            reagent_variable.variant_measure = reagent_variant_measures

        return reagent_template, reagent_variable, reagent_component

    def to_structure_request(self):
        sr_reagent = []
        for value in self._reagent_values:
            reagent = {dc_constants.NAME: self._reagent_name.to_structure_request(),
                       dc_constants.VALUE: str(value.get_value()),
                       dc_constants.UNIT: value.get_unit()}
            if self._timepoint:
                reagent[dc_constants.TIMEPOINT] = self._timepoint.to_structure_request()
            sr_reagent.append(reagent)
        return sr_reagent
