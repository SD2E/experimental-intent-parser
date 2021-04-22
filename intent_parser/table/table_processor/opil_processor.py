from intent_parser.intent_parser_exceptions import DictionaryMaintainerException, IntentParserException, TableException
from intent_parser.protocols.templates.experimental_request_template import ExperimentalRequest
from intent_parser.table.controls_table import ControlsTable
from intent_parser.table.lab_table import LabTable
from intent_parser.table.measurement_table import MeasurementTable
from intent_parser.table.parameter_table import ParameterTable
from intent_parser.table.table_processor.processor import Processor
from intent_parser.utils.id_provider import IdProvider
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import logging
import opil


class OpilProcessor(Processor):

    logger = logging.getLogger('opil_processor')
    _CONTROL_TYPES = ['HIGH_FITC',
                      'EMPTY_VECTOR',
                      'BASELINE',
                      'TREATMENT_1',
                      'TREATMENT_2',
                      'BASELINE_MEDIA_PR',
                      'CELL_DEATH_NEG_CONTROL',
                      'CELL_DEATH_POS_CONTROL']

    _FILE_TYPES = ['CSV',
                   'FCS'
                   ]

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

    _TIME_UNITS = [ip_constants.TIME_UNIT_DAY,
                   ip_constants.TIME_UNIT_HOUR,
                   ip_constants.TIME_UNIT_FEMTOSECOND,
                   ip_constants.TIME_UNIT_MICROSECOND,
                   ip_constants.TIME_UNIT_MILLISECOND,
                   ip_constants.TIME_UNIT_MINUTE,
                   ip_constants.TIME_UNIT_MONTH,
                   ip_constants.TIME_UNIT_NANOSECOND,
                   ip_constants.TIME_UNIT_PICOSECOND,
                   ip_constants.TIME_UNIT_SECOND,
                   ip_constants.TIME_UNIT_WEEK,
                   ip_constants.TIME_UNIT_YEAR]

    _MEASUREMENT_TYPE = [ip_constants.MEASUREMENT_TYPE_FLOW,
                         ip_constants.MEASUREMENT_TYPE_FLUOESCENE_MICROSCOPY,
                         ip_constants.MEASUREMENT_TYPE_RNA_SEQ,
                         ip_constants.MEASUREMENT_TYPE_DNA_SEQ,
                         ip_constants.MEASUREMENT_TYPE_PROTEOMICS,
                         ip_constants.MEASUREMENT_TYPE_SEQUENCING_CHROMATOGRAM,
                         ip_constants.MEASUREMENT_TYPE_AUTOMATED_TEST,
                         ip_constants.MEASUREMENT_TYPE_CFU,
                         ip_constants.MEASUREMENT_TYPE_PLATE_READER,
                         ip_constants.MEASUREMENT_TYPE_CONDITION_SPACE,
                         ip_constants.MEASUREMENT_TYPE_EXPERIMENTAL_DESIGN]

    def __init__(self,
                 experiment_ref,
                 experiment_ref_url,
                 lab_protocol_accessor,
                 sbol_dictionary,
                 lab_names=[]):
        super().__init__()
        self.processed_lab_name = ''
        self.processed_protocol_name = ''
        self.processed_controls = {}
        self.measurement_table = None
        self.processed_parameter = None
        self.opil_document = None

        self._experiment_id = None
        self._experiment_ref = experiment_ref
        self._experiment_ref_url = experiment_ref_url
        self._sbol_dictionary = sbol_dictionary
        self._lab_protocol_accessor = lab_protocol_accessor
        self._lab_names = lab_names
        self._id_provider = IdProvider()

    def get_intent(self):
        return self.opil_document

    def process_intent(self, lab_tables=[], control_tables=[], parameter_tables=[], measurement_tables=[]):
        self._process_tables(lab_tables, control_tables, parameter_tables, measurement_tables)
        try:
            self._process_opil()
        except IntentParserException as err:
            self.validation_errors.append(err.get_message())

    def _process_tables(self, lab_tables, control_tables, parameter_tables, measurement_tables):
        self._process_lab_tables(lab_tables)
        # opil.set_namespace(self._get_namespace_from_lab())
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

    def _process_opil(self):
        if not self.processed_protocol_name:
            raise IntentParserException('Name of lab must be provided for describing an experimental request but'
                                        'none was given.')

        opil_lab_template = self._lab_protocol_accessor.load_protocol_interface_from_lab(self.processed_protocol_name,
                                                                                         self.processed_lab_name)
        experimental_request = ExperimentalRequest(self._get_namespace_from_lab(),
                                                   opil_lab_template,
                                                   self._experiment_id,
                                                   self._experiment_ref,
                                                   self._experiment_ref_url)
        experimental_request.load_experimental_request()

        # add control table info
        if self.processed_controls:
            for control_table in self.processed_controls.values():
                experimental_request.load_from_control_table(control_table)

        # add measurement table info
        if self.measurement_table:
            experimental_request.load_from_measurement_table(self.measurement_table)
            experimental_request.load_sample_template_from_protocol_interface()
            experimental_request.create_subcomponents_from_template()
            experimental_request.load_sample_set(len(self.measurement_table.get_intents()))
            experimental_request.add_variable_features_from_measurement_intents(self.measurement_table.get_intents())
            experimental_request.load_and_update_measurement(self.measurement_table.get_intents())

        # add parameter table info
        if self.processed_parameter:
            experimental_request.load_lab_parameters()
            experimental_request.update_parameter_values(self.processed_parameter.get_default_parameters())
            experimental_request.add_run_parameters(self.processed_parameter)

        experimental_request.connect_properties()
        self.opil_document = experimental_request.to_opil()

    def _get_namespace_from_lab(self):
        if self.processed_lab_name == dc_constants.LAB_TRANSCRIPTIC:
            return ip_constants.STRATEOS_NAMESPACE
        elif self.processed_lab_name == dc_constants.LAB_DUKE_HAASE:
            return ip_constants.AQUARIUM_NAMESPACE
        return ip_constants.SD2E_NAMESPACE

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
                if table_caption:
                    self.processed_controls[table_caption] = controls_table

                self.validation_errors.extend(controls_table.get_validation_errors())
                self.validation_warnings.extend(controls_table.get_validation_warnings())
        except IntentParserException as err:
            self.validation_errors.extend([err.get_message()])

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
            lab_table = LabTable(intent_parser_table=table,
                                 lab_names=self._lab_names)
            lab_table.process_table()

        processed_lab = lab_table.get_intent()
        self.processed_lab_name = processed_lab.get_lab_name()
        self._experiment_id = processed_lab.to_structured_request()[dc_constants.EXPERIMENT_ID]
        self.validation_errors.extend(lab_table.get_validation_errors())
        self.validation_warnings.extend(lab_table.get_validation_warnings())

    def _process_measurement_tables(self, measurement_tables, strain_mapping):
        if len(measurement_tables) > 1:
            message = ('There are more than one measurement table specified in this experiment.'
                       'Only the last measurement table identified in the document will be used for generating a request.')
            self.validation_warnings.extend([message])
        try:
            table = measurement_tables[-1]
            measurement_table = MeasurementTable(table,
                                                 temperature_units=list(ip_constants.TEMPERATURE_UNIT_MAP.keys()),
                                                 timepoint_units=list(ip_constants.TIME_UNIT_MAP.keys()),
                                                 fluid_units=list(ip_constants.FLUID_UNIT_MAP.keys()),
                                                 measurement_types=self._MEASUREMENT_TYPE,
                                                 file_type=self._FILE_TYPES,
                                                 strain_mapping=strain_mapping)

            control_data = {}
            for table_caption, control_table in self.processed_controls.items():
                control_data[table_caption] = control_table.get_intents()
            measurement_table.process_table(control_data=control_data)

            self.measurement_table = measurement_table
            self.validation_warnings.extend(measurement_table.get_validation_warnings())
            self.validation_errors.extend(measurement_table.get_validation_errors())

        except (DictionaryMaintainerException, TableException, IntentParserException) as err:
            self.validation_errors.extend([err.get_message()])

    def _process_parameter_tables(self, parameter_tables):
        if len(parameter_tables) > 1:
            message = ('There are more than one parameter table specified in this experiment.'
                       'Only the last parameter table identified in the document will be used for generating opil.')
            self.validation_warnings.extend([message])
        try:
            table = parameter_tables[-1]
            strateos_dictionary_mapping = self._sbol_dictionary.map_common_names_and_transcriptic_id()
            parameter_table = ParameterTable(table,
                                             parameter_fields=strateos_dictionary_mapping,
                                             run_as_opil=True)
            parameter_table.process_table()

            self.validation_warnings.extend(parameter_table.get_validation_warnings())
            self.validation_errors.extend(parameter_table.get_validation_errors())
            processed_parameter_intent = parameter_table.get_parameter_intent()
            self.processed_parameter = processed_parameter_intent
            self.processed_protocol_name = processed_parameter_intent.get_protocol_name()

        except (DictionaryMaintainerException, IntentParserException, TableException) as err:
            self.validation_errors.extend([err.get_message()])


