import intent_parser.constants.sd2_datacatalog_constants as dc_constants

"""
Intent Parser's representation of strains.
"""
class StrainIntent(object):

    def __init__(self, strain_reference_link, lab_id, strain_common_name, lab_strain_names=[]):
        self._strain_reference_link = strain_reference_link
        self._lab_id = lab_id
        self._selected_strain = None
        self._strain_common_name = strain_common_name
        self._lab_strain_names = lab_strain_names

    def get_strain_common_name(self):
        return self._strain_common_name

    def get_lab_id(self):
        return self._lab_id

    def get_lab_strain_names(self):
        return self._lab_strain_names

    def get_strain_reference_link(self):
        return self._strain_reference_link

    def has_lab_strain_name(self, lab_strain_name):
        return lab_strain_name in self._lab_strain_names

    def set_selected_strain(self, strain_name):
        self._selected_strain = strain_name

    def to_structure_request(self):
        return {dc_constants.SBH_URI: self._strain_reference_link,
                dc_constants.LABEL: self._strain_common_name,
                dc_constants.LAB_ID: 'name.%s.%s' % (self._lab_id.lower(), self._selected_strain)}


