
from sbol3 import BooleanProperty, CombinatorialDerivation, Component, Feature, FloatProperty, IntProperty, TextProperty
from sbol3 import Measure, LocalSubComponent, SubComponent, VariableFeature
from intent_parser.intent.control_intent import ControlIntent
from intent_parser.intent.strain_intent import StrainIntent
from intent_parser.intent_parser_exceptions import IntentParserException
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
from typing import Union
import opil
import intent_parser.protocols.opil_parameter_utils as opil_utils
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
            return Measure(self._value, ip_constants.NCIT_CONCENTRATION)
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

    def to_sbol(self):
        all_sample_templates = []
        all_sample_variables = []

        media_template = None
        for content in self._contents.get_contents():
            media_templates, media_variables = content.to_sbol_for_media()
            reagent_templates, reagent_variables = content.to_sbol_for_reagent()
            col_id_template, col_id_variable = content.to_sbol_for_col_ids()
            dna_reaction_concentration_template, dna_reaction_concentration_variable = content.to_sbol_for_dna_reaction_concentration()
            lab_id_template, lab_id_variable = content.to_sbol_for_lab_ids()
            num_neg_control_template, num_neg_control_variable = content.to_sbol_for_number_of_negative_controls()
            use_rna_inhib_template, use_rna_inhib_variable = content.to_sbol_for_use_rna_inhibitor()
            row_id_template, row_id_variable = content.to_sbol_for_row_ids()
            template_dna_template, template_dna_variable = content.to_sbol_for_template_dna()

            all_sample_templates.extend([media_templates,
                                         reagent_templates,
                                         col_id_template,
                                         dna_reaction_concentration_template,
                                         lab_id_template,
                                         num_neg_control_template,
                                         use_rna_inhib_template,
                                         row_id_template,
                                         template_dna_template])
            all_sample_variables.extend([media_variables,
                                         reagent_variables,
                                         col_id_variable,
                                         dna_reaction_concentration_variable,
                                         lab_id_variable,
                                         num_neg_control_variable,
                                         use_rna_inhib_variable,
                                         row_id_variable,
                                         template_dna_variable])

        if len(self._strains) > 0:
            strain_template, strain_variable = self._encode_strains_using_sbol()
            all_sample_templates.append(strain_template)
            all_sample_variables.append(strain_variable)

        if len(self._temperatures) > 0:
            temperature_variable = self._encode_temperature_using_sbol()
            temperature_variable.variable = media_template

        if len(self._batches) > 0:
            batch_template, batch_variable = self._encode_batches_using_sbol()
            all_sample_templates.append(batch_template)
            all_sample_variables.append(batch_variable)

        if len(self._replicates) > 0:
            replicate_template, replicate_variable = self._encode_replicates_using_sbol()
            all_sample_templates.append(replicate_template)
            all_sample_variables.append(replicate_variable)

        if len(self._controls) > 0:
            control_template, control_variable = self._encode_control_using_sbol()
            all_sample_templates.append(control_template)
            all_sample_variables.append(control_variable)

        if len(self._optical_densities) > 0:
            ods_template, ods_variable = self._encode_optical_densities()
            all_sample_templates.append(ods_template)
            all_sample_variables.append(ods_variable)

        sample_template = Component(identity=ip_constants.SD2E_LINK + '#measurement_template',
                                    component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        sample_template.features = all_sample_templates

        sample_combinations = CombinatorialDerivation('measurement_combinatorial_derivation', sample_template)
        sample_combinations.variable_components = all_sample_variables

        return sample_combinations

    def to_opil(self):
        opil_measurement = opil.Measurement('IntentParser_Measurement')
        if self._measurement_type:
            self._encode_measurement_type_using_opil(opil_measurement)
        if len(self._file_type) > 0:
            self._encode_file_type_using_opil(opil_measurement)
        if len(self._timepoints) > 0:
            self._encode_timepoint_using_opil(opil_measurement)
        if len(self._controls) > 0:
            for control in self._controls:
                control.to_opil(opil_measurement)

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

    def _encode_batches_using_sbol(self):
        batch_template = Feature(identity=ip_constants.SD2E_LINK + '#batch_template',
                                 type_uri=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        batch_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        batch_variable.variable = batch_template
        batch_variable.variant_measure = [Measure(value, ip_constants.NCIT_NOT_APPLICABLE) for value in self._batches]
        return batch_template, batch_variable

    def _encode_file_type_using_opil(self, opil_measurement):
        for file_type in self._file_type:
            opil_measurement.file_type = TextProperty(opil_measurement,
                                                      '%s#file_type' % ip_constants.SD2E_LINK,
                                                      0,
                                                      1)
            opil_measurement.file_type = file_type

    def _encode_measurement_type_using_opil(self, opil_measurement):
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

    def _encode_control_using_sbol(self):
        control_template = Feature(identity=ip_constants.SD2E_LINK + '#control_template',
                                   type_uri=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        control_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        control_variable.variable = control_template
        control_variable.variant_derivation = [control.to_sbol() for control in self._controls]
        return control_template, control_variable

    def _encode_optical_densities(self):
        ods_template = Feature(identity=ip_constants.SD2E_LINK + '#ods_template',
                               type_uri=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        ods_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        ods_variable.variable = ods_template
        ods_variable.variant_measure = [Measure(value, ip_constants.NCIT_NOT_APPLICABLE) for value in self._optical_densities]
        return ods_template, ods_variable

    def _encode_replicates_using_sbol(self):
        replicate_template = Feature(identity=ip_constants.SD2E_LINK + '#replicate_template',
                                 type_uri=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        replicate_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        replicate_variable.variable = replicate_template
        replicate_variable.variant_measure = [Measure(value, ip_constants.NCIT_NOT_APPLICABLE) for value in self._replicates]
        return replicate_template, replicate_variable

    def _encode_strains_using_sbol(self):
        strain_template = Feature(identity='strain_template', type_uri=ip_constants.NCIT_STRAIN_URI)
        strain_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        strain_variable.variable = strain_template
        strain_variable.variant = [strain.to_sbol() for strain in self._strains]

        return strain_template, strain_variable

    def _encode_timepoint_using_opil(self, opil_measurement):
        encoded_timepoints = []
        for timepoint in self._timepoints:
            timepoint.to_sbol()
        opil_measurement.time = encoded_timepoints

    def _encode_temperature_using_sbol(self):
        # sbol3 requires that a VariantMeasure must point to a VariableFeature with a templated Feature.
        # However, there is no need for creating a template Feature to encode temperature. To address this,
        # temperatures will be attached to a media Feature.
        temperature_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        temperature_variable.variable = [temperature.to_sbol() for temperature in self._temperatures]
        return temperature_variable

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

    def to_sbol_for_col_ids(self):
        col_id_template = Feature(identity=ip_constants.SD2E_LINK + '#col_ids_template',
                                  type_uri=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        col_id_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        col_id_variable.variable = col_id_template

        col_id_components = []
        for value in self._column_ids:
            col_id_component = Component(identity=ip_constants.SD2E_LINK + '#col_ids',
                                         component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            col_id_component.name = value
            col_id_components.append(col_id_component)

        col_id_variable.variant = col_id_components
        return col_id_template, col_id_variable

    def to_sbol_for_dna_reaction_concentration(self):
        dna_reaction_concentration_template = Feature(identity=ip_constants.SD2E_LINK + '#dna_reaction_concentration_template',
                                                      type_uri=sbol_constants.SBO_FUNCTIONAL_ENTITY)

        dna_reaction_concentration_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        dna_reaction_concentration_variable.variable = dna_reaction_concentration_template

        dna_reaction_concentration_components = []
        for value in self._dna_reaction_concentrations:
            lab_component = Component(identity=ip_constants.SD2E_LINK + '#dna_reaction_concentration',
                                      component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            lab_component.name = value
            dna_reaction_concentration_components.append(lab_component)

        dna_reaction_concentration_variable.variant = dna_reaction_concentration_components
        return dna_reaction_concentration_template, dna_reaction_concentration_variable

    def to_sbol_for_lab_ids(self):
        lab_id_template = Feature(identity=ip_constants.SD2E_LINK + '#lab_ids_template',
                                  type_uri=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        lab_id_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        lab_id_variable.variable = lab_id_template

        lab_id_components = []
        for value in self._lab_ids:
            lab_component = Component(identity=ip_constants.SD2E_LINK + '#lab_id',
                                      component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            lab_component.name = value
            lab_id_components.append(lab_component)

        lab_id_variable.variant = lab_id_components
        return lab_id_template, lab_id_variable

    def to_sbol_for_media(self):
        media_template = Feature(identity=ip_constants.SD2E_LINK + '#media_template',
                                 type_uri=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        media_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)

        media_variants = []
        media_variant_measures = []
        for media in self._medias:
            media_variants.append(media.to_sbol())
            if media.get_timepoint() is not None:
                media_variant_measure = media.get_timepoint().to_sbol()
                media_variant_measures.append(media_variant_measure)

        media_variable.variable = media_template
        media_variable.variant = media_variants
        media_variable.variant_measure = media_variant_measure
        return media_template, media_variable

    def to_sbol_for_number_of_negative_controls(self):
        num_neg_control_template = Feature(identity=ip_constants.SD2E_LINK + '#num_neg_controls_template',
                                  type_uri=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        num_neg_control_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        num_neg_control_variable.variable = num_neg_control_template

        num_neg_control_components = []
        for value in self._num_neg_controls:
            num_neg_control_component = Component(identity=ip_constants.SD2E_LINK + '#num_neg_controls',
                                      component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            num_neg_control_component.name = str(value)
            num_neg_control_components.append(num_neg_control_component)

        num_neg_control_variable.variant = num_neg_control_components
        return num_neg_control_template, num_neg_control_variable

    def to_sbol_for_reagent(self):
        reagent_template = Feature(identity=ip_constants.SD2E_LINK + '#reagent_template',
                                   type_uri=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        reagent_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)

        reagent_variants = []
        reagent_variant_measures = []

        for reagent in self._reagents:
            reagent_variants.append(reagent.to_sbol())
            if reagent.get_timepoint() is not None:
                reagent_variant_measure = reagent.get_timepoint().to_sbol()
                reagent_variant_measures.append(reagent_variant_measure)

        reagent_variable.variable = reagent_template
        reagent_variable.variant = reagent_variants
        reagent_variable.variant_measure = reagent_variant_measures
        return reagent_template, reagent_variable

    def to_sbol_for_use_rna_inhibitor(self):
        use_rna_inhib_template = Feature(identity=ip_constants.SD2E_LINK + '#use_rna_inhibitor_template',
                                  type_uri=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        use_rna_inhib_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        use_rna_inhib_variable.variable = use_rna_inhib_template

        use_rna_inhib_components = []
        for value in self._rna_inhibitor_reaction_flags:
            use_rna_inhib_component = Component(identity=ip_constants.SD2E_LINK + '#use_rna_inhibitor',
                                      component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            use_rna_inhib_component.name = str(value)
            use_rna_inhib_components.append(use_rna_inhib_component)

        use_rna_inhib_variable.variant = use_rna_inhib_components
        return use_rna_inhib_template, use_rna_inhib_variable

    def to_sbol_for_row_ids(self):
        row_id_template = Feature(identity=ip_constants.SD2E_LINK + '#row_ids_template',
                                  type_uri=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        row_id_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        row_id_variable.variable = row_id_template

        row_id_components = []
        for value in self._row_ids:
            row_id_component = Component(identity=ip_constants.SD2E_LINK + '#row_ids',
                                         component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            row_id_component.name = str(value)
            row_id_components.append(row_id_component)

        row_id_variable.variant = row_id_components
        return row_id_template, row_id_variable

    def to_sbol_for_template_dna(self):
        template_dna_template = Feature(identity=ip_constants.SD2E_LINK + '#template_dna_template',
                                        type_uri=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        template_dna_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        template_dna_variable.variable = template_dna_template

        template_dna_components = []
        for value in self._template_dna_values:
            template_dna_component = Component(identity=ip_constants.SD2E_LINK + '#template_dna',
                                         component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            template_dna_component.name = value
            template_dna_components.append(template_dna_component)

        template_dna_variable.variant = template_dna_components
        return template_dna_template, template_dna_variable

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

    def to_sbol(self):
        media_component = Component(identity=ip_constants.SD2E_LINK + '#' + self._media_name.get_name(),
                                      component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        media_component.name = self._media_name.get_name()
        media_sub_component = SubComponent(self._media_name.get_link())
        media_component.features = [media_sub_component.identity]

        return media_component

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

    def to_sbol(self):
        content_component = Component(identity=ip_constants.SD2E_LINK + '#reagent' + self._reagent_name.get_name(),
                                      component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        content_component.name = self._reagent_name.get_name()
        content_sub_component = SubComponent(self._reagent_name.get_link())
        content_component.features = [content_sub_component.identity]

        return content_component

    def to_structure_request(self):
        reagent = {dc_constants.NAME: self._reagent_name.to_structure_request(),
                   dc_constants.VALUE: str(self._value),
                   dc_constants.UNIT: self._unit}
        if self._timepoint:
            reagent[dc_constants.TIMEPOINT] = self._timepoint.to_structure_request()

        return reagent



