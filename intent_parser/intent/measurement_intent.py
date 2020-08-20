
class MeasurementIntent(object):

    def __init__(self):
        self.intent = []

    def add_measurement(self, measurement):
        self.intent.append(measurement)

    def to_structured_request(self):

        return [measurement.to_structured_request() for measurement in self.intent if self.intent]

class Measurement(object):

    def __init__(self):
        self.intent = {}

    def add_field(self, field, value):
        self.intent[field] = value

    def to_structured_request(self):
        return self.intent
