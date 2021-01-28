import intent_parser.protocols.opil_parameter_utils as opil_utils

class ParameterField(object):
    """
    Intent Parser representation of a parameter
    """
    def __init__(self, field_name, opil_template, required=False, valid_values={}):
        self._description = ''
        self._field_name = field_name
        self._opil_template = opil_template
        self._required = required
        self._valid_values = valid_values

    def set_description(self, description):
        self._description = description

    def get_description(self):
        return self._description

    def get_field_name(self):
        return self._field_name

    def get_opil_template(self):
        return self._opil_template

    def is_required(self):
        return self._required

    def get_valid_values(self):
        return self._valid_values

    def is_valid_value(self, value: str):
        for parameter_value in self._valid_values:
            string_value = opil_utils.get_param_value_as_string(parameter_value)
            if string_value == value:
                return True
        return False