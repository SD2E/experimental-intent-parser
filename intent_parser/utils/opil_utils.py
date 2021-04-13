"""
Provides a list of functions for building opil objects.
"""
from intent_parser.intent.measure_property_intent import MeasuredUnit
from intent_parser.intent_parser_exceptions import IntentParserException
import intent_parser.utils.sbol3_utils as sbol3_utils
import intent_parser.table.cell_parser as cell_parser
import intent_parser.constants.intent_parser_constants as ip_constants
import opil
import tyto


def create_opil_boolean_parameter_value(value_id: str, value: bool):
    parameter_value = opil.BooleanValue(value_id)
    parameter_value.value = value
    return parameter_value


def create_opil_enumerated_parameter_value(value_id: str, value: str):
    parameter_value = opil.EnumeratedValue(value_id)
    parameter_value.value = value
    return parameter_value


def create_opil_integer_parameter_value(value_id: str, value: int):
    parameter_value = opil.IntegerValue(value_id)
    parameter_value.value = value
    return parameter_value


def create_opil_measurement_parameter_value(value_id: str, value: float, unit=''):
    parameter_value = opil.MeasureValue(value_id)
    measure = MeasuredUnit(value, unit)
    parameter_value.has_measure = measure.to_opil_measure()
    return parameter_value


def create_opil_string_parameter_value(value_id: str, value: str):
    parameter_value = opil.StringValue(value_id)
    parameter_value.value = value
    return parameter_value


def create_opil_URI_parameter_value(value_id: str, value: str):
    parameter_value = opil.URIValue(value_id)
    parameter_value.value = value
    return parameter_value


def create_parameter_value_from_parameter(opil_parameter, parameter_value, unique_id):
    if isinstance(opil_parameter, opil.BooleanParameter):
        return create_opil_boolean_parameter_value(unique_id, bool(parameter_value))
    elif isinstance(opil_parameter, opil.EnumeratedParameter):
        return create_opil_enumerated_parameter_value(unique_id, str(parameter_value))
    elif isinstance(opil_parameter, opil.IntegerParameter):
        return create_opil_integer_parameter_value(unique_id, int(parameter_value))
    elif isinstance(opil_parameter, opil.MeasureParameter):
        possible_units = list(ip_constants.FLUID_UNIT_MAP.values())
        measured_units = cell_parser.PARSER.process_values_unit(parameter_value,
                                                                units=possible_units,
                                                                unit_type=ip_constants.FLUID_UNIT_MAP)
        if len(measured_units) != 1:
            raise IntentParserException('Expecting one Measurement Parameter value but %d were found.' % len(measured_units))
        return create_opil_measurement_parameter_value(unique_id,
                                                       float(measured_units[0].get_value()),
                                                       measured_units[0].get_unit())
    elif isinstance(opil_parameter, opil.StringParameter):
        return create_opil_string_parameter_value(unique_id, str(parameter_value))
    elif isinstance(opil_parameter, opil.URIParameter):
        return create_opil_URI_parameter_value(unique_id, str(parameter_value))


def get_param_value_as_string(parameter_value):
    if type(parameter_value) is opil.BooleanValue:
        return str(parameter_value.value)
    elif type(parameter_value) is opil.EnumeratedValue:
        return str(parameter_value.value)
    elif type(parameter_value) is opil.IntegerValue:
        return str(parameter_value.value)
    elif type(parameter_value) is opil.MeasureValue:
        if parameter_value.has_measure:
            measure_number = float(parameter_value.has_measure.value)
            measure_unit = sbol3_utils.get_unit_name_from_uri(parameter_value.has_measure.unit)
            if measure_unit:
                if measure_unit == tyto.OM.number:
                    return str(measure_number)
                else:
                    return str(measure_number) + ' ' + measure_unit
            return str(measure_number)
    elif type(parameter_value) is opil.StringValue:
        return parameter_value.value if parameter_value.value else ' '
    elif type(parameter_value) is opil.URIValue:
        return str(parameter_value.value)
    elif isinstance(parameter_value, str):
        return parameter_value
    return ''

