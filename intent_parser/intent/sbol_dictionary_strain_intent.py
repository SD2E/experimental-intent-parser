from intent_parser.utils.id_provider import IdProvider


class SBOLDictionaryStrainIntent(object):
    """
    Intent Parser's representation of sbol dictionary strains.
    """

    def __init__(self, strain_reference_link: str, lab_id: str, strain_common_name: str, lab_strain_names=[]):
        self._strain_reference_link = strain_reference_link
        self._lab_id = lab_id
        self._strain_common_name = strain_common_name
        self._lab_strain_names = lab_strain_names
        self._id_provider = IdProvider()

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
