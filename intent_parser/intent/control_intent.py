from intent_parser.intent.measurement_intent import ReagentIntent, NamedStringValue
from intent_parser.intent_parser_exceptions import IntentParserException
from sbol3 import CombinatorialDerivation, Component, Feature, SubComponent, TextProperty, VariableFeature
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.constants.intent_parser_constants as ip_constants
import sbol3.constants as sbol_constants

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

    def to_opil(self, opil_measurement):
        if self._channel is not None:
            self._encode_channel_using_opil(opil_measurement)
        if self._control_type is not None:
            self._encode_control_type_using_opil(opil_measurement)
        if len(self._timepoints) > 0:
            self._encode_timepoints_using_opil(opil_measurement)

    def to_sbol(self):
        all_sample_templates = []
        all_sample_variables = []

        if len(self._strains) > 0:
            strain_template, strain_variable = self._encode_strains_using_sbol()
            all_sample_templates.append(strain_template)
            all_sample_variables.append(strain_variable)
        if len(self._contents) > 0:
            content_template, content_variable = self._encode_content_using_sbol()
            all_sample_templates.append(content_template)
            all_sample_variables.append(content_variable)

        sample_template = Component(identity=ip_constants.SD2E_LINK + '#Control_Template',
                                    component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        sample_template.features = all_sample_templates

        sample_combinations = CombinatorialDerivation(identity=ip_constants.SD2E_LINK + '#control_combinatorial_derivation',
                                                      template=sample_template)
        # TODO: update .variable_components to .variable_feature
        sample_combinations.variable_components = all_sample_variables
        return sample_combinations

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

    def _encode_channel_using_opil(self, opil_measurement):
        opil_measurement.annotation_property = TextProperty(opil_measurement, 0, 1)
        opil_measurement.annotation_property = self._channel

    def _encode_content_using_sbol(self):
        content_template = Feature(identity=ip_constants.SD2E_LINK + '#content_template',
                                   type_uri=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        content_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)

        content_variants = []
        content_variant_measures = []
        for content in self._contents:
            if isinstance(content, ReagentIntent):
                content_component = content.to_sbol()
                content_variants.append(content_component)
                if content.get_timepoint() is not None:
                    content_variant_measure = content.get_timepoint().to_sbol()
                    content_variant_measures.append(content_variant_measure)
            elif isinstance(content, NamedStringValue):
                content_component = Component(identity=ip_constants.SD2E_LINK + '#' + content.get_named_link().get_name(),
                                              component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
                content_sub_component = SubComponent(content.get_named_link().get_link())
                content_component.features = [content_sub_component.identity]
                content_variants.append(content_component)

        content_variable.variable = content_template
        content_variable.variant = content_variants
        content_variable.variant_measure = content_variant_measures
        return content_template, content_variable

    def _encode_control_type_using_opil(self, opil_measurement):
        opil_measurement.control_type = TextProperty(opil_measurement,
                                                     ip_constants.SD2E_LINK + '#control_type',
                                                     0,
                                                     1)
        opil_measurement.control_type = self._control_type

    def _encode_timepoints_using_opil(self, opil_measurement):
        opil_measurement.time = [timepoint.to_sbol() for timepoint in self._timepoints]

    def _encode_strains_using_sbol(self):
        strain_template = Feature(identity=ip_constants.SD2E_LINK + '#strain_template',
                                  type_uri=ip_constants.NCIT_STRAIN_URI)
        strain_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        strain_variable.variable = strain_template
        strain_variable.variant = [strain.to_sbol() for strain in self._strains]

        return strain_template, strain_variable