from intent_parser.intent_parser_exceptions import DictionaryMaintainerException, IntentParserException, TableException
from intent_parser.table.lab_table import LabTable
from intent_parser.table.parameter_table import ParameterTable
from intent_parser.table.table_processor.processor import Processor
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.utils.opil_utils as opil_utils
import logging

class ParameterInfoProcessor(Processor):

    logger = logging.getLogger('ParameterInfoProcessor')

    def __init__(self, protocol_factory, lab_names=[]):
        super().__init__()
        self._lab_names = lab_names
        self._protocol_factory = protocol_factory

        self.intent = []
        self.processed_lab_name = ''
        self.processed_protocol_id = ''
        self.processed_parameter = None

    def get_intent(self):
        intro_info = '''
        <h2>Parameter Table </h2>
        <p><b>Description</b>: %s's parameter definitions for protocol %s.</p>
        ''' % (self.processed_lab_name, self.processed_parameter.get_protocol_name())

        required_field_info = '''
        <li><b>%s</b>: an xplan directory. <i>Example</i>: xplan/directory/path</li>
        <li><b>%s</b>: a reactor assigned to xplan. <i>Acceptable value(s)</i>:xplan</li>
        <li><b>%s</b>: a microwell plate size. <i>Acceptable value(s)</i>: 24, 96</li>
        <li><b>%s</b>: a plate number. <i>Acceptable value(s)</i>: some integer value</li>
        <li><b>%s</b>: text values assigned by xplan. <i>Acceptable value(s)</i>: a list of text values</li>
        <li><b>%s</b>: text values assigned by xplan. <i>Acceptable value(s)</i>: SD2_common_name</li>
        <li><b>%s</b>: directory where this document is stored in xplan. <i>Example</i>: xplan/directory/path</li>
        <li><b>%s</b>: set true to run experiment. <i>Acceptable value(s)</i>: True or False</li>
        <li><b>%s</b>: an identifier assigned to protocol. <i>Acceptable value(s)</i>: %s</li>
        <li><b>%s</b>: set true to run experiment in test mode. <i>Acceptable value(s)</i>: True or False</li>
        <li><b>%s</b>: path to this experiment document. <i>Example</i>: experiment_request/directory/path</li>
        ''' % (ip_constants.PROTOCOL_FIELD_XPLAN_BASE_DIRECTORY,
               ip_constants.PROTOCOL_FIELD_XPLAN_REACTOR,
               ip_constants.PROTOCOL_FIELD_PLATE_SIZE,
               ip_constants.PROTOCOL_FIELD_PLATE_NUMBER,
               ip_constants.PROTOCOL_FIELD_CONTAINER_SEARCH_STRING,
               ip_constants.PROTOCOL_FIELD_STRAIN_PROPERTY,
               ip_constants.PROTOCOL_FIELD_XPLAN_PATH,
               ip_constants.PROTOCOL_FIELD_SUBMIT,
               ip_constants.PROTOCOL_FIELD_PROTOCOL_ID, self.processed_protocol_id,
               ip_constants.PROTOCOL_FIELD_TEST_MODE,
               ip_constants.PROTOCOL_FIELD_EXPERIMENT_REFERENCE_URL_FOR_XPLAN)

        optional_field_info = ''
        for ip_parameter in self.intent:
            accepted_values = ', '.join(opil_utils.get_param_value_as_string(ip_value) for ip_value in ip_parameter.get_valid_values())
            description = '''
            <li><b>%s</b>: %s. <i>Acceptable value(s):</i> %s</li>
            ''' %(ip_parameter.get_field_name(), ip_parameter.get_description(), accepted_values)
            if ip_parameter.is_required():
                required_field_info += description
            else:
                optional_field_info += description

        required_param_info = '''
        <b>Required fields:</b>
        <ul>%s</ul>
        ''' % required_field_info

        optional_param_info = '''
        <b>Optional fields:</b>
        <ul>%s</ul>
        ''' % optional_field_info
        html_info = intro_info + required_param_info + optional_param_info
        return html_info

    def process_intent(self, lab_tables=[], parameter_tables=[]):
        self._process_lab_tables(lab_tables)
        self._protocol_factory.set_selected_lab(self.processed_lab_name)

        if len(parameter_tables) == 0:
            self.validation_errors.append('Unable to get information about parameters: No parameter table to parse from document.')
            return

        self._process_parameter_tables(parameter_tables)
        parameter_fields_from_lab = self._protocol_factory.map_parameter_values(self.processed_parameter.get_protocol_name())
        for field in parameter_fields_from_lab.values():
            self.intent.append(field)

        self.processed_protocol_id = self._protocol_factory.get_protocol_id(self.processed_parameter.get_protocol_name())

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