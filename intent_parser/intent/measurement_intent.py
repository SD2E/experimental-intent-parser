from intent_parser.intent.measure_property_intent import TemperatureIntent, TimepointIntent
from intent_parser.intent.control_intent import ControlIntent
from intent_parser.intent.strain_intent import StrainIntent
from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.utils.id_provider import IdProvider
from math import inf
from sbol3 import Component, Measure, TextProperty
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

    def has_measurement_type(self):
        return True if self._measurement_type else False

    def get_contents(self):
        return self._contents

    def get_controls(self):
        return self._controls

    def get_file_types(self):
        return self._file_types

    def get_measurement_type(self) -> str:
        return self._measurement_type

    def get_replicates(self):
        return self._replicates

    def get_strains(self):
        return self._strains

    def get_temperatures(self):
        return self._temperatures

    def get_timepoints(self):
        return self._timepoints

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

    def size_of_file_types(self):
        return len(self._file_types)

    def size_of_optical_density(self):
        return len(self._optical_densities)

    def size_of_replicates(self):
        return len(self._replicates)

    def size_of_strains(self):
        return len(self._strains)

    def size_of_temperatures(self):
        return len(self._temperatures)

    def size_of_timepoints(self):
        return len(self._timepoints)

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

    def batch_values_to_opil_measures(self):
        return [Measure(value, tyto.OM.number) for value in self._batches]

    def file_types_to_opil_measurement_annotation(self, opil_measurement):
        opil_measurement.file_types = TextProperty(opil_measurement,
                                                  '%s#file_type' % ip_constants.SD2E_NAMESPACE,
                                                   0,
                                                   inf)
        opil_measurement.file_types = self._file_types

    def measurement_type_to_opil_measurement_type(self):
        measurement_type = opil.MeasurementType()
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
        return measurement_type

    def optical_density_values_to_opil_measures(self):
        return [Measure(value, tyto.OM.number) for value in self._optical_densities]

    def strain_values_to_opil_components(self):
        return [strain.to_opil_component() for strain in self._strains]

    def timepoint_values_to_opil_measures(self):
        encoded_timepoints = []
        for timepoint in self._timepoints:
            encoded_timepoints.append(timepoint.to_opil_measure())
        return encoded_timepoints

    def temperature_values_to_opil_measure(self):
        return [temperature.to_opil_measure() for temperature in self._temperatures]

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

    def get_medias(self):
        return self._medias

    def get_reagents(self):
        return self._reagents

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

    def col_id_values_to_opil_components(self):
        col_id_components = []
        for value in self._column_ids:
            col_id_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                         types=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            col_id_component.name = str(value.get_value())
            col_id_components.append(col_id_component)
        return col_id_components

    def dna_reaction_concentration_values_to_opil_components(self):
        dna_reaction_concentration_components = []
        for value in self._dna_reaction_concentrations:
            lab_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                      types=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            lab_component.name = str(value.get_value())
            dna_reaction_concentration_components.append(lab_component)
        return dna_reaction_concentration_components

    def lab_id_values_to_opil_components(self):
        lab_id_components = []
        for value in self._lab_ids:
            lab_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                      types=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            lab_component.name = str(value.get_value())
            lab_id_components.append(lab_component)
        return lab_id_components

    def number_of_negative_control_values_to_opil_components(self):
        num_neg_control_components = []
        for value in self._num_neg_controls:
            num_neg_control_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                                  types=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            num_neg_control_component.name = str(value.get_value())
            num_neg_control_components.append(num_neg_control_component)
        return num_neg_control_components

    def use_rna_inhibitor_values_to_opil_components(self):
        use_rna_inhib_components = []
        for value in self._rna_inhibitor_reaction_flags:
            use_rna_inhib_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                                types=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            use_rna_inhib_component.name = str(value.get_value())
            use_rna_inhib_components.append(use_rna_inhib_component)
        return use_rna_inhib_components

    def row_id_values_to_opil_components(self):
        row_id_components = []
        for value in self._row_ids:
            row_id_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                         types=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            row_id_component.name = str(value.get_value())
            row_id_components.append(row_id_component)
        return row_id_components

    def template_dna_values_to_opil_components(self):
        template_dna_components = []
        for value in self._template_dna_values:
            template_dna_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                               types=sbol_constants.SBO_FUNCTIONAL_ENTITY)
            template_dna_component.name = value.get_name()
            template_dna_components.append(template_dna_component)
        return template_dna_components

