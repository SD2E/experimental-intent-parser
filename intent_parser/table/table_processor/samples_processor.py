from intent_parser.intent_parser_exceptions import DictionaryMaintainerException, TableException
from intent_parser.table.table_processor.processor import Processor
from intent_parser.table.measurement_table import MeasurementTable
import logging

class StructuredRequestProcessor(Processor):
    """
    Generates a structured request from Intent Parser table templates.
    This data encoding is comes in the form of a json object.
    """

    logger = logging.getLogger('structured_request_processor')
    schema = {'$ref': 'https://schema.catalog.sd2e.org/schemas/structured_request.json'}

    def __init__(self):
        super().__init__()
        self.samples = {'action': 'calculateSamples'}
                        # 'tableIds': table_ids,
                        # 'sampleIndices': sample_indices,
                        # 'sampleValues': samples_values}
        self.processed_measurements = []


    def get_intent(self):
        return self.samples

    def process_intent(self, measurement_tables):
        self.process_measurement_tables(measurement_tables)

    def process_measurement_tables(self, measurement_tables):
        self.processed_measurements = []
        if not measurement_tables:
            return

        if len(measurement_tables) > 1:
            message = ('There are more than one measurement table specified in this experiment.'
                       'Only the last measurement table identified in the document will be used for generating a request.')
            self.validation_warnings.extend([message])
        try:
            table = measurement_tables[-1]
            meas_table = MeasurementTable(table)
            meas_table.process_table()
        except (DictionaryMaintainerException, TableException) as err:
            self.validation_errors.extend([err.get_message()])