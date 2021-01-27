from intent_parser.intent_parser_exceptions import DictionaryMaintainerException, IntentParserException, TableException
from intent_parser.table.controls_table import ControlsTable
from intent_parser.table.lab_table import LabTable
from intent_parser.table.measurement_table import MeasurementTable
from intent_parser.table.parameter_table import ParameterTable
from intent_parser.table.table_processor.processor import Processor
from intent_parser.utils.id_provider import IdProvider
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.protocols.opil_parameter_utils as opil_utils
import intent_parser.table.cell_parser as cell_parser
import logging
import opil

class OPILProcessor(Processor):

    logger = logging.getLogger('opil_processor')

    # units supported for opil conversion
    _CONTROL_TYPES = ['HIGH_FITC',
                      'EMPTY_VECTOR',
                      'BASELINE',
                      'TREATMENT_1',
                      'TREATMENT_2',
                      'BASELINE_MEDIA_PR',
                      'CELL_DEATH_NEG_CONTROL',
                      'CELL_DEATH_POS_CONTROL']
    _FLUID_UNITS = ['%',
                    'M',
                    'mM',
                    'X',
                    'g/L',
                    'ug/ml',
                    'micromole',
                    'nM',
                    'uM',
                    'mg/ml',
                    'ng/ul']

    _TIME_UNITS = ['day',
                   'hour',
                   'femtosecond',
                   'microsecond',
                   'millisecond',
                   'minute',
                   'month',
                   'nanosecond',
                   'picosecond',
                   'second',
                   'week',
                   'year']

    _TEMPERATURE_UNITS = ['celsius', 'fahrenheit']
    _MEASUREMENT_TYPE = [ip_constants.MEASUREMENT_TYPE_FLOW,
                         ip_constants.MEASUREMENT_TYPE_RNA_SEQ,
                         ip_constants.MEASUREMENT_TYPE_DNA_SEQ,
                         ip_constants.MEASUREMENT_TYPE_PROTEOMICS,
                         ip_constants.MEASUREMENT_TYPE_SEQUENCING_CHROMATOGRAM,
                         ip_constants.MEASUREMENT_TYPE_AUTOMATED_TEST,
                         ip_constants.MEASUREMENT_TYPE_CFU,
                         ip_constants.MEASUREMENT_TYPE_PLATE_READER,
                         ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE,
                         ip_constants.MEASUREMENT_TYPE_EXPERIMENTAL_DESIGN]

    def __init__(self, protocol_factory, sbol_dictionary, file_types=[], lab_names=[]):
        super().__init__()
        self._lab_names = lab_names
        self._protocol_factory = protocol_factory
        self._file_types = file_types
        self._sbol_dictionary = sbol_dictionary
        self._id_provider = IdProvider()

        self.processed_lab_name = ''
        self.processed_protocol_name = ''
        self.processed_controls = {}
        self.process_measurements = []
        self.processed_parameter = None

        self.opil_document = opil.Document()

    def get_processed_controls(self, control_table_index):
        return self.processed_controls[control_table_index]

    def get_intent(self):
        return self.opil_document

    def process_intent(self, lab_tables=[], control_tables=[], parameter_tables=[], measurement_tables=[]):
        self._process_lab_tables(lab_tables)
        opil.set_namespace(self._get_namespace_from_lab())
        self._protocol_factory.set_selected_lab(self.processed_lab_name)
        strain_mapping = self._sbol_dictionary.get_mapped_strain(self.processed_lab_name)

        if len(control_tables) == 0:
            self.validation_warnings.append('No control tables to parse from document.')
        else:
            self._process_control_tables(control_tables, strain_mapping)

        if len(measurement_tables) == 0:
            self.validation_errors.append('Unable to generate opil: No measurement table to parse from document.')
        else:
            self._process_measurement_tables(measurement_tables, strain_mapping)

        if len(parameter_tables) == 0:
            self.validation_errors.append('Unable to generate opil: No parameter table to parse from document.')
        else:
            self._process_parameter_tables(parameter_tables)

        try:
            self._process_opil_output()
        except IntentParserException as err:
            self.validation_errors.append(err.get_message())

    def _get_namespace_from_lab(self):
        if self.processed_lab_name == dc_constants.LAB_TRANSCRIPTIC:
            return ip_constants.STRATEOS_NAMESPACE

        return ip_constants.SD2E_NAMESPACE

    def _process_lab_tables(self, lab_tables):
        if len(lab_tables) == 0:
            message = 'No lab table specified in this experiment. Generated default values for lab contents.'
            self.logger.warning(message)
            lab_table = LabTable()
        else:
            if len(lab_tables) > 1:
                message = ('There are more than one lab table specified in this experiment.'
                           'Only the last lab table identified in the document will be used for generating a request.')
                self.validation_warnings.extend([message])

            table = lab_tables[-1]
            lab_table = LabTable(intent_parser_table=table, lab_names=self._lab_names)
            lab_table.process_table()

        processed_lab = lab_table.get_intent()
        self.processed_lab_name = processed_lab.get_lab_name()
        self.validation_errors.extend(lab_table.get_validation_errors())
        self.validation_warnings.extend(lab_table.get_validation_warnings())

    def _process_opil_output(self):
        if not self._protocol_factory.support_lab(self.processed_lab_name):
            raise IntentParserException('lab %s not supported for exporting opil metadata.' % self.processed_lab_name)

        opil_experimental_result = opil.ExperimentalRequest(self._id_provider.get_unique_sd2_id())
        opil_experimental_result.name = 'Experimental Result'

        opil_measurements = []
        opil_measurement_types = []
        for measurement_intent in self.process_measurements:
            opil_measurement, measurement_type = measurement_intent.to_opil()
            opil_measurement_types.append(measurement_type)
            opil_measurements.append(opil_measurement)
            measurement_intent.to_sbol(self.opil_document)

        if len(opil_measurements) > 0:
            opil_experimental_result.measurements = opil_measurements

        if self.processed_parameter:
            if self.processed_parameter.get_protocol_name() is None:
                raise IntentParserException('Unable to process parameter for opil: missing protocol name')
            parameter_fields_from_lab = self._protocol_factory.map_parameter_values(self.processed_parameter.get_protocol_name())

            run_param_fields, run_param_values = self.processed_parameter.to_opil_for_experiment()
            default_param_fields, default_param_values = self._process_default_parameters_as_opil(self.processed_parameter.get_default_parameters(),
                                                                                                  parameter_fields_from_lab,
                                                                                                  self.opil_document)
            all_param_values = run_param_values + default_param_values
            if len(all_param_values) > 0:
                opil_experimental_result.has_parameter_value = all_param_values

            all_param_fields = run_param_fields + default_param_fields
            opil_protocol_interface = self._protocol_factory.get_protocol_interface(self.processed_parameter.get_protocol_name())
            copied_protocol_interface = opil_protocol_interface.copy(self.opil_document)
            if len(all_param_fields) > 0:
                copied_protocol_interface.has_parameter = all_param_fields
            if len(opil_measurement_types) > 0:
                copied_protocol_interface.protocol_measurement_type = opil_measurement_types

        self.opil_document.add(opil_experimental_result)

        validation_report = self.opil_document.validate()
        if not validation_report.is_valid:
            raise IntentParserException(validation_report.message)

    def _validate_parameters_from_lab(self, parameter_fields_from_document, parameter_fields_from_lab):
        # Check for required fields.
        is_valid = True
        for field in parameter_fields_from_lab.values():
            if field.get_required() and field.get_field_name() not in parameter_fields_from_document:
                self.validation_errors.append('missing required parameter field %s' % field.get_field_name())
                is_valid = False
        # Check for valid values.
        for name, value in parameter_fields_from_document.items():
            if name not in parameter_fields_from_lab:
                is_valid = False
                self.validation_errors.append('%s is not a supported parameter field for protocol %s' %(name, self.processed_parameter.get_protocol_name()))
            elif not parameter_fields_from_lab[name].is_valid_value(value):
                is_valid = False
                self.validation_errors.append('%s is not a valid parameter value for parameter field %s' % (
                                                value, name))
        return is_valid

    def _process_default_parameters_as_opil(self, parameter_fields_from_document, parameter_fields_from_lab, opil_document):
        opil_param_values = []
        opil_param_fields = []
        if not self._validate_parameters_from_lab(parameter_fields_from_document, parameter_fields_from_lab):
            raise IntentParserException('Invalid parameter found.')

        for param_key, param_value in parameter_fields_from_document.items():
            param_field = parameter_fields_from_lab[param_key].get_opil_template()

            value_id = self._id_provider.get_unique_sd2_id()
            opil_param_field = param_field.copy(opil_document)
            opil_param_fields.append(opil_param_field)
            if type(param_field) is opil.opil_factory.BooleanParameter:
                boolean_value = cell_parser.PARSER.process_boolean_flag(param_value)
                opil_value = opil_utils.create_opil_boolean_parameter_value(value_id, boolean_value[0])
                param_field.default_value = opil_value
                opil_param_values.append(opil_value)

            elif type(param_field) is opil.opil_factory.EnumeratedParameter:
                opil_value = opil_utils.create_opil_enumerated_parameter_value(value_id, param_value)
                param_field.default_value = opil_value
                opil_param_values.append(opil_value)

            elif type(param_field) is opil.opil_factory.IntegerParameter:
                int_value = cell_parser.PARSER.process_numbers(param_value)
                opil_value = opil_utils.create_opil_integer_parameter_value(value_id, int(int_value[0]))
                param_field.default_value = opil_value
                opil_param_values.append(opil_value)

            elif type(param_field) is opil.opil_factory.MeasureParameter:
                if cell_parser.PARSER.is_number(param_value):
                    value = cell_parser.PARSER.process_numbers(param_value)
                    unit = ip_constants.NCIT_NOT_APPLICABLE
                    opil_value = opil_utils.create_opil_measurement_parameter_value(value_id, value[0], unit)
                    param_field.default_value = opil_value
                    opil_param_values.append(opil_value)
                elif cell_parser.PARSER.is_valued_cell(param_value):
                    value, unit = cell_parser.PARSER.process_value_unit_without_validation(param_value)
                    opil_value = opil_utils.create_opil_measurement_parameter_value(value_id, float(value), unit)
                    param_field.default_value = opil_value
                    opil_param_values.append(opil_value)
                else:
                    self.validation_errors.append('Unable to create an OPIL Measurement ParameterValue. '
                                                  'Expecting to get a  numerical value or a numerical value '
                                                  'followed by a unit but got %s' % param_value)

            elif type(param_field) is opil.opil_factory.StringParameter:
                opil_value = opil_utils.create_opil_string_parameter_value(value_id, param_value)
                param_field.default_value = opil_value
                opil_param_values.append(opil_value)

            elif type(param_field) is opil.opil_factory.URIParameter:
                opil_value = opil_utils.create_opil_URI_parameter_value(value_id, param_value)
                param_field.default_value = opil_value
                opil_param_values.append(opil_value)

        return opil_param_fields, opil_param_values

    def _process_control_tables(self, control_tables, strain_mapping):
        if not control_tables:
            self.validation_errors.append('No control tables to parse from document.')
            return
        try:
            for table in control_tables:
                controls_table = ControlsTable(table,
                                               control_types=self._CONTROL_TYPES,
                                               fluid_units=self._FLUID_UNITS,
                                               timepoint_units=self._TIME_UNITS,
                                               strain_mapping=strain_mapping)
                controls_table.process_table()
                table_caption = controls_table.get_table_caption()
                control_intents = controls_table.get_intents()
                if table_caption:
                    self.processed_controls[table_caption] = control_intents

                self.validation_errors.extend(controls_table.get_validation_errors())
                self.validation_warnings.extend(controls_table.get_validation_warnings())
        except IntentParserException as err:
            self.validation_errors.extend([err.get_message()])


    def _process_measurement_tables(self, measurement_tables, strain_mapping):
        if len(measurement_tables) > 1:
            message = ('There are more than one measurement table specified in this experiment.'
                       'Only the last measurement table identified in the document will be used for generating a request.')
            self.validation_warnings.extend([message])
        try:
            table = measurement_tables[-1]
            measurement_table = MeasurementTable(table,
                                                 temperature_units=self._TEMPERATURE_UNITS,
                                                 timepoint_units=self._TIME_UNITS,
                                                 fluid_units=self._FLUID_UNITS,
                                                 measurement_types=self._MEASUREMENT_TYPE,
                                                 file_type=self._file_types,
                                                 strain_mapping=strain_mapping)

            measurement_table.process_table(control_data=self.processed_controls)

            self.process_measurements.extend(measurement_table.get_intents())
            self.validation_warnings.extend(measurement_table.get_validation_warnings())
            self.validation_errors.extend(measurement_table.get_validation_errors())

        except (DictionaryMaintainerException, TableException, IntentParserException) as err:
            self.validation_errors.extend([err.get_message()])

    def _process_parameter_tables(self, parameter_tables):
        if len(parameter_tables) > 1:
            message = ('There are more than one parameter table specified in this experiment.'
                       'Only the last parameter table identified in the document will be used for generating a request.')
            self.validation_warnings.extend([message])
        try:
            table = parameter_tables[-1]
            parameter_table = ParameterTable(table, run_as_opil=True)
            parameter_table.process_table()

            self.validation_warnings.extend(parameter_table.get_validation_warnings())
            self.validation_errors.extend(parameter_table.get_validation_errors())

            self.processed_parameter = parameter_table.get_parameter_intent()

        except (DictionaryMaintainerException, IntentParserException, TableException) as err:
            self.validation_errors.extend([err.get_message()])

