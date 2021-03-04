"""
Provides a list of functions for building opil objects.
"""
from intent_parser.intent.measure_property_intent import MeasuredUnit
from sbol3 import TextProperty
import intent_parser.utils.sbol3_utils as sbol3_utils
import opil

def create_custom_string_annotation(annotated_object, annotated_value):
    annotated_object.annotation_property = TextProperty(rdf_predicate, cardinality_lower_bound, cardinality_upper_bound)

def create_opil_boolean_parameter_field(field_id: str, field: str):
    parameter_field = opil.BooleanParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_boolean_parameter_value(value_id: str, value: bool):
    parameter_value = opil.BooleanValue(value_id)
    parameter_value.value = value
    return parameter_value

def create_opil_enumerated_parameter_field(field_id: str, field: str):
    parameter_field = opil.EnumeratedParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_enumerated_parameter_value(value_id: str, value: str):
    parameter_value = opil.EnumeratedValue(value_id)
    parameter_value.value = value
    return parameter_value

def create_opil_integer_parameter_field(field_id: str, field: str):
    parameter_field = opil.IntegerParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_integer_parameter_value(value_id: str, value: int):
    parameter_value = opil.IntegerValue(value_id)
    parameter_value.value = value
    return parameter_value

def create_opil_measurement_parameter_field(field_id: str, field: str):
    parameter_field = opil.MeasureParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_measurement_parameter_value(value_id: str, value: float, unit: str):
    parameter_value = opil.MeasureValue(value_id)
    measure = MeasuredUnit(value, unit)
    parameter_value.has_measure = measure.to_opil()
    return parameter_value

def create_opil_string_parameter_field(field_id: str, field: str):
    parameter_field = opil.StringParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_string_parameter_value(value_id: str, value: str):
    parameter_value = opil.StringValue(value_id)
    parameter_value.value = value
    return parameter_value

def create_opil_uri_parameter_field(field_id: str, field: str):
    parameter_field = opil.URIParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_URI_parameter_value(value_id: str, value: str):
    parameter_value = opil.URIValue(value_id)
    parameter_value.value = value
    return parameter_value

def get_param_value_as_string(parameter_value):
    if type(parameter_value) is opil.opil_factory.BooleanValue:
        return str(parameter_value.value)
    elif type(parameter_value) is opil.opil_factory.EnumeratedValue:
        return str(parameter_value.value)
    elif type(parameter_value) is opil.opil_factory.IntegerValue:
        return str(parameter_value.value)
    elif type(parameter_value) is opil.opil_factory.MeasureValue:
        if parameter_value.has_measure:
            measure_number = float(parameter_value.has_measure.value)
            measure_unit = sbol3_utils.get_unit_name_from_uri(parameter_value.has_measure.unit)
            if measure_unit:
                return '%d %s' % (measure_number, measure_unit)
            return '%d' % measure_number
    elif type(parameter_value) is opil.opil_factory.StringValue:
        return parameter_value.value if parameter_value.value else ' '
    elif type(parameter_value) is opil.opil_factory.URIValue:
        return str(parameter_value.value)
    elif isinstance(parameter_value, str):
        return parameter_value

    return ''

def get_protocol_id_from_annotaton(protocol):
    namespace = 'http://strateos.com/'
    id_annotation = TextProperty(protocol, namespace + 'strateos_id', 0, 1)
    return id_annotation.property_owner.strateos_id

def get_protocol_interfaces_from_sbol_doc(sbol_doc) -> list:
    protocol_interfaces = []
    for obj in sbol_doc.objects:
        if type(obj) is opil.opil_factory.ProtocolInterface:
            protocol_interfaces.append(obj)
    return protocol_interfaces

def get_opil_experimental_requests(opil_doc):
    experimental_requests = []
    for opil_object in opil_doc.objects:
        if type(opil_object) is opil.oil_factory.ExperimentalRequest:
            experimental_requests.append(opil_object)
    return experimental_requests