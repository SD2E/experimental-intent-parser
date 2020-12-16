from intent_parser.table.table_processor.processor import Processor
from intent_parser.intent_parser_exceptions import DictionaryMaintainerException, TableException
from intent_parser.table.controls_table import ControlsTable
from intent_parser.table.lab_table import LabTable
from intent_parser.table.measurement_table import MeasurementTable
from intent_parser.table.parameter_table import ParameterTable
from jsonschema import validate
from jsonschema import ValidationError
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import logging

class StructuredRequestProcessor(Processor):

    logger = logging.getLogger('structured_request_processor')
    schema = {'$ref': 'https://schema.catalog.sd2e.org/schemas/structured_request.json'}

    def __init__(self, experiment_ref, experiment_ref_url, cp_id, title, doc_revision_id, bookmark_ids, catalog_accessor, sbol_dictionary):
        super().__init__()
        self._experiment_ref_url = experiment_ref_url
        self.request = {dc_constants.EXPERIMENT_REQUEST_NAME: title,
                        dc_constants.CHALLENGE_PROBLEM: cp_id,
                        dc_constants.EXPERIMENT_REFERENCE: experiment_ref,
                        dc_constants.EXPERIMENT_REFERENCE_URL: experiment_ref_url,
                        dc_constants.EXPERIMENT_VERSION: 1,
                        dc_constants.DOCUMENT_REVISION_ID: doc_revision_id}

        self.bookmark_ids = bookmark_ids
        self.catalog_accessor = catalog_accessor
        self.sbol_dictionary = sbol_dictionary
        self.processed_labs = {}
        self.processed_measurements = []
        self.processed_controls = {}
        self.processed_parameters = []
        self.processed_parameter_experiment = {}

    def get_intent(self):
        return self.request

    def get_experiment_intent(self):
        return self.processed_parameter_experiment

    def process_experiment_intent(self, lab_tables, parameter_tables):
        self.process_lab_tables(lab_tables)
        self.process_parameter_tables(parameter_tables)

    def process_intent(self, lab_tables, control_tables, measurement_tables, parameter_tables):
        self.process_lab_tables(lab_tables)
        self.process_control_tables(control_tables)
        self.process_measurement_tables(measurement_tables)
        self.process_parameter_tables(parameter_tables)

        self.request.update({
            dc_constants.EXPERIMENT_ID: self.processed_labs[dc_constants.EXPERIMENT_ID],
            dc_constants.LAB: self.processed_labs[dc_constants.LAB],
            dc_constants.RUNS: self.processed_measurements
        })

        if self.processed_parameters:
            self.request[dc_constants.PARAMETERS] = self.processed_parameters
        self.validate_schema()

    def process_control_tables(self, control_tables):
        self.processed_controls = {}

        if not control_tables:
            self.validation_warnings.append('No controls table to parse from document.')
            return

        try:
            strain_mapping = self.sbol_dictionary.get_mapped_strain(self.processed_labs[dc_constants.LAB])
        except (DictionaryMaintainerException, TableException) as err:
            self.validation_errors.extend([err.get_message()])

        for table in control_tables:
            controls_table = ControlsTable(table,
                                           control_types=self.catalog_accessor.get_control_type(),
                                           fluid_units=self.catalog_accessor.get_fluid_units(),
                                           timepoint_units=self.catalog_accessor.get_time_units(),
                                           strain_mapping=strain_mapping)
            controls_table.process_table()
            controls_data = controls_table.get_structured_request()
            table_caption = controls_table.get_table_caption()
            if table_caption:
                self.processed_controls[table_caption] = controls_data
            self.validation_errors.extend(controls_table.get_validation_errors())
            self.validation_warnings.extend(controls_table.get_validation_warnings())

    def process_lab_tables(self, lab_tables):
        if not lab_tables:
            message = 'No lab table specified in this experiment. Generated default values for lab contents.'
            self.logger.warning(message)
            lab_table = LabTable()
        else:
            if len(lab_tables) > 1:
                message = ('There are more than one lab table specified in this experiment.'
                           'Only the last lab table identified in the document will be used for generating a request.')
                self.validation_warnings.extend([message])

            table = lab_tables[-1]
            lab_table = LabTable(intent_parser_table=table, lab_names=self.catalog_accessor.get_lab_ids())
            lab_table.process_table()

        self.processed_labs = lab_table.get_structured_request()
        self.validation_errors.extend(lab_table.get_validation_errors())
        self.validation_warnings.extend(lab_table.get_validation_warnings())

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

            strain_mapping = self.sbol_dictionary.get_mapped_strain(self.processed_labs[dc_constants.LAB])
            meas_table = MeasurementTable(table,
                                          temperature_units=self.catalog_accessor.get_temperature_units(),
                                          timepoint_units=self.catalog_accessor.get_time_units(),
                                          fluid_units=self.catalog_accessor.get_fluid_units(),
                                          measurement_types=self.catalog_accessor.get_measurement_types(),
                                          file_type=self.catalog_accessor.get_file_types(),
                                          strain_mapping=strain_mapping)

            meas_table.process_table(control_tables=self.processed_controls, bookmarks=self.bookmark_ids)

            self.processed_measurements.append({dc_constants.MEASUREMENTS: meas_table.get_structured_request()})
            self.validation_errors.extend(meas_table.get_validation_errors())
            self.validation_warnings.extend(meas_table.get_validation_warnings())
        except (DictionaryMaintainerException, TableException) as err:
            self.validation_errors.extend([err.get_message()])

    def process_parameter_tables(self, parameter_tables):
        if not parameter_tables:
            self.validation_errors.append('No parameter table to parse from document.')
            return

        if len(parameter_tables) > 1:
            message = ('There are more than one parameter table specified in this experiment.'
                       'Only the last parameter table identified in the document will be used for generating a request.')
            self.logger.warning(message)
        try:
            table = parameter_tables[-1]
            strateos_dictionary_mapping = self.sbol_dictionary.map_common_names_and_transcriptic_id()
            parameter_table = ParameterTable(table, strateos_dictionary_mapping)
            parameter_table.set_experiment_reference_url(self._experiment_ref_url)
            parameter_table.process_table()

            self.validation_errors.extend(parameter_table.get_validation_errors())
            self.processed_parameters.append(parameter_table.get_structured_request())
            self.processed_parameter_experiment = parameter_table.get_experiment()
        except (DictionaryMaintainerException, TableException) as err:
            self.validation_errors.extend([err.get_message()])

    def validate_schema(self):
        try:
            validate(self.request, self.schema)
        except ValidationError as err:
            self.validation_errors.append(format(err).replace('\n', '&#13;&#10;'))