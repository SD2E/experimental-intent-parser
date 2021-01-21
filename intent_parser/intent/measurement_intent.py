
from sbol3 import BooleanProperty, Collection, CombinatorialDerivation, Component, FloatProperty, IntProperty, TextProperty
from sbol3 import Measure, LocalSubComponent, SubComponent, URIProperty, VariableComponent
from intent_parser.intent.control_intent import ControlIntent
from intent_parser.intent.strain_intent import StrainIntent
from intent_parser.intent_parser_exceptions import IntentParserException
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
from typing import List, Union
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

    def to_structure_request(self):
        return {dc_constants.VALUE: float(self._value),
                dc_constants.UNIT: self._unit}


class TemperatureIntent(MeasuredUnit):

    def __init__(self, value: float, unit: str):
        super().__init__(value, unit, 'temperature')


class TimepointIntent(MeasuredUnit):

    def __init__(self, value: Union[float, int], unit: str):
        super().__init__(value, unit, 'timepoint')


class MeasurementIntent(object):

    def __init__(self):
        self.sample_id = 1

        self.intent = {}
        self._measurement_type = None
        self._file_type = []
        self._batches = []
        self._contents = MeasurementContent()
        self._controls = []
        self._optical_densities = []
        self._replicates = []
        self._strains = []
        self._temperatures = []
        self._timepoints = []

    def add_batch(self, batch: int):
        self._batches.append(batch)

    def add_content(self, content):
        self._contents.add_content_intent(content)

    def add_control(self, control: ControlIntent):
        self._controls.append(control)

    def add_file_type(self, file_type: str):
        self._file_type.append(file_type)

    def add_optical_density(self, ods: float):
        self._optical_densities.append(ods)

    def add_replicate(self, replicate: int):
        self._replicates.append(replicate)

    def add_strain(self, strain: StrainIntent):
        self._strains.append(strain)

    def add_temperature(self, temperature: TemperatureIntent):
        self._temperatures.append(temperature)

    def add_timepoint(self, timepoint: TimepointIntent):
        self._timepoints.append(timepoint)

    def get_contents(self):
        return self._contents

    def get_file_types(self):
        return self._file_type

    def get_measurement_type(self):
        return self._measurement_type

    def is_empty(self):
        return (self._measurement_type is None and
                len(self._file_type) == 0 and
                len(self._batches) == 0 and
                self._contents.is_empty() and
                len(self._controls) == 0 and
                len(self._optical_densities) == 0 and
                len(self._replicates) == 0 and
                len(self._strains) == 0 and
                len(self._temperatures) == 0 and
                len(self._timepoints) == 0)

    def set_measurement_type(self, measurement_type: str):
        self._measurement_type = measurement_type

    def to_sbol_for_samples(self):
        all_sample_templates = []
        all_sample_variables = []

        for content in self._contents.get_contents():
            sample_templates, sample_variables = content.to_sbol_for_samples()
            all_sample_templates.extend(sample_templates)
            all_sample_variables.extend(sample_variables)

        strain_template, strain_variable = self._encode_strains_using_sbol()
        all_sample_templates.extend(strain_template)
        all_sample_variables.extend(strain_variable)

        sample_template = Component('Measurement_Template')
        sample_combinations = CombinatorialDerivation('measurement_combinatorial_derivation', sample_template)
        sample_combinations.variable_components = all_sample_variables
        sample_combinations.has_features = all_sample_templates

        return sample_combinations

    def to_sbol_for_measurement(self):
        opil_measurement = opil.Measurement()
        if self._measurement_type:
            self._encode_measurement_type_using_sbol(opil_measurement)
        if len(self._file_type) > 0:
            self._encode_file_type_using_sbol(opil_measurement)
        if len(self._batches) > 0:
            self._encode_batches_using_sbol(opil_measurement)
        if not self._contents.is_empty():
            for content in self._contents.get_contents():
                content.to_sbol_for_measurement(opil_measurement)
        if len(self._controls) > 0:
            pass # TODO:
        if len(self._optical_densities) > 0:
            self._encode_optical_densities(opil_measurement)
        if len(self._replicates) > 0:
            self._encode_replicates_using_sbol(opil_measurement)
        if len(self._temperatures) > 0:
            self._encode_temperature_using_sbol(opil_measurement)
        if len(self._timepoints) > 0:
            self._encode_timepoint_using_sbol(opil_measurement)

        return opil_measurement

    def to_structure_request(self):
        if self._measurement_type is None:
            raise IntentParserException("A structured request must have a measurement-type but none is set.")
        if len(self._file_type) == 0:
            raise IntentParserException("A structured request must have a file-type but file-type is empty.")

        structure_request = {dc_constants.MEASUREMENT_TYPE: self._measurement_type,
                             dc_constants.FILE_TYPE: self._file_type}

        if len(self._replicates) > 0:
            structure_request[dc_constants.REPLICATES] = self._replicates
        if len(self._strains) > 0:
            structure_request[dc_constants.STRAINS] = [strain.to_structure_request() for strain in self._strains]
        if len(self._optical_densities) > 0:
            structure_request[dc_constants.ODS] = self._optical_densities
        if len(self._temperatures) > 0:
            structure_request[dc_constants.TEMPERATURES] = [temperature.to_structure_request() for temperature in self._temperatures]
        if len(self._timepoints) > 0:
            structure_request[dc_constants.TIMEPOINTS] = [timepoint.to_structure_request() for timepoint in self._timepoints]
        if len(self._batches) > 0:
            structure_request[dc_constants.BATCH] = self._batches
        if len(self._controls) > 0:
            structure_request[dc_constants.CONTROLS] = [control.to_structure_request() for control in self._controls]
        if not self._contents.is_empty():
            structure_request.update(self._contents.to_structure_request())

        return structure_request

    def _encode_batches_using_sbol(self, opil_measurement):
        for batch_value in self._batches:
            opil_measurement.annotation_property = IntProperty(opil_measurement, 0, 1) # TODO: what is property owner?
            opil_measurement.annotation_property = batch_value # TODO: custom annotaton must declare as annotation_property?

    def _encode_file_type_using_sbol(self, opil_measurement):
        for file_type in self._file_type:
            opil_measurement.annotation_property = TextProperty(opil_measurement, 0, 1)
            opil_measurement.annotation_property = file_type

    def _encode_measurement_type_using_sbol(self, opil_measurement):
        measurement_type = opil.MeasurementType('measurement_type')
        measurement_type.required = True
        if self._measurement_type == ip_constants.MEASUREMENT_TYPE_FLOW:
            measurement_type.type = ip_constants.NCIT_FLOW_URI
        elif self._measurement_type == ip_constants.MEASUREMENT_TYPE_RNA_SEQ:
            measurement_type.type = ip_constants.NCIT_RNA_SEQ_URI
        elif self._measurement_type == ip_constants.MEASUREMENT_TYPE_DNA_SEQ:
            measurement_type.type = ip_constants.NCIT_DNA_SEQ_URI
        elif self._measurement_type == ip_constants.MEASUREMENT_TYPE_PROTEOMICS:
            measurement_type.type = ip_constants.NCIT_PROTEOMICS_URI
        elif self._measurement_type == ip_constants.MEASUREMENT_TYPE_SEQUENCING_CHROMATOGRAM:
            measurement_type.type = ip_constants.NCIT_SEQUENCING_CHROMATOGRAM_URI
        elif self._measurement_type == ip_constants.MEASUREMENT_TYPE_AUTOMATED_TEST:
            measurement_type.type = ip_constants.SD2_AUTOMATED_TEST_URI
        elif self._measurement_type == ip_constants.MEASUREMENT_TYPE_CFU:
            measurement_type.type = ip_constants.NCIT_CFU_URI
        elif self._measurement_type == ip_constants.MEASUREMENT_TYPE_PLATE_READER:
            measurement_type.type = ip_constants.NCIT_PLATE_READER_URI
        elif self._measurement_type == ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE:
            measurement_type.type = ip_constants.SD2_CONDITION_SPACE_URI
        elif self._measurement_type == ip_constants.MEASUREMENT_TYPE_EXPERIMENTAL_DESIGN:
            measurement_type.type = ip_constants.SD2_EXPERIMENTAL_DESIGN_URI
        else:
            raise IntentParserException(
                'Unable to create an opil measurement-type: %s not supported' % self._measurement_type)
        opil_measurement.instance_of = measurement_type

    def _encode_optical_densities(self, opil_measurement):
        for optical_density in self._optical_densities:
            opil_measurement.annotation_property = FloatProperty(opil_measurement, 0, 1)  # TODO: what is property owner?
            opil_measurement.annotation_property = optical_density  # TODO: custom annotaton must declare as annotation_property?

    def _encode_replicates_using_sbol(self, opil_measurement):
        for replicate in self._replicates:
            opil_measurement.annotation_property = IntProperty(opil_measurement, 0,
                                                                 1)  # TODO: what is property owner?
            opil_measurement.annotation_property = replicate  # TODO: custom annotaton must declare as annotation_property?

    def _encode_strains_using_sbol(self):
        strain_template = LocalSubComponent(name='strain_template', types=[ip_constants.NCIT_STRAIN_URI])
        strain_variable = VariableComponent(cardinality=sbol_constants.SBOL_ONE_OR_MORE)
        strain_variable.variable = strain_template

        chosen_strains = []
        strain_component = Component('strain_component', sbol_constants.SBO_DNA)
        for strain in self._strains:
            strain_sub_component = SubComponent(strain.get_strain_reference_link())
            chosen_strains.append(strain_sub_component)

        strain_component.features = chosen_strains
        strain_collection = Collection('strain_collection')
        strain_collection.members = [encoded_strain.identity for encoded_strain in chosen_strains]
        strain_variable.variant_collection = strain_collection

        return strain_template, strain_variable

    def _encode_timepoint_using_sbol(self, opil_measurement):
        encoded_timepoints = []
        for timepoint in self._timepoints:
            if timepoint.get_unit() == 'day':
                encoded_time = Measure(timepoint.get_value(), 'http://www.ontology-of-units-of-measure.org/resource/om-2/month')
                encoded_timepoints.append(encoded_time)
            elif timepoint.get_unit() == 'hour':
                encoded_time = Measure(timepoint.get_value(), 'http://www.ontology-of-units-of-measure.org/resource/om-2/hour')
                encoded_timepoints.append(encoded_time)
            elif timepoint.get_unit() == 'femtosecond':
                encoded_time = Measure(timepoint.get_value(), 'http://www.ontology-of-units-of-measure.org/resource/om-2/femtosecond-Time')
                encoded_timepoints.append(encoded_time)
            elif timepoint.get_unit() == 'microsecond':
                encoded_time = Measure(timepoint.get_value(), 'http://www.ontology-of-units-of-measure.org/resource/om-2/microsecond-Time')
                encoded_timepoints.append(encoded_time)
            elif timepoint.get_unit() == 'millisecond':
                encoded_time = Measure(timepoint.get_value(), 'http://www.ontology-of-units-of-measure.org/resource/om-2/millisecond-Time')
                encoded_timepoints.append(encoded_time)
            elif timepoint.get_unit() == 'minute':
                encoded_time = Measure(timepoint.get_value(), 'http://www.ontology-of-units-of-measure.org/resource/om-2/minute-Time')
                encoded_timepoints.append(encoded_time)
            elif timepoint.get_unit() == 'month':
                encoded_time = Measure(timepoint.get_value(), 'http://www.ontology-of-units-of-measure.org/resource/om-2/day')
                encoded_timepoints.append(encoded_time)
            elif timepoint.get_unit() == 'nanosecond':
                encoded_time = Measure(timepoint.get_value(), 'http://www.ontology-of-units-of-measure.org/resource/om-2/nanosecond-Time')
                encoded_timepoints.append(encoded_time)
            elif timepoint.get_unit() == 'picosecond':
                encoded_time = Measure(timepoint.get_value(), 'http://www.ontology-of-units-of-measure.org/resource/om-2/picosecond-Time')
                encoded_timepoints.append(encoded_time)
            elif timepoint.get_unit() == 'second':
                encoded_time = Measure(timepoint.get_value(), 'http://www.ontology-of-units-of-measure.org/resource/om-2/second-Time')
                encoded_timepoints.append(encoded_time)
            elif timepoint.get_unit() == 'week':
                encoded_time = Measure(timepoint.get_value(), 'http://www.ontology-of-units-of-measure.org/resource/om-2/week')
                encoded_timepoints.append(encoded_time)
            elif timepoint.get_unit() == 'year':
                encoded_time = Measure(timepoint.get_value(), 'http://www.ontology-of-units-of-measure.org/resource/om-2/year')
                encoded_timepoints.append(encoded_time)
            else:
                raise IntentParserException('unit %s not supported.' % timepoint.get_unit())

        opil_measurement.time = encoded_timepoints

    def _encode_temperature_using_sbol(self, opil_measurement):
        # TODO: confirm if there is a opil.temperature field for an opil.measurement object
        for temperature in self._temperatures:
            if temperature.get_unit() == 'celsius':
                opil_measurement.temperature = Measure(temperature.get_value(),
                                                       'http://www.ontology-of-units-of-measure.org/resource/om-2/degreeCelsius')
            elif temperature.get_unit() == 'fahrenheit':
                opil_measurement.temperature = Measure(temperature.get_value(),
                                                       'http://www.ontology-of-units-of-measure.org/resource/om-2/degreeFahrenheit')

class MeasurementContent(object):

    def __init__(self):
        self._contents = []

    def add_content_intent(self, content_intent):
        self._contents.append(content_intent)

    def get_contents(self):
        return self._contents

    def is_empty(self):
        return len(self._contents) == 0

    def to_structure_request(self):
        return {dc_constants.CONTENTS: content.to_structure_request() for content in self._contents}

class ContentIntent(object):

    def __init__(self):
        self._column_ids = []
        self._dna_reaction_concentrations = []
        self._lab_ids = []
        self._medias = []
        self._num_neg_controls = []
        self._reagents = []
        self._rna_inhibitor_reaction_flags = []
        self._row_ids = []
        self._template_dna_values = []

    def add_media(self, media):
        self._medias.append(media)

    def add_reagent(self, reagent):
        self._reagents.append(reagent)

    def get_row_ids(self):
        return self._row_ids

    def set_column_ids(self, col_ids):
        self._column_ids = col_ids

    def set_dna_reaction_concentrations(self, dna_reaction_concentrations):
        self._dna_reaction_concentrations = dna_reaction_concentrations

    def set_lab_ids(self, lab_ids):
        self._lab_ids = lab_ids

    def set_numbers_of_negative_controls(self, neg_control):
        self._num_neg_controls = neg_control

    def set_rna_inhibitor_reaction_flags(self, rna_inhibitor_reactions):
        self._rna_inhibitor_reaction_flags = rna_inhibitor_reactions

    def set_row_ids(self, row_ids):
        self._row_ids = row_ids

    def set_template_dna_values(self, template_dna_values):
        self._template_dna_values = template_dna_values

    def is_empty(self):
        return (len(self._num_neg_controls) == 0 and
                len(self._rna_inhibitor_reaction_flags) == 0 and
                len(self._dna_reaction_concentrations) == 0 and
                len(self._template_dna_values) == 0 and
                len(self._column_ids) == 0 and
                len(self._row_ids) == 0 and
                len(self._lab_ids) == 0 and
                len(self._reagents) == 0 and
                len(self._medias) == 0)

    def to_sbol_for_measurement(self, opil_measurement):
        self._encode_col_ids_using_sbol(opil_measurement)
        self._encode_dna_reaction_concentration(opil_measurement)
        self._encode_lab_ids_using_sbol(opil_measurement)
        self._encode_number_of_negative_controls_using_sbol(opil_measurement)
        self._encode_rna_inhibitor_using_sbol(opil_measurement)
        self._encode_row_ids_using_sbol(opil_measurement)
        self._encode_template_dna_using_sbol(opil_measurement)

    def to_sbol_for_samples(self):
        media_template, media_variable = self._encode_media_using_sbol()
        reagent_template, reagent_variable = self._encode_reagent_using_sbol()

        all_templates = [media_template, reagent_template]
        all_variables = [media_variable, reagent_variable]
        return all_templates, all_variables

    def to_structure_request(self):
        structure_request = []
        if len(self._num_neg_controls) > 0:
            structure_request.append([num_neg_control.to_structure_request() for num_neg_control in self._num_neg_controls])
        if len(self._rna_inhibitor_reaction_flags) > 0:
            structure_request.append([rna_inhibitor_reaction.to_structure_request() for rna_inhibitor_reaction in self._rna_inhibitor_reaction_flags])
        if len(self._dna_reaction_concentrations) > 0:
            structure_request.append([dna_reaction_concentration.to_structure_request() for dna_reaction_concentration in self._dna_reaction_concentrations])
        if len(self._template_dna_values) > 0:
            structure_request.append([template_dna.to_structure_request() for template_dna in self._template_dna_values])
        if len(self._column_ids) > 0:
            structure_request.append([col_id.to_structure_request() for col_id in self._column_ids])
        if len(self._row_ids) > 0:
            structure_request.append([row_id.to_structure_request() for row_id in self._row_ids])
        if len(self._lab_ids) > 0:
            structure_request.append([lab_id.to_structure_request() for lab_id in self._lab_ids])
        if len(self._reagents):
            structure_request.append([reagent.to_structure_request() for reagent in self._reagents])
        if len(self._medias) > 0:
            structure_request.append([media.to_structure_request() for media in self._medias])

        return structure_request

    def _encode_col_ids_using_sbol(self, opil_measurement):
        for col_id in self._column_ids:
            opil_measurement.annotation_property = IntProperty(opil_measurement, 0, 1) # TODO: what is property owner?
            opil_measurement.annotation_property = col_id # TODO: custom annotaton must declare as annotation_property?

    def _encode_dna_reaction_concentration(self, opil_measurement):
        for dna_reaction in self._dna_reaction_concentrations:
            opil_measurement.annotation_property = IntProperty(opil_measurement, 0, 1)
            opil_measurement.annotation_property = dna_reaction

    def _encode_lab_ids_using_sbol(self, opil_measurement):
        for lab_id in self._lab_ids:
            opil_measurement.annotation_property = TextProperty(opil_measurement, 0, 1) # TODO: what is property owner?
            opil_measurement.annotation_property = lab_id # TODO: custom annotaton must declare as annotation_property?

    def _encode_media_using_sbol(self):
        media_template = LocalSubComponent(name='media_template', types=[ip_constants.NCIT_MEDIA_URI])
        media_variable = VariableComponent(cardinality=sbol_constants.SBOL_ONE_OR_MORE)
        media_variable.variable = media_template

        chosen_medias = []
        media_component = Component('media_component', ip_constants.NCIT_MEDIA_URI)
        for media in self._medias:
            media_sub_component = SubComponent(media.get_media_name().get_link())
            chosen_medias.append(media_sub_component)

        media_component.features = chosen_medias
        media_collection = Collection(name='media_collection')
        media_collection.members = [encoded_media.identity for encoded_media in chosen_medias]
        media_variable.variant_collection = media_collection
        return media_template, media_variable

    def _encode_number_of_negative_controls_using_sbol(self, opil_measurement):
        for neg_control in self._num_neg_controls:
            opil_measurement.annotation_property = IntProperty(opil_measurement, 0, 1) # TODO: what is property owner?
            opil_measurement.annotation_property = neg_control # TODO: custom annotaton must declare as annotation_property?

    def _encode_reagent_using_sbol(self):
        reagent_template = LocalSubComponent(name='reagent_template', types=[ip_constants.NCIT_INDUCER_URI])
        reagent_variable = VariableComponent(cardinality=sbol_constants.SBOL_ONE_OR_MORE)
        reagent_variable.variable = reagent_template

        chosen_reagents = []
        reagent_component = Component('reagent_component', ip_constants.NCIT_INDUCER_URI)
        for reagent in self._reagents:
            reagent_sub_component = SubComponent(reagent.get_reagent_name().get_link())
            chosen_reagents.append(reagent_sub_component)

            # TODO: where to map these additional information?
            reagent.get_timepoint()
            reagent.get_value()
            reagent.get_unit()

        reagent_component.features = chosen_reagents
        reagent_collection = Collection(name='media_collection')
        reagent_collection.members = [encoded_reagent.identity for encoded_reagent in chosen_reagents]
        reagent_variable.variant_collection = reagent_collection
        return reagent_template, reagent_variable

    def _encode_rna_inhibitor_using_sbol(self, opil_measurement):
        for boolean_flag in self._rna_inhibitor_reaction_flags:
            opil_measurement.annotation_property = BooleanProperty(opil_measurement, 0, 1)
            opil_measurement.annotation_property = boolean_flag

    def _encode_row_ids_using_sbol(self, opil_measurement):
        for row_id in self._row_ids:
            opil_measurement.annotation_property = IntProperty(opil_measurement, 0, 1) # TODO: what is property owner?
            opil_measurement.annotation_property = row_id # TODO: custom annotaton must declare as annotation_property?

    def _encode_template_dna_using_sbol(self, opil_measurement):
        for template_dna in self._dna_reaction_concentrations:
            opil_measurement.annotation_property = TextProperty(opil_measurement, 0, 1)
            opil_measurement.annotation_property = template_dna

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

    def to_structure_request(self):
        result = {dc_constants.NAME: self._named_link.to_structure_request()}
        if self._value:
            result[dc_constants.VALUE] = self._value
        return result

class MediaIntent(object):

    def __init__(self, media_name: NamedLink, media_value: str):
        self._media_name = media_name
        self._media_value = media_value
        self._timepoint = None

    def get_media_name(self) -> NamedLink:
        return self._media_name

    def set_timepoint(self, timepoint: TimepointIntent):
        self._timepoint = timepoint

    def to_structure_request(self):
        media = {dc_constants.NAME: self._media_name.to_structure_request(),
                 dc_constants.VALUE: self._media_value}

        if self._timepoint:
            media[dc_constants.TIMEPOINT] = self._timepoint.to_structure_request()

        return media

class ReagentIntent(MeasuredUnit):

    def __init__(self, reagent_name: NamedLink, value: float, unit: str):
        super().__init__(value, unit, 'fluid')
        self._reagent_name = reagent_name
        self._timepoint = None

    def get_reagent_name(self):
        return self._reagent_name

    def get_timepoint(self):
        return self._timepoint

    def set_timepoint(self, timepoint: TimepointIntent):
        self._timepoint = timepoint

    def to_structure_request(self):
        reagent = {dc_constants.NAME: self._reagent_name.to_structure_request(),
                   dc_constants.VALUE: str(self._value),
                   dc_constants.UNIT: self._unit}
        if self._timepoint:
            reagent[dc_constants.TIMEPOINT] = self._timepoint.to_structure_request()

        return reagent



