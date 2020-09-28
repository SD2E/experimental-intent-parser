class Measurement(object):

    def __init__(self):
        self.intent = {}

    def add_field(self, field, value):
        self.intent[field] = value

    def to_structured_request(self):
        return self.intent
