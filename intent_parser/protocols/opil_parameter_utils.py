"""
Provides a list of functions for building opil objects.
"""
import opil
import sbol3

MEASUREMENT_UNITS = {
    'microliter': 'http://www.ontology-of-units-of-measure.org/resource/om-2/microlitre',
    'nanometer': 'http://www.ontology-of-units-of-measure.org/resource/om-2/nanometre',
    'hour': 'http://www.ontology-of-units-of-measure.org/resource/om-2/hour'
}

def clone_boolean_parameter_field(boolean_parameter):
    return create_opil_boolean_parameter_field(boolean_parameter.identity, boolean_parameter.name)

def create_opil_boolean_parameter_field(field_id: str, field: str):
    parameter_field = opil.BooleanParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_boolean_parameter_value(value_id: str, value: bool):
    parameter_value = opil.BooleanValue(value_id)
    parameter_value.value = value
    return parameter_value

def clone_enumerated_parameter_field(enumerated_parameter):
    return create_opil_enumerated_parameter_field(enumerated_parameter.identity, enumerated_parameter.name)

def create_opil_enumerated_parameter_field(field_id: str, field: str):
    parameter_field = opil.EnumeratedParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_enumerated_parameter_value(value_id: str, value: str):
    parameter_value = opil.EnumeratedValue(value_id)
    parameter_value.value = value
    return parameter_value

def clone_integer_parameter_field(integer_parameter):
    return create_opil_integer_parameter_field(integer_parameter.identity, integer_parameter.name)

def create_opil_integer_parameter_field(field_id: str, field: str):
    parameter_field = opil.IntegerParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_integer_parameter_value(value_id: str, value: int):
    parameter_value = opil.IntegerValue(value_id)
    parameter_value.value = value
    return parameter_value

def clone_measurement_parameter_field(measurement_parameter):
    return create_opil_measurement_parameter_field(measurement_parameter.identity, measurement_parameter.name)

def create_opil_measurement_parameter_field(field_id: str, field: str):
    parameter_field = opil.MeasureParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_measurement_parameter_value(value_id: str, value: str, unit: str):
    new_id = value_id.replace('.', '_')
    parameter_value = opil.MeasureValue(new_id)
    unit_uri = 'http://bbn.com/synbio/opil#pureNumber'
    if unit in MEASUREMENT_UNITS:
        unit_uri = MEASUREMENT_UNITS[unit]

    measure = sbol3.Measure(float(value), unit_uri, name=new_id)
    parameter_value.has_measure = measure
    return parameter_value

def clone_string_parameter_field(string_parameter):
    return create_opil_string_parameter_field(string_parameter.identity, string_parameter.name)

def create_opil_string_parameter_field(field_id: str, field: str):
    parameter_field = opil.StringParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_string_parameter_value(value_id: str, value: str):
    parameter_value = opil.StringValue(value_id)
    parameter_value.value = value
    return parameter_value

def clone_uri_parameter_field(uri_parameter):
    return create_opil_uri_parameter_field(uri_parameter.identity, uri_parameter.name)

def create_opil_uri_parameter_field(field_id: str, field: str):
    parameter_field = opil.URIParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_URI_parameter_value(value_id: str, value: str):
    parameter_value = opil.URIValue(value_id)
    parameter_value.value = value
    return parameter_value

def get_protocol_id_from_annotaton(protocol):
    namespace = 'http://strateos.com/'
    id_annotation = sbol3.TextProperty(protocol, namespace + 'strateos_id', 0, 1)

    return id_annotation.property_owner.strateos_id

def get_param_value_as_string(parameter_value):
    if type(parameter_value) is opil.opil_factory.BooleanValue:
        return str(parameter_value.value)
    elif type(parameter_value) is opil.opil_factory.EnumeratedValue:
        return str(parameter_value.value)
    elif type(parameter_value) is opil.opil_factory.IntegerValue:
        return str(parameter_value.value)
    elif type(parameter_value) is opil.opil_factory.MeasureValue:
        if parameter_value.has_measure:
            measure_number = parameter_value.has_measure.value
            measure_unit = get_measurement_unit(parameter_value.has_measure.unit)
            return '%d %s' % (measure_number, measure_unit)
    elif type(parameter_value) is opil.opil_factory.StringValue:
        return parameter_value.value if parameter_value.value else ' '
    elif type(parameter_value) is opil.opil_factory.URIValue:
        return str(parameter_value.value)

def get_measurement_unit(measure_unit):
    for unit, ontology in MEASUREMENT_UNITS.items():
        if measure_unit == ontology:
            return unit

    if measure_unit == 'http://bbn.com/synbio/opil#pureNumber':
        return ''

    return 'UNIDENTIFIED UNIT'


