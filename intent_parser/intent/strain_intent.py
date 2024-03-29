from intent_parser.intent.measure_property_intent import NamedLink
from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.utils.id_provider import IdProvider
from sbol3 import Component, SubComponent
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import opil
import sbol3.constants as sbol_constants

class StrainIntent(object):
    """
    Intent Parser's data representation of a strain.
    """

    def __init__(self, strain: NamedLink):
        self._id_provider = IdProvider()
        self._lab_name = ''
        self._strain_name = strain
        self._strain_commmon_name = ''

    def get_name(self) -> NamedLink:
        return self._strain_name

    def set_strain_lab_name(self, lab_name):
        if self._lab_name:
            raise IntentParserException('conflict setting stran lab name: Current lab set to %s' % self._lab_name)
        self._lab_name = lab_name

    def set_strain_common_name(self, common_name):
        if self._strain_commmon_name:
            raise IntentParserException('conflict setting strain common name: '
                                        'Current common name set to %s' % self._strain_commmon_name)
        self._strain_commmon_name = common_name

    def to_opil_component(self):
        strain_component = Component(identity=self._id_provider.get_unique_sd2_id(),
                                     types=sbol_constants.SBO_DNA)
        strain_component.name = self._strain_name.get_name()

        if self._strain_name.get_link():
            strain_sub_component = SubComponent(self._strain_name.get_link())
            strain_component.features = [strain_sub_component]
        return strain_component

    def to_structured_request(self):
        return {dc_constants.SBH_URI: self._strain_name.get_link(),
                dc_constants.LABEL: self._strain_commmon_name,
                dc_constants.LAB_ID: 'name.%s.%s' % (self._lab_name.lower(), self._strain_name.get_name())}