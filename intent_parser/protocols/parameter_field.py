
class ParameterField(object):
    """
    Intent Parser representation of a parameter
    """
    def __init__(self, field_name, opil_template, required=False, valid_values={}):
        self._field_name = field_name
        self._opil_template = opil_template
        self._required = required
        self._valid_values = valid_values

    def get_field_name(self):
        return self._field_name

    def get_opil_template(self):
        return self._opil_template

    def get_required(self):
        return self._required

    def is_valid_value(self, value):
        return value in self._valid_values