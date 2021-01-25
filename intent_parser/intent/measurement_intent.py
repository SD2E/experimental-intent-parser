from intent_parser.intent.measure_property_intent import TemperatureIntent, TimepointIntent
from sbol3 import CombinatorialDerivation, Component, LocalSubComponent, TextProperty
from sbol3 import Measure, VariableFeature
from intent_parser.intent.control_intent import ControlIntent
from intent_parser.intent.strain_intent import StrainIntent
from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.utils.id_provider import IdProvider
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import logging
import opil
import sbol3.constants as sbol_constants

class MeasurementIntent(object):

    logger = logging.getLogger('MeasurementIntent')

    def __init__(self):
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
        self._id_provider = IdProvider()

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

        media_templates = []
        for content in self._contents.get_contents():
            media_template, media_variables = content.to_sbol_for_media()
            content_templates, content_variables = content.to_sbol()
            all_sample_templates.extend(content_templates)
            all_sample_variables.extend(content_variables)

            media_templates.append(media_template)

        if len(self._strains) > 0:
            strain_template, strain_variable = self._encode_strains_using_sbol()
            all_sample_templates.append(strain_template)
            all_sample_variables.append(strain_variable)

        if len(self._temperatures) > 0:
            if len(media_templates) > 1:
                self.logger.warning('more than one media detected. Last media is used to assign measurement temperature variants.')
            temperature_variable = self._encode_temperature_using_sbol()
            temperature_variable.variable = media_templates[-1]

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
            ods_template, ods_variable = self._encode_optical_densities_using_sbol()
            all_sample_templates.append(ods_template)
            all_sample_variables.append(ods_variable)

        sample_template = Component(identity=self._id_provider.get_unique_sd2_id(),
                                    component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        sample_template.name = 'measurement template'
        if len(all_sample_templates) == 0:
            raise IntentParserException('measurement template is empty')
        sample_template.features = all_sample_templates

        sample_combinations = CombinatorialDerivation(identity=self._id_provider.get_unique_sd2_id(),
                                                      template=sample_template)
        sample_combinations.name = 'measurement combinatorial derivation'
        if len(all_sample_variables) == 0:
            raise IntentParserException('measurement variables is empty')
        sample_combinations.variable_components = all_sample_variables

        return sample_combinations

    def to_opil(self):
        opil_measurement = opil.Measurement('measurement')
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
        batch_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                           types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        batch_template.name = ip_constants.HEADER_BATCH_VALUE

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
        control_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                             types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        control_template.name = ip_constants.HEADER_CONTROL_TYPE_VALUE

        control_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        control_variable.variable = control_template
        control_variable.variant_derivation = [control.to_sbol() for control in self._controls]
        return control_template, control_variable

    def _encode_optical_densities_using_sbol(self):
        ods_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                         types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        ods_template.name = ip_constants.HEADER_ODS_VALUE

        ods_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        ods_variable.variable = ods_template
        ods_variable.variant_measure = [Measure(value, ip_constants.NCIT_NOT_APPLICABLE) for value in self._optical_densities]
        return ods_template, ods_variable

    def _encode_replicates_using_sbol(self):
        replicate_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                               types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        replicate_template.name = ip_constants.HEADER_REPLICATE_VALUE

        replicate_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        replicate_variable.variable = replicate_template
        replicate_variable.variant_measure = [Measure(value, ip_constants.NCIT_NOT_APPLICABLE) for value in self._replicates]
        return replicate_template, replicate_variable

    def _encode_strains_using_sbol(self):
        strain_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                            types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        strain_template.name = ip_constants.HEADER_STRAINS_VALUE
        strain_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        strain_variable.variable = strain_template
        strain_variable.variant = [strain.to_sbol() for strain in self._strains]

        return strain_template, strain_variable

    def _encode_timepoint_using_opil(self, opil_measurement):
        encoded_timepoints = []
        for timepoint in self._timepoints:
            encoded_timepoints.append(timepoint.to_sbol())
        # TODO: bug in opil. opil limits one Measure assignment to a measurement time.
        # Update this line of code to opil_measurement.time = encoded_timepoints when this issue is resolved.
        opil_measurement.time = encoded_timepoints[0]

    def _encode_temperature_using_sbol(self):
        # sbol3 requires that a VariantMeasure must point to a VariableFeature with a templated Feature.
        # However, there is no need for creating a template Feature to encode temperature. To address this,
        # temperatures will be attached to a media Feature.
        temperature_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        temperature_variable.name = 'temperature variants'
        temperature_variable.variant_measure = [temperature.to_sbol() for temperature in self._temperatures]
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
        self._id_provider = IdProvider()

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

    def to_sbol(self):
        all_templates = []
        all_variables = []
        if len(self._medias) > 0:
            media_template, media_variables = self.to_sbol_for_media()
            all_templates.append(media_template)
            all_variables.append(media_variables)
        if len(self._reagents) > 0:
            reagent_templates, reagent_variables = self.to_sbol_for_reagent()
            all_templates.append(reagent_templates)
            all_variables.append(reagent_variables)
        if len(self._column_ids) > 0:
            col_id_template, col_id_variable = self.to_sbol_for_col_ids()
            all_templates.append(col_id_template)
            all_variables.append(col_id_variable)
        if len(self._dna_reaction_concentrations) > 0:
            dna_reaction_concentration_template, dna_reaction_concentration_variable = self.to_sbol_for_dna_reaction_concentration()
            all_templates.append(dna_reaction_concentration_template)
            all_variables.append(dna_reaction_concentration_variable)
        if len(self._lab_ids) > 0:
            lab_id_template, lab_id_variable = self.to_sbol_for_lab_ids()
            all_templates.append(lab_id_template)
            all_variables.append(lab_id_variable)
        if len(self._num_neg_controls) > 0:
            num_neg_control_template, num_neg_control_variable = self.to_sbol_for_number_of_negative_controls()
            all_templates.append(num_neg_control_template)
            all_variables.append(num_neg_control_variable)
        if len(self._rna_inhibitor_reaction_flags) > 0:
            use_rna_inhib_template, use_rna_inhib_variable = self.to_sbol_for_use_rna_inhibitor()
            all_templates.append(use_rna_inhib_template)
            all_variables.append(use_rna_inhib_variable)
        if len(self._row_ids) > 0:
            row_id_template, row_id_variable = self.to_sbol_for_row_ids()
            all_templates.append(row_id_template)
            all_variables.append(row_id_variable)
        if len(self._template_dna_values) > 0:
            template_dna_template, template_dna_variable = self.to_sbol_for_template_dna()
            all_templates.append(template_dna_template)
            all_variables.append(template_dna_variable)
        return all_templates, all_variables

    def to_sbol_for_col_ids(self):
        col_id_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                            types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        col_id_template.name = ip_constants.HEADER_COLUMN_ID_VALUE

        col_id_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        col_id_variable.variable = col_id_template

        col_id_components = []
        for value in self._column_ids:
            col_id_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                         component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            col_id_component.name = str(value.get_value())
            col_id_components.append(col_id_component)

        col_id_variable.variant = col_id_components
        return col_id_template, col_id_variable

    def to_sbol_for_dna_reaction_concentration(self):
        dna_reaction_concentration_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                                                types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        dna_reaction_concentration_template.name = ip_constants.HEADER_DNA_REACTION_CONCENTRATION_VALUE

        dna_reaction_concentration_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        dna_reaction_concentration_variable.variable = dna_reaction_concentration_template

        dna_reaction_concentration_components = []
        for value in self._dna_reaction_concentrations:
            lab_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                      component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            lab_component.name = str(value.get_value())
            dna_reaction_concentration_components.append(lab_component)

        dna_reaction_concentration_variable.variant = dna_reaction_concentration_components
        return dna_reaction_concentration_template, dna_reaction_concentration_variable

    def to_sbol_for_lab_ids(self):
        lab_id_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                            types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        lab_id_template.name = ip_constants.HEADER_LAB_ID_VALUE
        lab_id_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        lab_id_variable.variable = lab_id_template

        lab_id_components = []
        for value in self._lab_ids:
            lab_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                      component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            lab_component.name = value.get_value()
            lab_id_components.append(lab_component)

        lab_id_variable.variant = lab_id_components
        return lab_id_template, lab_id_variable

    def to_sbol_for_media(self):
        media_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                           types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        media_template.name = 'media template'
        media_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)

        media_variants = []
        media_variant_measures = []
        for media in self._medias:
            media_variants.append(media.to_sbol())
            if media.get_timepoint() is not None:
                media_variant_measure = media.get_timepoint().to_sbol()
                media_variant_measures.append(media_variant_measure)

        media_variable.variable = media_template
        if len(media_variants) == 0:
            raise IntentParserException('no media values generated for sbol.')
        media_variable.variant = media_variants

        if len(media_variant_measures) > 0:
            media_variable.variant_measure = media_variant_measures
        return media_template, media_variable

    def to_sbol_for_number_of_negative_controls(self):
        num_neg_control_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                                     types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        num_neg_control_template.name = ip_constants.HEADER_NUMBER_OF_NEGATIVE_CONTROLS_VALUE

        num_neg_control_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        num_neg_control_variable.variable = num_neg_control_template

        num_neg_control_components = []
        for value in self._num_neg_controls:
            num_neg_control_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                                  component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            num_neg_control_component.name = str(value.get_value())
            num_neg_control_components.append(num_neg_control_component)

        num_neg_control_variable.variant = num_neg_control_components
        return num_neg_control_template, num_neg_control_variable

    def to_sbol_for_reagent(self):
        reagent_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                             types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        reagent_template.name = 'reagent template'
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
        use_rna_inhib_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                                   types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        use_rna_inhib_template.name = ip_constants.HEADER_USE_RNA_INHIBITOR_IN_REACTION_VALUE

        use_rna_inhib_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        use_rna_inhib_variable.variable = use_rna_inhib_template

        use_rna_inhib_components = []
        for value in self._rna_inhibitor_reaction_flags:
            use_rna_inhib_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                                component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            use_rna_inhib_component.name = str(value.get_value())
            use_rna_inhib_components.append(use_rna_inhib_component)

        use_rna_inhib_variable.variant = use_rna_inhib_components
        return use_rna_inhib_template, use_rna_inhib_variable

    def to_sbol_for_row_ids(self):
        row_id_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                            types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        row_id_template.name = ip_constants.HEADER_ROW_ID_VALUE
        row_id_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        row_id_variable.variable = row_id_template

        row_id_components = []
        for value in self._row_ids:
            row_id_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                         component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            row_id_component.name = str(value.get_value())
            row_id_components.append(row_id_component)

        row_id_variable.variant = row_id_components
        return row_id_template, row_id_variable

    def to_sbol_for_template_dna(self):
        template_dna_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                                  types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        template_dna_template.name = ip_constants.HEADER_TEMPLATE_DNA_VALUE

        template_dna_variable = VariableFeature(cardinality=sbol_constants.SBOL_ONE)
        template_dna_variable.variable = template_dna_template

        template_dna_components = []
        for value in self._template_dna_values:
            template_dna_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                               component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            template_dna_component.name = value.get_value()
            template_dna_components.append(template_dna_component)

        template_dna_variable.variant = template_dna_components
        return template_dna_template, template_dna_variable

