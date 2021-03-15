from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.utils.id_provider import IdProvider
from sbol3 import Component, SubComponent, VariableFeature
from typing import Union
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.constants.intent_parser_constants as ip_constants
import opil
import sbol3.constants as sbol_constants
import tyto

class MeasuredUnit(object):

    def __init__(self, value: Union[float, int], unit: str, unit_type=None):
        self._value = value
        self._unit = unit
        self._unit_type = unit_type

    def get_unit(self):
        return self._unit

    def get_value(self):
        return self._value

    def to_opil(self):
        if self._unit in ip_constants.FLUID_UNIT_MAP:
            unit_uri = ip_constants.FLUID_UNIT_MAP[self._unit]
            return opil.Measure(self._value, unit_uri)
        elif self._unit in ip_constants.TEMPERATURE_UNIT_MAP:
            unit_uri = ip_constants.TEMPERATURE_UNIT_MAP[self._unit]
            return opil.Measure(self._value, unit_uri)
        elif self._unit in ip_constants.TIME_UNIT_MAP:
            unit_uri = ip_constants.TIME_UNIT_MAP[self._unit]
            return opil.Measure(self._value, unit_uri)
        else:
            return opil.Measure(self._value, tyto.OM.number)

    def to_structured_request(self):
        return {dc_constants.VALUE: float(self._value),
                dc_constants.UNIT: self._unit}

class TemperatureIntent(MeasuredUnit):

    def __init__(self, value: float, unit: str):
        super().__init__(value, unit, unit_type=ip_constants.UNIT_TYPE_TEMPERATURE)

class TimepointIntent(MeasuredUnit):

    def __init__(self, value: Union[float, int], unit: str):
        super().__init__(value, unit, unit_type=ip_constants.UNIT_TYPE_TIMEPOINTS)

class NamedLink(object):

    def __init__(self, name, link=None):
        self._name = name
        self._link = link

    def get_name(self):
        return self._name

    def get_link(self):
        return self._link

    def to_structured_request(self):
        return {dc_constants.LABEL: self._name,
                dc_constants.SBH_URI: self._link if self._link else dc_constants.NO_PROGRAM_DICTIONARY}


class NamedBooleanValue(object):

    def __init__(self, named_link: NamedLink, value: bool):
        self._named_link = named_link
        self._value = value

    def get_value(self):
        return self._value

    def to_structured_request(self):
        return {dc_constants.NAME: self._named_link.to_structured_request(),
                dc_constants.VALUE: str(self._value)}

class NamedIntegerValue(object):

    def __init__(self, named_link: NamedLink, value: int):
        self._named_link = named_link
        self._value = value

    def get_value(self):
        return self._value

    def to_structured_request(self):
        return {dc_constants.NAME: self._named_link.to_structured_request(),
                dc_constants.VALUE: self._value}

class NamedStringValue(object):

    def __init__(self, named_link: NamedLink, value=''):
        self._named_link = named_link
        self._value = value

    def get_named_link(self):
        return self._named_link

    def get_value(self):
        return self._value

    def to_structured_request(self):
        result = {dc_constants.NAME: self._named_link.to_structured_request()}
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

    def to_structured_request(self):
        sr_media = []
        for value in self._media_values:
            media = {dc_constants.NAME: self._media_name.to_structured_request(),
                     dc_constants.VALUE: value.get_name()}
            if self._timepoint:
                media[dc_constants.TIMEPOINT] = self._timepoint.to_structured_request()
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

    def to_structured_request(self):
        sr_reagent = []
        for value in self._reagent_values:
            reagent = {dc_constants.NAME: self._reagent_name.to_structured_request(),
                       dc_constants.VALUE: str(value.get_value()),
                       dc_constants.UNIT: value.get_unit()}
            if self._timepoint:
                reagent[dc_constants.TIMEPOINT] = self._timepoint.to_structured_request()
            sr_reagent.append(reagent)
        return sr_reagent
