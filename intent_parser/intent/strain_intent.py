from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.utils.id_provider import IdProvider
from sbol3 import Component, SubComponent
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import sbol3.constants as sbol_constants

"""
Intent Parser's representation of strains.
"""
class StrainIntent(object):

    def __init__(self, strain_reference_link: str, lab_id: str, strain_common_name: str, lab_strain_names=[]):
        self._strain_reference_link = strain_reference_link
        self._lab_id = lab_id
        self._selected_strain = None
        self._strain_common_name = strain_common_name
        self._lab_strain_names = lab_strain_names
        self._id_provider = IdProvider()

    def get_strain_common_name(self):
        return self._strain_common_name

    def get_lab_id(self):
        return self._lab_id

    def get_lab_strain_names(self):
        return self._lab_strain_names

    def get_selected_strain_name(self):
        return self._selected_strain

    def get_strain_reference_link(self):
        return self._strain_reference_link

    def has_lab_strain_name(self, lab_strain_name):
        return lab_strain_name in self._lab_strain_names

    def set_selected_strain(self, strain_name):
        self._selected_strain = strain_name

    def to_sbol(self, sbol_document):
        strain_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                     component_type=sbol_constants.SBO_DNA)
        if self._selected_strain is None:
            raise IntentParserException('no strain selected to encode to sbol')

        strain_component.name = self._selected_strain
        strain_sub_component = SubComponent(self._strain_reference_link)
        strain_component.features = [strain_sub_component]
        sbol_document.add(strain_component)
        return strain_component

    def to_structure_request(self):
        return {dc_constants.SBH_URI: self._strain_reference_link,
                dc_constants.LABEL: self._strain_common_name,
                dc_constants.LAB_ID: 'name.%s.%s' % (self._lab_id.lower(), self._selected_strain)}


