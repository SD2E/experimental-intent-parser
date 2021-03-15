from intent_parser.intent.measure_property_intent import TemperatureIntent, TimepointIntent
from intent_parser.intent.control_intent import ControlIntent
from intent_parser.intent.strain_intent import StrainIntent
from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.utils.id_provider import IdProvider
from math import inf
from sbol3 import CombinatorialDerivation, Component, LocalSubComponent, TextProperty
from sbol3 import Measure, VariableFeature
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import logging
import opil
import sbol3.constants as sbol_constants
import tyto

class MeasurementIntent(object):

    logger = logging.getLogger('MeasurementIntent')

    def __init__(self):
        self.intent = {}
        self._measurement_type = None
        self._file_types = []
        self._batches = []
        self._contents = MeasurementContent()
        self._controls = []
        self._optical_densities = []
        self._replicates = []
        self._strains = []
        self._temperatures = []
        self._timepoints = []
        self._id_provider = IdProvider()

    def add_batch(self, batch: int):
        self._batches.append(batch)

    def add_content(self, content):
        self._contents.add_content_intent(content)

    def add_control(self, control: ControlIntent):
        self._controls.append(control)

    def add_file_type(self, file_type: str):
        self._file_types.append(file_type)

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
        return self._file_types

    def get_measurement_type(self) -> str:
        return self._measurement_type

    def is_empty(self):
        return (self._measurement_type is None and
                len(self._file_types) == 0 and
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

    def size_of_batches(self):
        return len(self._batches)

    def contents_is_empty(self):
        return self._contents.is_empty()

    def size_of_controls(self):
        return len(self._controls)

    def size_of_optical_density(self):
        return len(self._optical_densities)

    def size_of_strains(self):
        return len(self._strains)

    def size_of_temperatures(self):
        return len(self._temperatures)

    def to_opil(self):
        opil_measurement = opil.Measurement(self._id_provider.get_unique_sd2_id())
        opil_measurement.name = 'measurement'
        if self._measurement_type is None:
            raise IntentParserException("Exporting opil must have a measurement-type but none is set.")

        # convert required fields
        measurement_type = self._encode_measurement_type_using_opil(opil_measurement)

        # convert optional fields
        if len(self._file_types) > 0:
            self._encode_file_type_using_opil(opil_measurement)
        if len(self._timepoints) > 0:
            self._encode_timepoint_using_opil(opil_measurement)
        if len(self._controls) > 0:
            for control_index in range(len(self._controls)):
                control = self._controls[control_index]
                control.to_opil(opil_measurement)
                # TODO: opil does not allow more than one custom annotation assign to an opil_measurement.
                # temporary assign one control to a measurement.
                break

        return opil_measurement, measurement_type

    def to_structured_request(self):
        if self._measurement_type is None:
            raise IntentParserException("A structured request must have a measurement-type but none is set.")
        if len(self._file_types) == 0:
            raise IntentParserException("A structured request must have a file-type but file-type is empty.")

        structure_request = {dc_constants.MEASUREMENT_TYPE: self._measurement_type,
                             dc_constants.FILE_TYPE: self._file_types}

        if len(self._replicates) > 0:
            structure_request[dc_constants.REPLICATES] = self._replicates
        if self._strains:
            structure_request[dc_constants.STRAINS] = [strain.to_structured_request() for strain in self._strains]
        if len(self._optical_densities) > 0:
            structure_request[dc_constants.ODS] = self._optical_densities
        if len(self._temperatures) > 0:
            structure_request[dc_constants.TEMPERATURES] = [temperature.to_structured_request() for temperature in self._temperatures]
        if len(self._timepoints) > 0:
            structure_request[dc_constants.TIMEPOINTS] = [timepoint.to_structured_request() for timepoint in self._timepoints]
        if len(self._batches) > 0:
            structure_request[dc_constants.BATCH] = self._batches
        if len(self._controls) > 0:
            structure_request[dc_constants.CONTROLS] = [control.to_structured_request() for control in self._controls]
        if not self._contents.is_empty():
            structure_request.update(self._contents.to_structured_request())

        return structure_request

    def batch_values_to_sbol_variable_feature(self, batch_template):
        batch_variable = VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                         cardinality=sbol_constants.SBOL_ONE)
        batch_variable.variable = batch_template
        batch_variable.variant_measure = [Measure(value, tyto.OM.number) for value in self._batches]
        return batch_variable

    def _encode_file_type_using_opil(self, opil_measurement):
        opil_measurement.file_types = TextProperty(opil_measurement,
                                                  '%s#file_type' % ip_constants.SD2E_NAMESPACE,
                                                   0,
                                                   inf)
        opil_measurement.file_types = self._file_types

    def _encode_measurement_type_using_opil(self, opil_measurement):
        measurement_type = opil.MeasurementType(self._id_provider.get_unique_sd2_id())
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
        return measurement_type

    def control_to_sbol_variable_feature(self, sbol_document, control_template):
        control_variable = VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                           cardinality=sbol_constants.SBOL_ONE)
        control_variable.variable = control_template
        # todo: finish encoding control to sbol combinatorial derivations
        control_variable.variant_derivation = [control.to_sbol_combinatorial_derivation(sbol_document) for control in self._controls]
        return control_variable

    def optical_density_values_to_sbol_variable_feature(self, ods_template):
        ods_variable = VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                       cardinality=sbol_constants.SBOL_ONE)
        ods_variable.variable = ods_template
        ods_variable.variant_measure = [Measure(value, tyto.OM.number) for value in self._optical_densities]
        return ods_variable

    def replicate_values_to_opil_samplesets(self, replicate_template):
        replicate_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                               types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        replicate_template.name = ip_constants.HEADER_REPLICATE_VALUE
        sample_sets = []
        for replicate_value in self._replicates:
            sample_set = opil.SampleSet(identity=self._id_provider.get_unique_sd2_id(),
                                        template=replicate_template)
            sample_set.replicates = [replicate_value]
            sample_sets.append(sample_set)
        return sample_sets

    def strain_values_to_sbol_variable_feature(self, sbol_document, strain_template):
        strain_variable = VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                          cardinality=sbol_constants.SBOL_ONE)
        strain_variable.variable = strain_template
        strain_variable.variant = [strain.to_sbol_component(sbol_document) for strain in self._strains]
        return strain_variable

    def _encode_timepoint_using_opil(self, opil_measurement):
        encoded_timepoints = []
        for timepoint in self._timepoints:
            encoded_timepoints.append(timepoint.to_opil())
        opil_measurement.time = encoded_timepoints

    def temperature_values_to_sbol_variable_feature(self, media_template):
        # sbol3 does not have an object that can directly represent temperatures.
        # A suggestion was to use CombinatorialDerivations for encoding this information.
        # One downside to this suggestion is sbol3 requires that a VariantMeasure must
        # point to a VariableFeature with a templated Feature. However, a temperature
        # does not need an SBOL template to define its value so creating a template for
        # temperature is not the ideal way of representing this information.
        # For now, temperatures will be attached to an sbol3 media Feature object until
        # a new object is introduced to best encode this information.
        temperature_variable = VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                               cardinality=sbol_constants.SBOL_ONE)
        temperature_variable.variable = media_template
        temperature_variable.variant_measure = [temperature.to_opil() for temperature in self._temperatures]
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

    def to_structured_request(self):
        return {dc_constants.CONTENTS: content.to_structured_request() for content in self._contents}

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
        self._id_provider = IdProvider()

    def add_media(self, media):
        self._medias.append(media)

    def add_reagent(self, reagent):
        self._reagents.append(reagent)

    def get_media_size(self):
        return len(self._medias)

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

    def to_structured_request(self):
        structure_request = []
        if len(self._num_neg_controls) > 0:
            structure_request.append([num_neg_control.to_structured_request() for num_neg_control in self._num_neg_controls])
        if len(self._rna_inhibitor_reaction_flags) > 0:
            structure_request.append([rna_inhibitor_reaction.to_structured_request() for rna_inhibitor_reaction in self._rna_inhibitor_reaction_flags])
        if len(self._dna_reaction_concentrations) > 0:
            structure_request.append([dna_reaction_concentration.to_structured_request() for dna_reaction_concentration in self._dna_reaction_concentrations])
        if len(self._template_dna_values) > 0:
            structure_request.append([template_dna.to_structured_request() for template_dna in self._template_dna_values])
        if len(self._column_ids) > 0:
            structure_request.append([col_id.to_structured_request() for col_id in self._column_ids])
        if len(self._row_ids) > 0:
            structure_request.append([row_id.to_structured_request() for row_id in self._row_ids])
        if len(self._lab_ids) > 0:
            structure_request.append([lab_id.to_structured_request() for lab_id in self._lab_ids])
        if len(self._reagents) > 0:
            for reagent in self._reagents:
                structure_request.append(reagent.to_structured_request())
        if len(self._medias) > 0:
            for media in self._medias:
                structure_request.append(media.to_structured_request())

        return structure_request

    def size_of_column_id(self):
        return len(self._column_ids)

    def size_of_dna_reaction_concentrations(self):
        return len(self._dna_reaction_concentrations)

    def size_of_lab_ids(self):
        return len(self._lab_ids)

    def size_of_num_of_neg_controls(self):
        return len(self._num_neg_controls)

    def size_of_rna_inhibitor_flags(self):
        return len(self._rna_inhibitor_reaction_flags)

    def size_of_row_ids(self):
        return len(self._row_ids)

    def size_of_template_dna_values(self):
        return len(self._template_dna_values)

    def size_of_reagents(self):
        return len(self._reagents)

    def size_of_medias(self):
        return len(self._medias)

    def col_id_values_to_sbol_variable_feature(self, sbol_document, col_id_template):
        col_id_variable = VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                          cardinality=sbol_constants.SBOL_ONE)
        col_id_variable.variable = col_id_template

        col_id_components = []
        for value in self._column_ids:
            col_id_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                         component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            col_id_component.name = str(value.get_value())
            col_id_components.append(col_id_component)
            sbol_document.add(col_id_component)
        col_id_variable.variant = col_id_components
        return col_id_variable

    def dna_reaction_concentration_values_to_sbol_variable_feature(self, sbol_document, dna_reaction_concentration_template):
        dna_reaction_concentration_variable = VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                                              cardinality=sbol_constants.SBOL_ONE)
        dna_reaction_concentration_variable.variable = dna_reaction_concentration_template

        dna_reaction_concentration_components = []
        for value in self._dna_reaction_concentrations:
            lab_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                      component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            lab_component.name = str(value.get_value())
            dna_reaction_concentration_components.append(lab_component)
            sbol_document.add(lab_component)
        dna_reaction_concentration_variable.variant = dna_reaction_concentration_components
        return dna_reaction_concentration_variable

    def lab_id_values_to_sbol_variable_feature(self, sbol_document, lab_id_template):
        lab_id_variable = VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                          cardinality=sbol_constants.SBOL_ONE)
        lab_id_variable.variable = lab_id_template

        lab_id_components = []
        for value in self._lab_ids:
            lab_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                      component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            lab_component.name = value.get_value()
            lab_id_components.append(lab_component)
            sbol_document.add(lab_component)
        lab_id_variable.variant = lab_id_components
        return lab_id_variable

    def number_of_negative_control_values_to_sbol_variable_feature(self, sbol_document, num_neg_control_template):
        num_neg_control_variable = VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                                   cardinality=sbol_constants.SBOL_ONE)
        num_neg_control_variable.variable = num_neg_control_template

        num_neg_control_components = []
        for value in self._num_neg_controls:
            num_neg_control_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                                  component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            num_neg_control_component.name = str(value.get_value())
            num_neg_control_components.append(num_neg_control_component)
            sbol_document.add(num_neg_control_component)
        num_neg_control_variable.variant = num_neg_control_components
        return num_neg_control_variable

    def reagent_values_to_sbol(self, sbol_document):
        reagent_templates = []
        reagent_variables = []
        for reagent in self._reagents:
            reagent_template, reagent_variable, _ = reagent.to_sbol_combinatorial_derivation(sbol_document)
            reagent_templates.append(reagent_template)
            reagent_variables.append(reagent_variable)

        return reagent_templates, reagent_variables

    def use_rna_inhibitor_values_to_sbol_variable_feature(self, sbol_document, use_rna_inhib_template):
        use_rna_inhib_variable = VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                                 cardinality=sbol_constants.SBOL_ONE)
        use_rna_inhib_variable.variable = use_rna_inhib_template

        use_rna_inhib_components = []
        for value in self._rna_inhibitor_reaction_flags:
            use_rna_inhib_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                                component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            use_rna_inhib_component.name = str(value.get_value())
            use_rna_inhib_components.append(use_rna_inhib_component)
            sbol_document.add(use_rna_inhib_component)
        use_rna_inhib_variable.variant = use_rna_inhib_components
        return use_rna_inhib_variable

    def row_id_values_to_sbol_variable_feature(self, sbol_document, row_id_template):
        row_id_variable = VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                          cardinality=sbol_constants.SBOL_ONE)
        row_id_variable.variable = row_id_template

        row_id_components = []
        for value in self._row_ids:
            row_id_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                         component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            row_id_component.name = str(value.get_value())
            row_id_components.append(row_id_component)
            sbol_document.add(row_id_component)
        row_id_variable.variant = row_id_components
        return row_id_variable

    def template_dna_values_to_sbol_variable_feature(self, sbol_document, template_dna_template):
        template_dna_variable = VariableFeature(identity=self._id_provider.get_unique_sd2_id(),
                                                cardinality=sbol_constants.SBOL_ONE)
        template_dna_variable.variable = template_dna_template

        template_dna_components = []
        for value in self._template_dna_values:
            template_dna_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                               component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            template_dna_component.name = value.get_name()
            template_dna_components.append(template_dna_component)
            sbol_document.add(template_dna_components)
        template_dna_variable.variant = template_dna_components
        return template_dna_variable

