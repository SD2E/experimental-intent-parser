from intent_parser.intent_parser_exceptions import DictionaryMaintainerException, IntentParserException, TableException
from intent_parser.table.lab_table import LabTable
from intent_parser.table.parameter_table import ParameterTable
from intent_parser.table.table_processor.processor import Processor
from intent_parser.protocols.opil_factory import OpilFactory
import intent_parser.table.cell_parser as cell_parser
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.protocols.opil_parameter_utils as opil_utils
import logging
import opil

class OPILProcessor(Processor):

    logger = logging.getLogger('opil_processor')

    def __init__(self, sbol_dictionary, lab_names={}):
        super().__init__()
        self._lab_names = lab_names
        self.processed_lab_name = ''
        self.processed_protocol_name = ''
        self.processed_parameters = {}
        self.processed_experiment_intent = None
        self.sbol_doc = None
        self.lab_accessors = {}
        self.sbol_dictionary = sbol_dictionary


    def get_intent(self):
        return self.sbol_doc

    def process_intent(self, lab_tables, parameter_tables):
        self._process_lab_tables(lab_tables)
        self._process_parameter_tables(parameter_tables)
        self._process_opil_protocol()

    def set_lab_accessor(self, lab_accessors):
        self.lab_accessors = lab_accessors

    def _get_namespace_from_lab(self):
        if self.processed_lab_name == dc_constants.LAB_TRANSCRIPTIC:
            return 'http://strateos.com/'

        return 'http://www.sd2e.org/'

    def _process_lab_tables(self, lab_tables):
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
            lab_table = LabTable(intent_parser_table=table, lab_names=self._lab_names)
            lab_table.process_table()

        processed_lab = lab_table.get_structured_request()
        self.processed_lab_name = processed_lab[dc_constants.LAB]
        self.validation_errors.extend(lab_table.get_validation_errors())
        self.validation_warnings.extend(lab_table.get_validation_warnings())

    def _process_opil_protocol(self):
        opil_factory = OpilFactory(self.lab_accessors[dc_constants.LAB_TRANSCRIPTIC])
        try:
            opil_protocol_interface = opil_factory.load_protocol_interface_from_lab(self.processed_lab_name,
                                                                                    self.processed_experiment_intent.get_protocol_name())
            namespace = self._get_namespace_from_lab()
            opil.set_namespace(namespace)
            sbol_doc = opil.Document()
            experiment_param_fields, experiment_param_values = self.processed_experiment_intent.to_opil_for_experiment()
            default_param_fields, default_param_values = self._process_default_parameters_as_opil(self.processed_experiment_intent.get_default_parameters(),
                                                                                                  opil_protocol_interface)
            experiment_param_fields.extend(default_param_fields)
            experiment_param_values.extend(default_param_values)
            for updated_param_value in experiment_param_values:
                if type(updated_param_value) is opil.opil_factory.EnumeratedParameter:
                    experiment_param_fields.append(updated_param_value)
                else:
                    sbol_doc.add(updated_param_value)

            opil_protocol_interface.has_parameter = experiment_param_fields
            sbol_doc.add(opil_protocol_interface)
            validation_report = sbol_doc.validate()
            if validation_report.is_valid:
                self.sbol_doc = sbol_doc
            else:
                self.validation_errors.append(validation_report.results)

        except IntentParserException as err:
                self.validation_errors.append(err.get_message())


    def _process_default_parameters_as_opil(self, parameters, opil_protocol_inteface):
        opil_param_values = []
        opil_param_fields = []
        for param_key, param_value in parameters.items():
            opil_param = self._get_opil_from_parameter_field(param_key, opil_protocol_inteface)
            if opil_param is None:
                continue

            opil_param_fields.append(opil_param)
            value_id = '%s_value_id' % opil_param.name.replace('.', '_')
            if type(opil_param) is opil.opil_factory.BooleanParameter:
                boolean_value = cell_parser.PARSER.process_boolean_flag(param_value)
                opil_value = opil_utils.create_opil_boolean_parameter_value(value_id, boolean_value[0])
                opil_param.default_value = [opil_value]
                opil_param_values.append(opil_value)
            elif type(opil_param) is opil.opil_factory.EnumeratedParameter:
                opil_value = opil_utils.create_opil_enumerated_parameter_value(value_id, param_value)
                opil_param.allowed_value = [opil_value]
                opil_param_values.append(opil_value)
            elif type(opil_param) is opil.opil_factory.IntegerParameter:
                int_value = cell_parser.PARSER.process_numbers(param_value)
                opil_value = opil_utils.create_opil_integer_parameter_value(value_id, int(int_value[0]))
                opil_param.default_value = [opil_value]
                opil_param_values.append(opil_value)
            elif type(opil_param) is opil.opil_factory.MeasureParameter:
                value, unit = cell_parser.PARSER.process_value_unit_without_validation(param_value)
                opil_value = opil_utils.create_opil_measurement_parameter_value(value_id, value, unit)
                opil_param.default_value = [opil_value]
                opil_param_values.append(opil_value)
            elif type(opil_param) is opil.opil_factory.StringParameter:
                opil_value = opil_utils.create_opil_string_parameter_value(value_id, param_value)
                opil_param.default_value = [opil_value]
                opil_param_values.append(opil_value)
            elif type(opil_param) is opil.opil_factory.URIParameter:
                opil_value = opil_utils.create_opil_URI_parameter_value(value_id, param_value)
                opil_param.default_value = [opil_value]
                opil_param_values.append(opil_value)

        return opil_param_fields, opil_param_values

    def _get_opil_from_parameter_field(self, parameter_field, opil_protocol_inteface):
        targeted_opil_param = None
        for opil_param in opil_protocol_inteface.has_parameter:
            if opil_param.name == parameter_field:
                targeted_opil_param = opil_param

        return targeted_opil_param

    def _process_parameter_tables(self, parameter_tables):
        if not parameter_tables:
            self.validation_errors.append('No parameter table to parse from document.')
            return

        if len(parameter_tables) > 1:
            message = ('There are more than one parameter table specified in this experiment.'
                       'Only the last parameter table identified in the document will be used for generating a request.')
            self.validation_warnings.extend([message])
        try:
            table = parameter_tables[-1]
            strateos_dictionary_mapping = self.sbol_dictionary.map_common_names_and_transcriptic_id()
            parameter_table = ParameterTable(table, parameter_fields=strateos_dictionary_mapping, run_as_opil=True)
            parameter_table.process_table()

            self.validation_errors.extend(parameter_table.get_validation_errors())
            self.processed_parameters = parameter_table.get_structured_request()
            self.processed_experiment_intent = parameter_table.get_experiment_intent()
        except (DictionaryMaintainerException, TableException) as err:
            self.validation_errors.extend([err.get_message()])

