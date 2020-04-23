from catalog_accessor import CatalogAccessor
from datacatalog.formats.common import map_experiment_reference
from intent_parser_exceptions import DictionaryMaintainerException
from jsonschema import validate
from jsonschema import ValidationError
from lab_experiment import LabExperiment
from lab_table import LabTable
from measurement_table import MeasurementTable
from parameter_table import ParameterTable
import intent_parser_constants
import intent_parser_utils
import logging
import numpy as np
import table_utils

class IntentParser(object):
    '''
    Processes information from a lab experiment to:
        - link information to/from a SynBioHub data repository
        - generate and validate a structure request
    '''
    
    # Used for inserting experiment result data
    # Since the experiment result data is uploaded with the requesting document id
    # and the test documents are copies of those, the ids won't match
    # In order to test this, if we receive a document Id in the key of this map, we will instead query for the value
    _test_doc_id_map = {'1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoT' : '10HqgtfVCtYhk3kxIvQcwljIUonSNlSiLBC8UFmlwm1s',
                       '1RenmUdhsXMgk4OUWReI2oS6iF5R5rfWU5t7vJ0NZOHw': '1g0SjxU2Y5aOhUbM63r8lqV50vnwzFDpJg4eLXNllut4',
                       '1_I4pxB26zOLb209Xlv8QDJuxiPWGDafrejRDKvZtEl8': '1K5IzBAIkXqJ7iPF4OZYJR7xgSts1PUtWWM2F0DKhct0',
                       '1zf9l0K4rj7I08ZRpxV2ZY54RMMQc15Rlg7ULviJ7SBQ': '1uXqsmRLeVYkYJHqgdaecmN_sQZ2Tj4Ck1SZKcp55yEQ' }

    logger = logging.getLogger('intent_parser')
    
    def __init__(self, lab_experiment, datacatalog_config, sbh_instance, sbol_dictionary):
        self.lab_experiment = lab_experiment 
        self.catalog_accessor = CatalogAccessor()
        self.datacatalog_config = datacatalog_config
        self.sbh = sbh_instance
        self.sbol_dictionary = sbol_dictionary
        
        self.request = {} 
        self.validation_errors = []
        self.validation_warnings = []
       
    def process(self):
        self._generate_request()
        self._validate_schema()
    
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
                if cellTxt == intent_parser_constants.COL_HEADER_SAMPLES:
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
                    if headerTxt == intent_parser_constants.COL_HEADER_MEASUREMENT_TYPE:
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
                    if headerTxt == intent_parser_constants.COL_HEADER_MEASUREMENT_TYPE or headerTxt == intent_parser_constants.COL_HEADER_NOTES or headerTxt == intent_parser_constants.COL_HEADER_SAMPLES:
                        colIdx += 1
                        continue

                    cellContent = row['tableCells'][colIdx]['content']
                    cellTxt = ' '.join([intent_parser_utils.get_paragraph_text(c['paragraph']).strip() for c in cellContent]).strip()

                    if headerTxt == intent_parser_constants.COL_HEADER_REPLICATE:
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
                if url_host not in self.sbh.get_sbh_link_host():
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
    
    def generate_displayId_from_selection(self, start_paragraph, start_offset, end_offset):
        paragraphs = self.lab_experiment.paragraphs()
        paragraph_text = intent_parser_utils.get_paragraph_text(paragraphs[start_paragraph])
        selection = paragraph_text[start_offset:end_offset + 1]
        # Remove leading/trailing space
        selection = selection.strip()
        return selection, self.sbh.sanitize_name_to_display_id(selection)
      
    def get_structured_request(self):
        return self.request
    
    def get_validation_errors(self):
        return self.validation_errors
    
    def get_validation_warnings(self):
        return self.validation_warnings
    
    def update_experimental_results(self):
        # For test documents, replace doc id with corresponding production doc
        if self.lab_experiment.document_id() in self._test_doc_id_map:
            source_doc_uri = 'https://docs.google.com/document/d/' + self._test_doc_id_map[self.lab_experiment.document_id()]
        else:
            source_doc_uri = 'https://docs.google.com/document/d/' + self.lab_experiment.document_id()

        # Search SBH to get data
        target_collection = '%s/user/%s/experiment_test/experiment_test_collection/1' % (self.sbh.get_sbh_url(), self.sbh.get_sbh_collection_user())
        exp_collection = self.sbh.query_experiments(self.sbh, target_collection)
        data = {}
        for exp in exp_collection:
            exp_uri = exp['uri']
            timestamp = exp['timestamp']
            title = exp['title']
            request_doc = self.sbh.query_experiment_request(exp_uri)
            if source_doc_uri == request_doc:
                source_uri = self.sbh.query_experiment_source(exp_uri)  # Get the reference to the source document with lab data
                data[exp_uri] = {'timestamp' : timestamp, 'agave' : source_uri[0], 'title' : title}

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
   
    def get_challenge_problem_id(self, text):
        """
        Find the closest matching measurement type to the given type, and return that as a string
        """
        # challenge problem ids have underscores, so replace spaces with underscores to make the inputs match better
        text = text.replace(' ', '_')
        best_match_type = None
        best_match_size = 0
        for cid in self.catalog_accessor.get_challenge_problem_ids():
            matches = intent_parser_utils.find_common_substrings(text.lower(), cid.lower(), 1, 0)
            for m in matches:
                if m.size > best_match_size and m.size > int(0.25 * len(cid)):
                    best_match_type = cid
                    best_match_size = m.size
        return best_match_type
     
    def _generate_request(self):
        """
        Generates a structured request for a given doc id
        """
        output_doc = { "experiment_reference_url" : "https://docs.google.com/document/d/%s" % self.lab_experiment.document_id() }
        if self.datacatalog_config['mongodb']['authn']:
            try:
                map_experiment_reference(self.datacatalog_config, output_doc)
            except:
                pass # We don't need to do anything, failure is handled later, but we don't want it to crash

        lab = 'Unknown'
        title = self.lab_experiment.title()[0]
        experiment_id = 'experiment.tacc.TBD'

        if 'challenge_problem' in output_doc and 'experiment_reference' in output_doc and 'experiment_reference_url' in output_doc:
            cp_id = output_doc['challenge_problem']
            experiment_reference = output_doc['experiment_reference']
            experiment_reference_url = output_doc['experiment_reference_url']
        else:
            self.logger.info('WARNING: Failed to map experiment reference for doc id %s!' % self.lab_experiment.document_id())
            titleToks = title.split(sep='-')
            if len(titleToks) > 1:
                experiment_reference = title.split(sep='-')[1].strip()
            else:
                experiment_reference = title
            experiment_reference_url = 'https://docs.google.com/document/d/' + self.lab_experiment.document_id()
            # This will return a parent list, which should have one or more Ids of parent directories
            # We want to navigate those and see if they are a close match to a challenge problem ID
            parent_list = self.lab_experiment.parents()
            cp_id = 'Unknown'
            if not parent_list['kind'] == 'drive#parentList':
                self.logger.info('ERROR: expected a drive#parent_list, received a %s' % parent_list['kind'])
            else:
                for parent_ref in parent_list['items']:
                    if not parent_ref['kind'] == 'drive#parentReference':
                        continue
                    parent_experiment = LabExperiment(parent_ref['id'])
                    parent_meta = parent_experiment.load_metadata_from_google_doc()
                    new_cp_id = self.get_challenge_problem_id(parent_meta['title'])
                    if new_cp_id is not None:
                        cp_id = new_cp_id

        measurements = []
        parameter = []

        doc_tables = self.lab_experiment.tables() 
        measurement_table_new_idx = -1
        lab_table_idx = -1
        parameter_table_idx = -1
        for tIdx in range(len(doc_tables)):
            table = doc_tables[tIdx]
            
            is_new_measurement_table = table_utils.detect_new_measurement_table(table)
            if is_new_measurement_table:
                measurement_table_new_idx = tIdx

            is_lab_table = table_utils.detect_lab_table(table)
            if is_lab_table:
                lab_table_idx = tIdx
                
            is_parameter_table = table_utils.detect_parameter_table(table)
            if is_parameter_table:
                parameter_table_idx = tIdx

        if measurement_table_new_idx >= 0:
            table = doc_tables[measurement_table_new_idx]
            meas_table = MeasurementTable(self.catalog_accessor.get_temperature_units(), 
                                          self.catalog_accessor.get_time_units(), 
                                          self.catalog_accessor.get_fluid_units(), 
                                          self.catalog_accessor.get_measurement_types(), 
                                          self.catalog_accessor.get_file_types())
            measurements = meas_table.parse_table(table)
            self.validation_errors.extend(meas_table.get_validation_errors())
            self.validation_warnings.extend(meas_table.get_validation_warnings())

        if lab_table_idx >= 0:
            table = doc_tables[lab_table_idx]

            lab_table = LabTable()
            lab = lab_table.parse_table(table)
        
        if parameter_table_idx >=0:
            table = doc_tables[parameter_table_idx]
            try:
                parameter_table = ParameterTable(self.sbol_dictionary.get_strateos_mappings())
                parameter = parameter_table.parse_table(table)
                self.validation_errors.extend(parameter_table.get_validation_errors())
            except DictionaryMaintainerException as err:
                self.validation_errors.extend(err.get_message())
            
        self.request['name'] = title
        self.request['experiment_id'] = experiment_id
        self.request['challenge_problem'] = cp_id
        self.request['experiment_reference'] = experiment_reference
        self.request['experiment_reference_url'] = experiment_reference_url
        self.request['experiment_version'] = 1
        self.request['lab'] = lab
        self.request['runs'] = [{ 'measurements' : measurements}]
        self.request['doc_revision_id'] = self.lab_experiment.head_revision()
        if parameter:
            self.request['parameters'] = [parameter] 
    
    def _validate_schema(self):
        if self.request:
            try:
                schema = { '$ref' : 'https://schema.catalog.sd2e.org/schemas/structured_request.json' }
                validate(self.request, schema)
            except ValidationError as err:
                self.validation_errors.append(format(err).replace('\n', '&#13;&#10;'))

