from intent_parser.intent.measure_property_intent import ReagentIntent, MediaIntent
from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.table.measurement_table import MeasurementTable
from intent_parser.utils.id_provider import IdProvider
from sbol3 import CombinatorialDerivation, Component, SubComponent, TextProperty, LocalSubComponent
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.utils.opil_utils as opil_utils
import opil
import sbol3.constants as sbol_constants

class OpilDocumentTemplate(object):
    def __init__(self):
        self.opil_components = []
        self.opil_combinatorial_derivations = []
        self.opil_experimental_requests = []
        self.opil_protocol_interfaces = []

    def get_components(self):
        return self.opil_components

    def get_combinatorial_derivations(self):
        return self.opil_combinatorial_derivations

    def get_experimental_requests(self):
        return self.opil_experimental_requests

    def get_protocol_interfaces(self):
        return self.opil_protocol_interfaces

    def load_from_template(self, template: opil.Document):
        for top_level in template.objects:
            if type(top_level) == opil.Component:
                self.opil_components.append(top_level)
            elif type(top_level) == opil.CombinatorialDerivation:
                self.opil_combinatorial_derivations.append(top_level)
            elif type(top_level) == opil.ExperimentalRequest:
                self.opil_experimental_requests.append(top_level)
            elif type(top_level) == opil.ProtocolInterface:
                self.opil_protocol_interfaces.append(top_level)

class OpilComponentTemplate(object):
    def __init__(self):
        self.batch_template = None
        self.column_id_template = None
        self.control_template = None
        self.dna_reaction_concentration_template = None
        self.lab_id_template = None
        self.media_and_reagent_templates = []
        self.num_neg_control_template = None
        self.ods_template = None
        self.row_id_template = None
        self.strains_template = None
        self.template_dna_template = None
        self.use_rna_inhib_template = None

    def load_from_measurement_table(self, measurement_table: MeasurementTable):
        if measurement_table.has_batch():
            self.batch_template = ip_constants.HEADER_BATCH_VALUE
        if measurement_table.has_column_id():
            self.column_id_template = ip_constants.HEADER_COLUMN_ID_VALUE
        if measurement_table.has_control():
            self.control_template = ip_constants.HEADER_CONTROL_TYPE_VALUE
        if measurement_table.has_dna_reaction_concentration():
            self.dna_reaction_concentration_template = ip_constants.HEADER_DNA_REACTION_CONCENTRATION_VALUE
        if measurement_table.has_lab_id():
            self.lab_id_template = ip_constants.HEADER_LAB_ID_VALUE
        if measurement_table.has_medias_and_reagents():
            self.media_and_reagent_templates.extend(measurement_table.get_processed_reagents_and_medias())
        if measurement_table.has_number_of_negative_controls():
            self.num_neg_control_template = ip_constants.HEADER_NUMBER_OF_NEGATIVE_CONTROLS_VALUE
        if measurement_table.has_ods():
            self.ods_template = ip_constants.HEADER_ODS_VALUE
        if measurement_table.has_row_id():
            self.row_id_template = ip_constants.HEADER_ROW_ID_VALUE
        if measurement_table.has_rna_inhibitor():
            self.use_rna_inhib_template = ip_constants.HEADER_USE_RNA_INHIBITOR_IN_REACTION_VALUE
        if measurement_table.has_strains():
            self.strains_template = ip_constants.HEADER_STRAINS_VALUE
        if measurement_table.has_template_dna():
            self.template_dna_template = ip_constants.HEADER_TEMPLATE_DNA_VALUE


class ExperimentalRequest(object):
    """An experimental request is ..."""
    def __init__(self, lab_namespace, template: OpilDocumentTemplate, component_template: OpilComponentTemplate):
        self.opil_components = [component.copy() for component in template.get_components()]
        self.opil_combinatorial_derivations = [component.copy() for component in template.get_combinatorial_derivations()]
        self.opil_experimental_requests = [component.copy() for component in template.get_experimental_requests()]
        self.opil_protocol_interfaces = [component.copy() for component in template.get_protocol_interfaces()]
        self._lab_namespace = lab_namespace
        self._opil_component_template = component_template
        self._id_provider = IdProvider()

    def create_components_from_template(self):
        if self._opil_component_template.batch_template:
            batch_template = self._create_opil_local_subcomponent(self._opil_component_template.batch_template)
            self.opil_components.append(batch_template)
        if self._opil_component_template.column_id_template:
            col_id_template = self._create_opil_local_subcomponent(self._opil_component_template.column_id_template)
            self.opil_components.append(col_id_template)
        if self._opil_component_template.control_template:
            control_template = self._create_opil_local_subcomponent(self._opil_component_template.control_template)
            self.opil_components.append(control_template)
        if self._opil_component_template.dna_reaction_concentration_template:
            dna_reaction_concentration_template = self._create_opil_local_subcomponent(self._opil_component_template.dna_reaction_concentration_template)
            self.opil_components.append(dna_reaction_concentration_template)
        if self._opil_component_template.lab_id_template:
            lab_id_template = self._create_opil_local_subcomponent(self._opil_component_template.lab_id_template)
            self.opil_components.append(lab_id_template)
        if self._opil_component_template.num_neg_control_template:
            num_neg_control_template = self._create_opil_local_subcomponent(self._opil_component_template.num_neg_control_template)
            self.opil_components.append(num_neg_control_template)
        if self._opil_component_template.ods_template:
            ods_template = self._create_opil_local_subcomponent(self._opil_component_template.ods_template)
            self.opil_components.append(ods_template)
        if self._opil_component_template.row_id_template:
            row_id_template = self._create_opil_local_subcomponent(self._opil_component_template.row_id_template)
            self.opil_components.append(row_id_template)
        if self._opil_component_template.use_rna_inhib_template:
            use_rna_inhib_template = self._create_opil_local_subcomponent(self._opil_component_template.use_rna_inhib_template)
            self.opil_components.append(use_rna_inhib_template)
        if self._opil_component_template.template_dna_template:
            template_dna_template = self._create_opil_local_subcomponent(self._opil_component_template.template_dna_template)
            self.opil_components.append(template_dna_template)

        self.opil_components.append(self._get_or_create_strain_template())

    def _get_or_create_strain_template(self):
        strain = None
        for opil_component in self.opil_components:
            if ip_constants.NCIT_STRAIN_URI in opil_component.roles:
                if not strain:
                    strain = opil_component
                else:
                    raise IntentParserException('More than one strain found: %s, %s'
                                                % (opil_component.identity, strain.identity))
            elif 'strain' in opil_component.name.lower():
                if not strain:
                    strain = opil_component # todo: tell ben to fix to strains
                else:
                    raise IntentParserException('More than one strain found: %s, %s'
                                                % (opil_component.identity, strain.identity))
        if not strain:
            strain = self._create_opil_local_subcomponent(self._opil_component_template.strains_template)
        return strain

    def _get_or_create_reagent_and_media_templates(self):
        medias_and_reagents = {}
        for opil_component in self.opil_components:
            if ip_constants.NCIT_REAGENT_URI in opil_component.roles:
                medias_and_reagents[opil_component.name] = opil_component
            elif ip_constants.NCIT_MEDIA_URI in opil_component.roles:
                medias_and_reagents[opil_component.name] = opil_component
            elif ip_constants.NCIT_INDUCER_URI in opil_component.roles:
                medias_and_reagents[opil_component.name] = opil_component

        for ip_component in self._opil_component_template.media_and_reagent_templates:
            if isinstance(ip_component, ReagentIntent):
                reagent_name = ip_component.get_reagent_name()
                if reagent_name.get_name() not in medias_and_reagents:
                    reagent_component = self._create_reagent_template(ip_component)
                    medias_and_reagents[reagent_component.name] = reagent_component
            elif isinstance(ip_component, MediaIntent):
                media_name = ip_component.get_media_name()
                if media_name.get_name() not in medias_and_reagents:
                    media_component = self._create_media_template(ip_component)
                    medias_and_reagents[media_component.name] = media_component

    def get_component_template(self):
        return self._opil_component_template

    def _create_media_template(self, ip_media):
        media_name = ip_media.get_media_name()
        media_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                    component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        media_component.name = media_name.get_name()
        media_component.roles = [ip_constants.NCIT_MEDIA_URI]
        if media_name.get_link() is None:
            media_template = SubComponent(media_component)
            media_component.features = [media_template]
        else:
            media_template = SubComponent(media_name.get_link())
            media_component.features = [media_template]

        if ip_media.get_timepoint() is not None:
            media_timepoint_measure = ip_media.get_timepoint().to_opil()
            media_template.measures = [media_timepoint_measure]
        return media_component

    def _create_reagent_template(self, ip_reagent):
        reagent_name = ip_reagent.get_reagent_name()
        reagent_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                      component_type=sbol_constants.SBO_FUNCTIONAL_ENTITY)
        reagent_component.roles = [ip_constants.NCIT_REAGENT_URI]
        reagent_component.name = reagent_name.get_name()
        if reagent_name.get_link() is None:
            reagent_template = SubComponent(reagent_component)
            reagent_component.features = [reagent_template]
        else:
            reagent_template = SubComponent(reagent_name.get_link())
            reagent_component.features = [reagent_template]

        if ip_reagent.get_timepoint():
            reagent_timepoint_measure = ip_reagent.get_timepoint().to_opil()
            reagent_template.measures = [reagent_timepoint_measure]
        return reagent_component

    def get_or_add_experimental_request(self):
        if len(self.opil_experimental_requests) == 0:
            opil_experimental_request = opil.ExperimentalRequest(self._id_provider.get_unique_sd2_id())
            self.opil_experimental_requests.append(opil_experimental_request)
            return opil_experimental_request
        elif len(self.opil_experimental_requests) == 1:
            # IP can't get name of experimental request from a document so return
            # first instance of this object in this class.
            return self.opil_experimental_requests[0]
        else:
            raise IntentParserException('expecting 1 but got %d opil.ExperimentalRequest.' % len(self.opil_experimental_requests))

    def to_opil(self):
        opil_doc = opil.Document()
        for component in self.opil_components:
            opil_doc.add(component)
        for component in self.opil_combinatorial_derivations:
            opil_doc.add(component)
        for component in self.opil_experimental_requests:
            opil_doc.add(component)
        for component in self.opil_protocol_interfaces:
            opil_doc.add(component)
        return opil_doc

    def _create_opil_local_subcomponent(self, template_name):
        component_template = LocalSubComponent(identity=self._id_provider.get_unique_sd2_id(),
                                               types=[sbol_constants.SBO_FUNCTIONAL_ENTITY])
        component_template.name = template_name
        return component_template