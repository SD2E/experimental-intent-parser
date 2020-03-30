from datacatalog.formats.common import map_experiment_reference
from google_accessor import GoogleAccessor
from intent_parser_exceptions import ConnectionException
from jsonschema import validate
from jsonschema import ValidationError
from lab_table import LabTable
from measurement_table import MeasurementTable
from parameter_table import ParameterTable
import intent_parser_utils
import table_utils
import traceback

class IntentParser(object):
    '''
    Processes information from a Google Doc to:
        - link information to/from a SynBioHub data repository
        - generate and validate a structure request
    '''
    _request = {} 
    _validation_errors = []
    _validation_warnings = []

    def __init__(self, document_id, spreadsheet_id, datacatalog_config):
        self._document_id = document_id
        self.google_accessor = GoogleAccessor.create()
        self.google_accessor.set_spreadsheet_id(spreadsheet_id)
        self.datacatalog_config = datacatalog_config

       
    def process(self):
        self.internal_generate_request()
        self._validate_schema()
        
    def generate_report(self):
        try:
            doc = self.google_accessor.get_document(document_id=self._document_id)
        except Exception as ex:
            self.logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
            raise ConnectionException('404', 'Not Found',
                                      'Failed to access document ' +
                                      self._document_id)

        text_runs = intent_parser_utils.get_element_type(doc, 'textRun')
        text_runs = list(filter(lambda x: 'textStyle' in x,
                                text_runs))
        text_runs = list(filter(lambda x: 'link' in x['textStyle'],
                                text_runs))
        links_info = list(map(lambda x: (x['content'],
                                         x['textStyle']['link']),
                              text_runs))

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
                if url_host not in self.sbh_link_hosts:
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
        report['experiment_reference_url'] = \
            'https://docs.google.com/document/d/' + self._document_id
        report['labs'] = []

        report['mapped_names'] = mapped_names
        return report
        
    def get_structured_request(self):
        return self._request
    
    def get_validation_errors(self):
        return self._validation_errors
    
    def get_validation_warnings(self):
        return self._validation_warnings
    
    def internal_generate_request(self):
        """
        Generates a structured request for a given doc id
        """

        try:
            doc = self.google_accessor.get_document(document_id=self._document_id)
        except Exception as ex:
            self.logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
            raise ConnectionException('404', 'Not Found','Failed to access document ' + self._document_id)

        output_doc = { "experiment_reference_url" : "https://docs.google.com/document/d/%s" % self._document_id }
        if self.datacatalog_config['mongodb']['authn']:
            try:
                map_experiment_reference(self.datacatalog_config, output_doc)
            except:
                pass # We don't need to do anything, failure is handled later, but we don't want it to crash

        lab = 'Unknown'

        experiment_id = 'experiment.tacc.TBD'

        if 'challenge_problem' in output_doc and 'experiment_reference' in output_doc and 'experiment_reference_url' in output_doc:
            cp_id = output_doc['challenge_problem']
            experiment_reference = output_doc['experiment_reference']
            experiment_reference_url = output_doc['experiment_reference_url']
        else:
            self.logger.info('WARNING: Failed to map experiment reference for doc id %s!' % self._document_id)
            titleToks = doc['title'].split(sep='-')
            if len(titleToks) > 1:
                experiment_reference = doc['title'].split(sep='-')[1].strip()
            else:
                experiment_reference = doc['title']
            experiment_reference_url = 'https://docs.google.com/document/d/' + self._document_id
            # This will return a parent list, which should have one or more Ids of parent directories
            # We want to navigate those and see if they are a close match to a challenge problem ID
            parent_list = self.google_accessor.get_document_parents(document_id=self._document_id)
            cp_id = 'Unknown'
            if not parent_list['kind'] == 'drive#parentList':
                self.logger.info('ERROR: expected a drive#parent_list, received a %s' % parent_list['kind'])
            else:
                for parent_ref in parent_list['items']:
                    if not parent_ref['kind'] == 'drive#parentReference':
                        continue
                    parent_meta = self.google_accessor.get_document_metadata(document_id=parent_ref['id'])
                    new_cp_id = self.get_challenge_problem_id(parent_meta['title'])
                    if new_cp_id is not None:
                        cp_id = new_cp_id

        measurements = []
        parameter = []

        doc_tables = intent_parser_utils.get_element_type(doc, 'table')
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
            meas_table = MeasurementTable(self.temp_units, self.time_units, self.fluid_units, self.measurement_types, self.file_types)
            measurements = meas_table.parse_table(table)
            self._validation_errors.extend(meas_table.get_validation_errors())

        if lab_table_idx >= 0:
            table = doc_tables[lab_table_idx]

            lab_table = LabTable()
            lab = lab_table.parse_table(table)
        
        if parameter_table_idx >=0:
            table = doc_tables[parameter_table_idx]
            parameter_table = ParameterTable(self.strateos_mapping)
            parameter = parameter_table.parse_table(table)
            self._validation_errors.extend(parameter_table.get_validation_errors())
            
        self._request['name'] = doc['title']
        self._request['experiment_id'] = experiment_id
        self._request['challenge_problem'] = cp_id
        self._request['experiment_reference'] = experiment_reference
        self._request['experiment_reference_url'] = experiment_reference_url
        self._request['experiment_version'] = 1
        self._request['lab'] = lab
        self._request['runs'] = [{ 'measurements' : measurements}]
            
        if parameter:
            self._request['parameters'] = [parameter] 
    
    def _validate_schema(self):
        if self._request:
            try:
                schema = { '$ref' : 'https://schema.catalog.sd2e.org/schemas/structured_request.json' }
                validate(self._request, schema)
                
                reagent_with_no_uri = intent_parser_utils.get_reagent_with_no_uri(self._request)
                for reagent in reagent_with_no_uri:
                    self._validation_warnings.append('%s does not have a SynbioHub URI specified!&#13;&#10;' % reagent) 
            except ValidationError as err:
                self._validation_errors.append('Schema Validation Error: {0}\n'.format(err).replace('\n', '&#13;&#10;'))

    