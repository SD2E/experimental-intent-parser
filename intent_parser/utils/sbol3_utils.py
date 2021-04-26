from sbol3 import CombinatorialDerivation
import intent_parser.constants.intent_parser_constants as ip_constants


def get_combinatorial_derivations(sbol_doc):
    combinatorial_derivations = []
    for sbol_obj in sbol_doc.objects:
        if type(sbol_obj) == CombinatorialDerivation:
            combinatorial_derivations.append(sbol_obj)
    return combinatorial_derivations

def get_unit_name_from_timepoint_uri(unit_uri):
    for key, value in ip_constants.TIME_UNIT_MAP.items():
        if value == unit_uri:
            return key
    return None

def get_unit_name_from_fluid_uri(unit_uri):
    for key, value in ip_constants.FLUID_UNIT_MAP.items():
        if value == unit_uri:
            return key
    return None

def get_unit_name_from_temperature_uri(unit_uri):
    for key, value in ip_constants.TEMPERATURE_UNIT_MAP.items():
        if value == unit_uri:
            return key
    return None

def get_unit_name_from_uri(unit_uri: str):
    """
    Get unit name from an measurement unit uri.
    Args:
        unit_uri: unit uri
    Returns:
        a string representing the unit name of the given unit uri.
        An empty string is returned if no unit name is found for the given uri.
    """
    fluid_unit_name = get_unit_name_from_fluid_uri(unit_uri)
    if fluid_unit_name:
        return fluid_unit_name

    temperature_unit_name = get_unit_name_from_temperature_uri(unit_uri)
    if temperature_unit_name:
        return temperature_unit_name

    timepoint_unit_name = get_unit_name_from_timepoint_uri(unit_uri)
    if timepoint_unit_name:
        return timepoint_unit_name

    if unit_uri == ip_constants.OTU_NANOMETER:
        return 'nanometer'

    if unit_uri == ip_constants.OTU_HOUR:
        return 'hour'

    return None