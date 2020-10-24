
class Processor(object):
    """A base class for processing table output"""

    def __init__(self):
        self.validation_warnings = []
        self.validation_errors = []

    def get_warnings(self):
        return self.validation_warnings

    def get_errors(self):
        return self.validation_errors

    def get_intent(self):
        raise NotImplementedError
