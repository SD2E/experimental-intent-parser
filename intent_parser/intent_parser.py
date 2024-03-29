from datacatalog.formats.common import map_experiment_reference
from intent_parser.accessor.catalog_accessor import CatalogAccessor
from intent_parser.intent_parser_exceptions import IntentParserException
from intent_parser.table.table_processor.experimental_protocol_processor import ExperimentalProtocolProcessor
from intent_parser.table.table_processor.opil_processor import OpilProcessor
from intent_parser.table.table_processor.parameter_information_processor import ParameterInfoProcessor
from intent_parser.table.table_processor.structured_request_processor import StructuredRequestProcessor
from intent_parser.table.experiment_specification_table import ExperimentSpecificationTable
from intent_parser.table.experiment_status_table import ExperimentStatusTableParser
from intent_parser.table.intent_parser_table_factory import IntentParserTableFactory
from intent_parser.table.lab_table import LabTable
from intent_parser.table.intent_parser_table_type import TableType
import intent_parser.constants.google_api_constants as google_constants
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.table.table_utils as table_utils
import intent_parser.utils.intent_parser_utils as intent_parser_utils
import logging
import numpy as np

class IntentParser(object):
    """
    Processes information from a lab experiment to:
    """

    logger = logging.getLogger('intent_parser')

    def __init__(self, lab_experiment, datacatalog_config, sbh_instance, sbol_dictionary):
        self.lab_experiment = lab_experiment
        self.catalog_accessor = CatalogAccessor()
        self.datacatalog_config = datacatalog_config
        self.sbh = sbh_instance
        self.sbol_dictionary = sbol_dictionary
        self.ip_table_factory = IntentParserTableFactory()

        self.experiment_status = {}
        self.experiment_request = {}
        self.structured_request = {}
        self.validation_errors = []
        self.validation_warnings = []
        self.experimental_protocol = None
        self.opil_request = None
        self.table_info = None
        self.ip_tables = None
        self.tables_with_captions = {}
        self.experiment_status_tables = {}
        self.experiment_specification_tables = None
        self.processed_lab_name = None

    def create_experiment_specification_table(self, experiment_id_with_indices={}, spec_table_index=None):
        spec_table = ExperimentSpecificationTable()
        for experiment_id, table_index in experiment_id_with_indices.items():
            spec_table.add_experiment_status_table_ref(experiment_id, table_index)
        if spec_table_index is None:
            spec_table_index = self.get_largest_table_index() + 1
        spec_table.set_table_caption(spec_table_index)
        return spec_table

    def create_experiment_status_table(self, list_of_status):
        status_table = ExperimentStatusTableParser(status_mappings=self.sbol_dictionary.map_common_names_and_tacc_id())
        for status in list_of_status:
            status_table.add_status(status.status_type,
                                    status.last_updated,
                                    status.state,
                                    status.path)
        table_index = self.get_largest_table_index() + 1
        status_table.set_table_caption(table_index)
        self.tables_with_captions[table_index] = status_table.get_intent_parser_table()
        self.experiment_status_tables[table_index] = status_table
        return status_table

    def calculate_samples(self):
        doc_tables = self.lab_experiment.tables()

        table_ids = []
        sample_indices = []
        samples_values = []
        for tIdx in range(len(doc_tables)):
            table = doc_tables[tIdx]

            is_new_measurement_table = table_utils.detect_new_measurement_table(table)
            if not is_new_measurement_table:
                continue

            rows = table['tableRows']
            headerRow = rows[0]
            samples_col = -1
            for cell_idx in range(len(headerRow['tableCells'])):
                cellTxt = intent_parser_utils.get_paragraph_text(headerRow['tableCells'][cell_idx]['content'][0]['paragraph']).strip()
                if cellTxt == ip_constants.HEADER_SAMPLES_VALUE:
                    samples_col = cell_idx

            samples = []
            numCols = len(headerRow['tableCells'])

            # Scrape data for each row
            for row in rows[1:]:
                comp_count = []
                is_type_col = False
                colIdx = 0
                # Process reagents
                while colIdx < numCols and not is_type_col:
                    paragraph_element = headerRow['tableCells'][colIdx]['content'][0]['paragraph']
                    headerTxt =  intent_parser_utils.get_paragraph_text(paragraph_element).strip()
                    if headerTxt == ip_constants.HEADER_MEASUREMENT_TYPE_VALUE:
                        is_type_col = True
                    else:
                        cellContent = row['tableCells'][colIdx]['content']
                        cellTxt = ' '.join([intent_parser_utils.get_paragraph_text(c['paragraph']).strip() for c in cellContent]).strip()
                        comp_count.append(len(cellTxt.split(sep=',')))
                    colIdx += 1

                # Process the rest of the columns
                while colIdx < numCols:
                    paragraph_element = headerRow['tableCells'][colIdx]['content'][0]['paragraph']
                    headerTxt =  intent_parser_utils.get_paragraph_text(paragraph_element).strip()
                    # Certain columns don't contain info about samples
                    if headerTxt == ip_constants.HEADER_MEASUREMENT_TYPE_VALUE or headerTxt == ip_constants.HEADER_NOTES_VALUE or headerTxt == ip_constants.HEADER_SAMPLES_VALUE:
                        colIdx += 1
                        continue

                    cellContent = row['tableCells'][colIdx]['content']
                    cellTxt = ' '.join([intent_parser_utils.get_paragraph_text(c['paragraph']).strip() for c in cellContent]).strip()

                    if headerTxt == ip_constants.HEADER_REPLICATE_VALUE:
                        comp_count.append(int(cellTxt))
                    else:
                        comp_count.append(len(cellTxt.split(sep=',')))
                    colIdx += 1
                samples.append(int(np.prod(comp_count)))

            table_ids.append(tIdx)
            sample_indices.append(samples_col)
            samples_values.append(samples)

        samples = {}
        samples['action'] = 'calculateSamples'
        samples['tableIds'] = table_ids
        samples['sampleIndices'] = sample_indices
        samples['sampleValues'] = samples_values
        return samples

    def generate_displayId_from_selection(self, start_paragraph, start_offset, end_offset):
        paragraphs = self.lab_experiment.paragraphs()
        paragraph_text = intent_parser_utils.get_paragraph_text(paragraphs[start_paragraph])
        selection = paragraph_text[start_offset:end_offset + 1]
        # Remove leading/trailing space
        selection = selection.strip()
        return selection, self.sbh.generate_display_id(selection)

    def generate_report(self):
        links_info = self.lab_experiment.links_info()
        mapped_names = []
        term_map = {}
        for link_info in links_info:
            try:
                term = link_info[0].strip()
                url = link_info[1]['url']
                if len(term) == 0:
                    continue

                if term in term_map:
                    if term_map[term] == url:
                        continue

                url_host = url.split('/')[2]
                if url_host not in self.sbh.get_sbh_link_hosts():
                    continue

                term_map[term] = url
                mapped_name = {}
                mapped_name['label'] = term
                mapped_name['sbh_url'] = url
                mapped_names.append(mapped_name)
            except:
                continue

        report = {}
        report['challenge_problem_id'] = 'undefined'
        report['experiment_reference_url'] = 'https://docs.google.com/document/d/' + self.lab_experiment.document_id()
        report['labs'] = []
        report['mapped_names'] = mapped_names
        return report

    def get_experiment_specification_table(self):
        return self.experiment_specification_tables

    def get_experiment_request(self):
        return self.experiment_request

    def get_experiment_status_request(self):
        """
        Retrieve experiment status from an experiment document.
        Returns:
            A dictionary containing a lab name and a list of status elements.
        """
        return self.experiment_status

    def get_lab_name(self):
        return self.processed_lab_name

    def get_largest_table_index(self):
        """
        Retrieve the largest table index in the document.
        """
        table_indices = self.tables_with_captions.keys()
        if table_indices:
            return max(table_indices)
        return 0

    def get_table_info(self):
        return self.table_info

    def process_parameter_info(self, lab_protocol_accessor):
        filtered_tables = self.get_tables_by_type()
        param_info_processor = ParameterInfoProcessor(lab_protocol_accessor,
                                                      lab_names=[ip_constants.LAB_TRANSCRIPTIC])

        param_info_processor.process_intent(lab_tables=filtered_tables[TableType.LAB],
                                            parameter_tables=filtered_tables[TableType.PARAMETER])
        self.validation_errors.extend(param_info_processor.get_errors())
        self.validation_warnings.extend(param_info_processor.get_warnings())
        self.table_info = param_info_processor.get_intent()

    def get_experimental_protocol_request(self):
        return self.experimental_protocol

    def get_opil_request(self):
        return self.opil_request

    def get_structured_request(self):
        return self.structured_request

    def get_tables_by_type(self):
        self.process_tables()
        return self._filter_tables_by_type()

    def get_table_from_index(self, index):
        """
        Get a table from its table caption index. Example: To get Table 1 in the document, provide index as 1.
        Args:
            index: an integer value of the table caption.
        Returns:
            An instance of a table.
        """
        if index not in self.tables_with_captions:
            raise IntentParserException('Table %d does not exist within this document.' % index)
        return self.tables_with_captions[index]

    def get_validation_errors(self):
        return self.validation_errors

    def get_validation_warnings(self):
        return self.validation_warnings

    def process_experiment_run_request(self):
        filtered_tables = self.get_tables_by_type()
        experiment_ref = self._get_experiment_reference()
        experiment_ref_url = self._get_experiment_reference_url()
        cp_id = self._get_challenge_problem()
        title = self._get_request_name()

        sr_processor = StructuredRequestProcessor(experiment_ref,
                                                  experiment_ref_url,
                                                  cp_id,
                                                  title,
                                                  self.lab_experiment.head_revision(),
                                                  self.lab_experiment.bookmarks(),
                                                  self.catalog_accessor,
                                                  self.sbol_dictionary)
        sr_processor.process_experiment_intent(filtered_tables[TableType.LAB],
                                               filtered_tables[TableType.PARAMETER])
        self.experiment_request = sr_processor.get_experiment_intent()

    def process_experiment_status_request(self):
        filtered_tables = self.get_tables_by_type()
        self._generate_experiment_status_request(filtered_tables[TableType.LAB],
                                                 filtered_tables[TableType.EXPERIMENT_SPECIFICATION],
                                                 filtered_tables[TableType.EXPERIMENT_STATUS])

    def process_lab_name(self):
        filtered_tables = self.get_tables_by_type()
        lab_tables = filtered_tables[TableType.LAB]
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

        lab_name = lab_table.get_intent().get_lab_name()
        self.processed_lab_name = lab_name

    def process_experimental_protocol_request(self, lab_name, opil_document_template):
        experimental_protocol = ExperimentalProtocolProcessor(opil_document_template, lab_name)
        experimental_protocol.process_protocol_interface(self._get_experiment_reference_url())
        self.validation_errors.extend(experimental_protocol.get_errors())
        self.validation_warnings.extend(experimental_protocol.get_warnings())
        self.experimental_protocol = experimental_protocol.get_intent()

    def process_opil_request(self, lab_protocol_accessor):
        filtered_tables = self.get_tables_by_type()
        experiment_ref = self._get_experiment_reference()
        experiment_ref_url = self._get_experiment_reference_url()
        opil_processor = OpilProcessor(experiment_ref,
                                       experiment_ref_url,
                                       lab_protocol_accessor,
                                       self.sbol_dictionary,
                                       lab_names=[ip_constants.LAB_TRANSCRIPTIC, ip_constants.LAB_DUKE_HASE])
        opil_processor.process_intent(lab_tables=filtered_tables[TableType.LAB],
                                      control_tables=filtered_tables[TableType.CONTROL],
                                      parameter_tables=filtered_tables[TableType.PARAMETER],
                                      measurement_tables=filtered_tables[TableType.MEASUREMENT])
        self.validation_errors.extend(opil_processor.get_errors())
        self.validation_warnings.extend(opil_processor.get_warnings())
        self.opil_request = opil_processor.get_intent()

    def process_structure_request(self):
        filtered_tables = self.get_tables_by_type()
        experiment_ref = self._get_experiment_reference()
        experiment_ref_url = self._get_experiment_reference_url()
        cp_id = self._get_challenge_problem()
        title = self._get_request_name()

        sr_processor = StructuredRequestProcessor(experiment_ref,
                                                  experiment_ref_url,
                                                  cp_id,
                                                  title,
                                                  self.lab_experiment.head_revision(),
                                                  self.lab_experiment.bookmarks(),
                                                  self.catalog_accessor,
                                                  self.sbol_dictionary)
        sr_processor.process_intent(filtered_tables[TableType.LAB],
                                    filtered_tables[TableType.CONTROL],
                                    filtered_tables[TableType.MEASUREMENT],
                                    filtered_tables[TableType.PARAMETER])

        self.validation_errors.extend(sr_processor.get_errors())
        self.validation_warnings.extend(sr_processor.get_warnings())
        self.structured_request = sr_processor.get_intent()

    def process_tables(self):
        if self.ip_tables is None:
            tables = []
            list_of_tables = self.lab_experiment.tables()
            for table in list_of_tables:
                tables.append(self.ip_table_factory.from_google_doc(table))
            self.ip_tables = tables

    def process_table_indices(self):
        for table in self.lab_experiment.tables():
            ip_table = self.ip_table_factory.from_google_doc(table)
            table_index = ip_table.caption()
            if table_index is None:
                continue
            if table_index in self.tables_with_captions:
                message = 'There are more than one table with %d as a table caption index' % table_index
                self.validation_errors.append(message)
            self.tables_with_captions[table_index] = ip_table

    def update_experimental_results(self):
        source_doc_uri = 'https://docs.google.com/document/d/' + self.lab_experiment.document_id()

        # Search SBH to get data
        target_collection = '%s/user/%s/experiment_test/experiment_test_collection/1' % (self.sbh.get_sbh_url(), self.sbh.get_sbh_collection_user())
        exp_collection = self.sbh.query_experiments(target_collection)
        data = {}
        for exp in exp_collection:
            exp_uri = exp['uri']
            timestamp = exp['timestamp']
            title = exp['title']
            request_doc = self.sbh.query_experiment_request(exp_uri)
            if source_doc_uri == request_doc:
                source_uri = self.sbh.query_experiment_source(exp_uri)  # Get the reference to the source document with lab data
                data[exp_uri] = {'timestamp': timestamp,
                                 'agave': source_uri[0],
                                 'title': title}

        exp_data = []
        exp_links = []
        for exp in data:
            exp_data.append((data[exp]['title'], ' updated on ', data[exp]['timestamp'], ', ', 'Agave link', '\n'))
            exp_links.append((exp, '', '', '',  data[exp]['agave'], ''))

        if exp_data == '':
            exp_data = ['No currently run experiments.']

        paragraphs = self.lab_experiment.paragraphs()

        headerIdx = -1
        contentIdx = -1
        for pIdx in range(len(paragraphs)):
            para_text = intent_parser_utils.get_paragraph_text(paragraphs[pIdx])
            if para_text == "Experiment Results\n":
                headerIdx = pIdx
            elif headerIdx >= 0 and not para_text == '\n':
                contentIdx = pIdx
                break

        if headerIdx >= 0 and contentIdx == -1:
            self.logger.error('ERROR: Couldn\'t find a content paragraph index for experiment results!')

        experimental_result = {}
        experimental_result['action'] = 'updateExperimentResults'
        experimental_result['headerIdx'] = headerIdx
        experimental_result['contentIdx'] = contentIdx
        experimental_result['expData'] = exp_data
        experimental_result['expLinks'] = exp_links
        return experimental_result

    def _get_challenge_problem(self):
        try:
            if self.datacatalog_config['mongodb']['authn']:
                experiment_ref = {dc_constants.EXPERIMENT_REFERENCE_URL: self._get_experiment_reference_url()}
                map_experiment_reference(self.datacatalog_config, experiment_ref)
                return experiment_ref[dc_constants.CHALLENGE_PROBLEM]
        except Exception as err:
            message = 'Failed to map challenge problem for doc id %s! Check that this document is in the ' \
                      'Challenge Problem folder under DARPA SD2E Shared > CP Working Groups > ExperimentalRequests'\
                      % self.lab_experiment.document_id()
            self.validation_errors.append(message)
            return dc_constants.UNDEFINED

    def _get_experiment_reference_url(self):
        return google_constants.GOOGLE_DOC_URL_PREFIX + self.lab_experiment.document_id()

    def _get_experiment_reference(self):
        try:
            if self.datacatalog_config['mongodb']['authn']:
                experiment_ref = {dc_constants.EXPERIMENT_REFERENCE_URL: self._get_experiment_reference_url()}
                map_experiment_reference(self.datacatalog_config, experiment_ref)
                return experiment_ref[dc_constants.EXPERIMENT_REFERENCE]
        except Exception as err:
            message = 'Failed to map experiment reference for doc id %s!' % self.lab_experiment.document_id()
            self.validation_errors.append(message)
            return dc_constants.UNKOWN

    def _generate_experiment_status_request(self, lab_tables, experiment_specification_tables, experiment_status_tables):
        self.process_lab_name()
        exp_id_to_status_table = self._process_experiment_specification_tables(experiment_specification_tables)
        table_id_to_statuses = self._process_experiment_status_tables(experiment_status_tables)
        self.experiment_status[dc_constants.LAB] = self.processed_lab_name
        self.experiment_status[dc_constants.EXPERIMENT_ID] = exp_id_to_status_table
        self.experiment_status[dc_constants.STATUS_ELEMENT] = table_id_to_statuses

    def _get_request_name(self):
        return self.lab_experiment.title()[0]

    def _process_experiment_specification_tables(self, exp_specification_tables):
        result = {}
        if not exp_specification_tables:
            message = 'No experiment specification table to parse from document.'
            self.validation_warnings.append(message)
            return result

        if len(exp_specification_tables) > 1:
            message = 'More than one experiment specification table found. Only the last table is used.'
            self.validation_warnings.append(message)

        table = exp_specification_tables[-1]
        spec_table_parser = ExperimentSpecificationTable(table, self.catalog_accessor.get_lab_ids())
        spec_table_parser.process_table()
        self.experiment_specification_tables = spec_table_parser
        return spec_table_parser.experiment_id_to_status_table()

    def _process_experiment_status_tables(self, status_tables):
        table_id_to_statuses = {}
        if not status_tables:
            message = 'No experiment status table to parse from document.'
            self.validation_warnings.append(message)
            return table_id_to_statuses

        for table in status_tables:
            status_table_parser = ExperimentStatusTableParser(table, self.sbol_dictionary.map_common_names_and_tacc_id())
            status_table_parser.process_table()
            table_id_to_statuses[status_table_parser.get_table_caption()] = status_table_parser
            self.experiment_status_tables[table.caption()] = status_table_parser
        return table_id_to_statuses

    def _filter_tables_by_type(self):
        measurement_tables = []
        lab_tables = []
        parameter_tables = []
        control_tables = []
        experiment_status_tables = []
        experiment_spec_tables = []
        for table in self.ip_tables:
            table_type = table.get_table_type()
            if table_type == TableType.CONTROL:
                control_tables.append(table)
            elif table_type == TableType.EXPERIMENT_STATUS:
                experiment_status_tables.append(table)
            elif table_type == TableType.EXPERIMENT_SPECIFICATION:
                experiment_spec_tables.append(table)
            elif table_type == TableType.LAB:
                lab_tables.append(table)
            elif table_type == TableType.MEASUREMENT:
                measurement_tables.append(table)
            elif table_type == TableType.PARAMETER:
                parameter_tables.append(table)

        return {TableType.CONTROL: control_tables,
                TableType.EXPERIMENT_SPECIFICATION: experiment_spec_tables,
                TableType.EXPERIMENT_STATUS: experiment_status_tables,
                TableType.LAB: lab_tables,
                TableType.MEASUREMENT: measurement_tables,
                TableType.PARAMETER: parameter_tables}