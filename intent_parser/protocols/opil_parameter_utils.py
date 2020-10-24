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

def create_opil_boolean_parameter(field: str, value: bool):
    parameter_field = create_opil_boolean_parameter_field('%s_field_id' % field, field)
    parameter_value = create_opil_boolean_parameter_value('%s_value_id' % field, value)
    parameter_field.default_value = [parameter_value]
    return parameter_field, parameter_value

def create_opil_boolean_parameter_field(field_id: str, field: str):
    parameter_field = opil.BooleanParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_boolean_parameter_value(value_id: str, value: bool):
    parameter_value = opil.BooleanValue(value_id)
    parameter_value.value = value
    return parameter_value

def create_opil_enumerated_parameter(field: str, value: str):
    parameter_field = create_opil_enumerated_parameter_field('%s_field_id' % field, field)
    parameter_value = create_opil_enumerated_parameter_value('%s_value_id' % field, value)
    parameter_field.default_value = [parameter_value]
    return parameter_field, parameter_value

def create_opil_enumerated_parameter_field(field_id: str, field: str):
    parameter_field = opil.EnumeratedParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_enumerated_parameter_value(value_id: str, value: str):
    parameter_value = opil.EnumeratedValue(value_id)
    parameter_value.value = value
    return parameter_value

def create_opil_integer_parameter(field: str, value: int):
    parameter_field = create_opil_integer_parameter_field('%s_field_id' % field, field)
    parameter_value = create_opil_integer_parameter_value('%s_value_id' % field, value)
    parameter_field.default_value = [parameter_value]
    return parameter_field, parameter_value

def create_opil_integer_parameter_field(field_id: str, field: str):
    parameter_field = opil.IntegerParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_integer_parameter_value(value_id: str, value: int):
    parameter_value = opil.IntegerValue(value_id)
    parameter_value.value = value
    return parameter_value

def create_opil_measurement_parameter(field: str, value: str, unit: str):
    parameter_field = create_opil_measurement_parameter_field('%s_field_id' % field, field)
    parameter_value = create_opil_measurement_parameter_value('%s_value_id' % field, value, unit)
    parameter_field.default_value = [parameter_value]
    return parameter_field, parameter_value

def create_opil_measurement_parameter_field(field_id: str, field: str):
    parameter_field = opil.MeasurementParameter(field_id)
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

def create_opil_string_parameter(field: str, value: str):
    parameter_field = create_opil_string_parameter_field('%s_field_id' % field, field)
    parameter_value = create_opil_string_parameter_value('%s_value_id' % field, value)
    parameter_field.default_value = [parameter_value]
    return parameter_field, parameter_value

def create_opil_string_parameter_field(field_id: str, field: str):
    parameter_field = opil.StringParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_string_parameter_value(value_id: str, value: str):
    parameter_value = opil.StringValue(value_id)
    parameter_value.value = value
    return parameter_value

def create_opil_uri_parameter(field: str, value: str):
    parameter_field = create_opil_uri_parameter_field('%s_field_id' % field, field)
    parameter_value = create_opil_URI_parameter_value('%s_value_id' % field, value)
    parameter_field.default_value = [parameter_value]
    return parameter_field, parameter_value

def create_opil_uri_parameter_field(field_id: str, field: str):
    parameter_field = opil.URIParameter(field_id)
    parameter_field.name = field
    return parameter_field

def create_opil_URI_parameter_value(value_id: str, value: str):
    parameter_value = opil.URIValue(value_id)
    parameter_value.value = value
    return parameter_value
