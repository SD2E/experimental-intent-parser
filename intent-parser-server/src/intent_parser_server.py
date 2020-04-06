from datacatalog.formats.common import map_experiment_reference
from datetime import datetime
from google_accessor import GoogleAccessor
from intent_parser_exceptions import ConnectionException
from intent_parser_sbh import IntentParserSBH
from jsonschema import validate
from jsonschema import ValidationError
from lab_table import LabTable
from measurement_table import MeasurementTable
from multiprocessing import Pool
from operator import itemgetter
from parameter_table import ParameterTable
from sbh_accessor import SBHAccessor
from sbol_dictionary_accessor import SBOLDictionaryAccessor
from socket_manager import SocketManager
from spellchecker import SpellChecker
import constants
import getopt
import http_message;
import inspect
import intent_parser_utils
import json
import logging.config
import numpy as np
import os
import re
import sbol
import signal
import socket
import sys
import table_utils
import threading
import time
import traceback
import urllib.request

class IntentParserServer:

    # Used for inserting experiment result data
    # Since the experiment result data is uploaded with the requesting document id
    # and the test documents are copies of those, the ids won't match
    # In order to test this, if we receive a document Id in the key of this map, we will instead query for the value
    test_doc_id_map = {'1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoT' : '10HqgtfVCtYhk3kxIvQcwljIUonSNlSiLBC8UFmlwm1s',
                       '1RenmUdhsXMgk4OUWReI2oS6iF5R5rfWU5t7vJ0NZOHw': '1g0SjxU2Y5aOhUbM63r8lqV50vnwzFDpJg4eLXNllut4',
                       '1_I4pxB26zOLb209Xlv8QDJuxiPWGDafrejRDKvZtEl8': '1K5IzBAIkXqJ7iPF4OZYJR7xgSts1PUtWWM2F0DKhct0',
                       '1zf9l0K4rj7I08ZRpxV2ZY54RMMQc15Rlg7ULviJ7SBQ': '1uXqsmRLeVYkYJHqgdaecmN_sQZ2Tj4Ck1SZKcp55yEQ' }

    dict_path = 'dictionaries'

    link_pref_path = 'link_pref'

    lab_ids_list = sorted(['BioFAB UID',
                            'Ginkgo UID',
                            'Transcriptic UID',
                            'LBNL UID',
                            'EmeraldCloud UID',
                            'CalTech UID',
                            'PennState (Salis) UID'])

    item_types = {
            'component': {
                'Bead'     : 'http://purl.obolibrary.org/obo/NCIT_C70671',
                'CHEBI'    : 'http://identifiers.org/chebi/CHEBI:24431',
                'DNA'      : 'http://www.biopax.org/release/biopax-level3.owl#DnaRegion',
                'Protein'  : 'http://www.biopax.org/release/biopax-level3.owl#Protein',
                'RNA'      : 'http://www.biopax.org/release/biopax-level3.owl#RnaRegion'
            },
            'module': {
                'Strain'   : 'http://purl.obolibrary.org/obo/NCIT_C14419',
                'Media'    : 'http://purl.obolibrary.org/obo/NCIT_C85504',
                'Stain'    : 'http://purl.obolibrary.org/obo/NCIT_C841',
                'Buffer'   : 'http://purl.obolibrary.org/obo/NCIT_C70815',
                'Solution' : 'http://purl.obolibrary.org/obo/NCIT_C70830'
            },
            'collection': {
                'Challenge Problem' : '',
                'Collection' : ''
            },
            'external': {
                'Attribute' : ''
            }
        }

    logger = logging.getLogger('intent_parser_server')

    # Define the percentage of length of the search term that must
    # be matched in order to have a valid partial match
    partial_match_thresh = 0.75

    # Terms below a certain size should be force to have an exact match
    partial_match_min_size = 3

    # How many results we allow
    sparql_limit = 5

    # Defines how many processes are in the pool, for parallelism
    multiprocessing_pool_size = 8

    # Defines a period of time to wait to send analyze progress updates, in seconds
    analyze_progress_period = 2.5

    # Determine how long a lab UID string has to be in order to be added to the item map.
    # Strings below this size are ignored.
    uid_length_threshold = 3

    # Some lab UIDs are short but still valid.  This defines an exceptions to the length threshold.
    uid_length_exception = ['M9', 'LB']

    def __init__(self, bind_port=8081, bind_ip="0.0.0.0",
                 sbh_collection_uri=None,
                 sbh_spoofing_prefix=None,
                 spreadsheet_id=None,
                 sbh_username=None, sbh_password=None,
                 item_map_cache=True,
                 sbh_link_hosts=['hub-staging.sd2e.org',
                                 'hub.sd2e.org'],
                 datacatalog_authn='',
                 init_server=True,
                 init_sbh=True):

        fh = logging.FileHandler('intent_parser_server.log')
        self.logger.addHandler(fh)
        
        self.sbh = None
        self.server = None
        self.shutdownThread = False
        self.event = threading.Event()
        self.curr_running_threads = {}
        self.client_thread_lock = threading.Lock()
        
        self.my_path = os.path.dirname(os.path.realpath(__file__))

        f = open(self.my_path + '/create_measurements_table.html', 'r')
        self.create_measurements_table_html = f.read()
        f.close()

        f = open(self.my_path + '/add.html', 'r')
        self.add_html = f.read()
        f.close()

        f = open(self.my_path + '/analyze_sidebar.html', 'r')
        self.analyze_html = f.read()
        f.close()

        f = open(self.my_path + '/findSimilar.sparql', 'r')
        self.sparql_similar_query = f.read()
        f.close()

        f = open(self.my_path + '/findSimilarCount.sparql', 'r')
        self.sparql_similar_count = f.read()
        f.close()

        self.sparql_similar_count_cache = {}

        self.datacatalog_config = { "mongodb" : { "database" : "catalog_staging", "authn" : datacatalog_authn } }

        if init_sbh:
            self.initialize_sbh(sbh_collection_uri=sbh_collection_uri,
                 sbh_spoofing_prefix=sbh_spoofing_prefix,
                 spreadsheet_id=spreadsheet_id,
                 item_map_cache=item_map_cache,
                 sbh_username=sbh_username, sbh_password=sbh_password,
                 sbh_link_hosts=sbh_link_hosts)

        if init_server:
            self.initialize_server(bind_port=bind_port, bind_ip=bind_ip)

        self.spellCheckers = {}

        if not os.path.exists(self.dict_path):
            os.makedirs(self.dict_path)

        if not os.path.exists(self.link_pref_path):
            os.makedirs(self.link_pref_path)

        # Dictionary per-user that stores analyze associations to ignore
        self.analyze_never_link = {}

        self.cache_json_data()

    def initialize_sbh(self, *,
                 sbh_collection_uri,
                 spreadsheet_id,
                 sbh_spoofing_prefix=None,
                 sbh_username=None, sbh_password=None,
                 item_map_cache=True,
                 sbh_link_hosts=['hub-staging.sd2e.org',
                                 'hub.sd2e.org']):
        """
        Initialize the connection to SynbioHub.
        """

        if sbh_collection_uri[:8] == 'https://':
            sbh_url_protocol = 'https://'
            sbh_collection_path = sbh_collection_uri[8:]

        elif sbh_collection_uri[:7] == 'http://':
            sbh_url_protocol = 'http://'
            sbh_collection_path = sbh_collection_uri[7:]

        else:
            raise Exception('Invalid collection url: ' + sbh_collection_uri)

        sbh_collection_path_parts = sbh_collection_path.split('/')
        if len(sbh_collection_path_parts) != 6:
            raise Exception('Invalid collection url: ' + sbh_collection_uri)

        sbh_collection = sbh_collection_path_parts[3]
        sbh_collection_user = sbh_collection_path_parts[2]
        sbh_collection_version = sbh_collection_path_parts[5]
        sbh_url = sbh_url_protocol + sbh_collection_path_parts[0]

        if sbh_collection_path_parts[4] != (sbh_collection + '_collection'):
            raise Exception('Invalid collection url: ' + sbh_collection_uri)

        self.sbh = None
        if sbh_url is not None:
            # log into Syn Bio Hub
            if sbh_username is None:
                self.logger.info('SynBioHub username was not specified')
                usage()
                sys.exit(2)

            if sbh_password is None:
                self.logger.info('SynBioHub password was not specified')
                usage()
                sys.exit(2)

            self.sbh = SBHAccessor(sbh_url=sbh_url)
            self.sbh_collection = sbh_collection
            self.sbh_collection_user = sbh_collection_user
            self.sbh_spoofing_prefix = sbh_spoofing_prefix
            self.sbh_url = sbh_url
            self.sbh_link_hosts = sbh_link_hosts

            if sbh_spoofing_prefix is not None:
                self.sbh.spoof(sbh_spoofing_prefix)
                self.sbh_collection_uri = sbh_spoofing_prefix \
                    + '/user/' + sbh_collection_user \
                    + '/' + sbh_collection + '/' \
                    + sbh_collection + '_collection/' \
                    + sbh_collection_version
            else:
                self.sbh_collection_uri = sbh_url + '/'
                self.sbh_collection_uri = sbh_url \
                    + '/user/' + sbh_collection_user \
                    + '/' + sbh_collection + '/' \
                    + sbh_collection + '_collection/' \
                    + sbh_collection_version

            self.sbh_uri_prefix = sbh_url \
                + '/user/' + sbh_collection_user \
                + '/' + sbh_collection + '/'

        self.google_accessor = GoogleAccessor.create()
        self.spreadsheet_id = spreadsheet_id
        self.google_accessor.set_spreadsheet_id(self.spreadsheet_id)
        self.spreadsheet_tabs = self.google_accessor.type_tabs.keys()

        self.analyze_processing_map = {}
        self.analyze_processing_map_lock = threading.Lock() # Used to lock the map
        self.analyze_processing_lock = {} # Used to indicate if the processing thread has finished, mapped to each doc_id
        self.client_state_map = {}
        self.client_state_lock = threading.Lock()
        self.item_map_lock = threading.Lock()
        self.item_map_lock.acquire()
        self.item_map = self.generate_item_map(use_cache=item_map_cache)
        sbol_dictionary = SBOLDictionaryAccessor(self.spreadsheet_id, self.sbh)
        self.strateos_mapping = sbol_dictionary.get_strateos_mappings()
        self.item_map_lock.release()
        
        # Inverse map of typeTabs
        self.type2tab = {}
        for tab_name in self.google_accessor.type_tabs.keys():
            for type_name in self.google_accessor.type_tabs[tab_name]:
                self.type2tab[type_name] = tab_name

        if self.sbh is not None:
            self.sbh.login(sbh_username, sbh_password)
            self.logger.info('Logged into {}'.format(sbh_url))

        self.housekeeping_thread = \
            threading.Thread(target=self.housekeeping)
        self.housekeeping_thread.start()

    def initialize_server(self, *, bind_port=8081, bind_ip="0.0.0.0"):
        """
        Initialize the server.
        """
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.server.bind((bind_ip, bind_port))

        self.server.listen(5)
        self.logger.info('listening on {}:{}'.format(bind_ip, bind_port))

    def serverRunLoop(self, *, background=False):
        if background:
            run_thread = threading.Thread(target=self.serverRunLoop)
            self.logger.info('Start background thread')
            run_thread.start()
            return

        self.logger.info('Start Listener')

        while True:
            try:
                if self.shutdownThread:
                    return

                client_sock, __ = self.server.accept()
            except ConnectionAbortedError:
                # Shutting down
                return
            except OSError:
                # Shutting down
                return
            except InterruptedError:
                # Received when server is shutting down
                return
            except Exception as e:
                raise e
            
            if self.shutdownThread:
                    return
            
            
            client_handler = threading.Thread(
                target=self.handle_client_connection,
                args=(client_sock,)  # without comma you'd get a... TypeError: handle_client_connection() argument after * must be a sequence, not _socketobject
            )
            client_handler.start()
            
            self.client_thread_lock.acquire()
            self.curr_running_threads[client_handler.ident] = client_handler
            self.client_thread_lock.release()
            
    def handle_client_connection(self, client_socket):
        self.logger.info('Connection')
        sm = SocketManager(client_socket)

        try:
            while True:
                httpMessage = http_message.HttpMessage(sm)

                if httpMessage.get_state() == http_message.State.ERROR:
                    client_socket.close()
                    return

                method = httpMessage.get_method()

                try:
                    if method == 'POST':
                        self.handlePOST(httpMessage, sm)
                    elif method == 'GET':
                        self.handleGET(httpMessage, sm)
                    else:
                        self.send_response(501, 'Not Implemented', 'Unrecognized request method\n',
                                           sm)

                except ConnectionException as ex:
                    self.send_response(ex.code, ex.message, ex.content, sm)

                except Exception as ex:
                    self.logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
                    self.send_response(504, 'Internal Server Error', 'Internal Server Error\n', sm)

        except Exception as e:
            self.logger.info('Exception: {}'.format(e))

        client_socket.close()
        client_socket.shutdown(socket.SHUT_RDWR)
        

    def send_response(self, code, message, content, sm, content_type='text/html'):
            response = http_message.HttpMessage()
            response.set_response_code(code, message)
            response.set_header('content-type', content_type)
            response.set_body(content.encode('utf-8'))
            response.send(sm)

    def handlePOST(self, httpMessage, sm):
        resource = httpMessage.get_resource()

        if resource == '/analyzeDocument':
            self.process_analyze_document(httpMessage, sm)
        elif resource == '/updateExperimentalResults':
            self.process_update_exp_results(httpMessage, sm)
        elif resource == '/calculateSamples':
            self.process_calculate_samples(httpMessage, sm)
        elif resource == '/message':
            self.process_message(httpMessage, sm)
        elif resource == '/buttonClick':
            self.process_button_click(httpMessage, sm)
        elif resource == '/addToSynBioHub':
            self.process_add_to_syn_bio_hub(httpMessage, sm)
        elif resource == '/addBySpelling':
            self.process_add_by_spelling(httpMessage, sm)
        elif resource == '/searchSynBioHub':
            self.process_search_syn_bio_hub(httpMessage, sm)
        elif resource == '/submitForm':
            self.process_submit_form(httpMessage, sm)
        elif resource == '/createTableTemplate':
            self.process_create_table_template(httpMessage, sm)
        elif resource == '/validateStructuredRequest':
            self.process_validate_structured_request(httpMessage, sm)
        elif resource == '/generateStructuredRequest':
            self.process_validate_and_generate_structured_request(httpMessage, sm)
        elif resource == '/createParameterTable':
            self.process_submit_form(httpMessage, sm)
        else:
            self.send_response(404, 'Not Found', 'Resource Not Found\n', sm)

    def get_json_body(self, httpMessage):
        body = httpMessage.get_body()
        if body == None or len(body) == 0:
            errorMessage = 'No POST data\n'
            raise ConnectionException(400, 'Bad Request', errorMessage)

        bodyStr = body.decode('utf-8')

        try:
            return json.loads(bodyStr)
        except json.decoder.JSONDecodeError as e:
            errorMessage = 'Failed to decode JSON data: {}\n'.format(e);
            raise ConnectionException(400, 'Bad Request', errorMessage)

    def process_button_click(self, httpMessage, sm):
        (json_body, client_state) = self.get_client_state(httpMessage)

        if 'data' not in json_body:
            errorMessage = 'Missing data'
            raise ConnectionException(400, 'Bad Request', errorMessage)
        data = json_body['data']

        if 'buttonId' not in data:
            errorMessage = 'data missing buttonId'
            raise ConnectionException(400, 'Bad Request', errorMessage)
        if type(data['buttonId']) is dict:
            buttonDat = data['buttonId']
            buttonId = buttonDat['buttonId']
        else:
            buttonId = data['buttonId']

        method = getattr( self, buttonId )

        try:
            actionList = method(json_body, client_state)
            actions = {'actions': actionList}
            self.send_response(200, 'OK', json.dumps(actions), sm,
                               'application/json')
        except Exception as e:
            raise e
        finally:
            self.release_connection(client_state)

    def process_calculate_samples(self, httpMessage, sm):
        """
        Find all measurements tables and update the samples columns, or add the samples column if it doesn't exist.
        """
        start = time.time()

        json_body = self.get_json_body(httpMessage)
        document_id = json_body['documentId']
        try:
            doc = self.google_accessor.get_document(document_id=document_id)
        except Exception as ex:
            self.logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
            raise ConnectionException('404', 'Not Found','Failed to access document ' + document_id)

        doc_tables = self.get_element_type(doc, 'table')
        table_ids = []
        sample_indices = []
        samples_values = []
        for tIdx in range(len(doc_tables)):
            table = doc_tables[tIdx]

            # Only process new style measurement tables
            is_new_measurement_table = table_utils.detect_new_measurement_table(table)
            if not is_new_measurement_table:
                continue

            rows = table['tableRows']
            headerRow = rows[0]
            samples_col = -1
            for cell_idx in range(len(headerRow['tableCells'])):
                cellTxt = intent_parser_utils.get_paragraph_text(headerRow['tableCells'][cell_idx]['content'][0]['paragraph']).strip()
                if cellTxt == constants.COL_HEADER_SAMPLES:
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
                    if headerTxt == constants.COL_HEADER_MEASUREMENT_TYPE:
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
                    if headerTxt == constants.COL_HEADER_MEASUREMENT_TYPE or headerTxt == constants.COL_HEADER_NOTES or headerTxt == constants.COL_HEADER_SAMPLES:
                        colIdx += 1
                        continue

                    cellContent = row['tableCells'][colIdx]['content']
                    cellTxt = ' '.join([intent_parser_utils.get_paragraph_text(c['paragraph']).strip() for c in cellContent]).strip()

                    if headerTxt == constants.COL_HEADER_REPLICATE:
                        comp_count.append(int(cellTxt))
                    else:
                        comp_count.append(len(cellTxt.split(sep=',')))
                    colIdx += 1
                samples.append(int(np.prod(comp_count)))

            table_ids.append(tIdx)
            sample_indices.append(samples_col)
            samples_values.append(samples)

        action = {}
        action['action'] = 'calculateSamples'
        action['tableIds'] = table_ids
        action['sampleIndices'] = sample_indices
        action['sampleValues'] = samples_values

        actions = {'actions': [action]}

        end = time.time()
        self.logger.info('Calculated samples in %0.2fms, %s, %s' %((end - start) * 1000, document_id, time.time()))

        self.send_response(200, 'OK', json.dumps(actions), sm, 'application/json')

    
    def process_validate_structured_request(self, httpMessage, sm):
        '''
        Generate a structured request from a given document, then run it against the validation.
        '''
        json_body = self.get_json_body(httpMessage)
        result = 'Passed!'
        msg = ''
        if json_body is None:
            result = 'Failed!'
            msg = 'Unable to get information from Google document.'
        else:
            document_id = json_body['documentId']
            result, msg = self._internal_validate_request(document_id)
        
        text_area_rows = 33
        height = 600
        if result == 'Passed!':
            height = 300
            text_area_rows = 15
        elif result == 'Failed!':
            height = 600
            
        msg = "<textarea cols='80' rows='%d'> %s </textarea>" % (text_area_rows, msg)
        buttons = [('Ok', 'process_nop')]
        dialog_action = self.simple_modal_dialog(msg, buttons, 'Structured request validation: %s' % result, 500, height)
        actionList = [dialog_action]
        actions = {'actions': actionList}
        self.send_response(200, 'OK', json.dumps(actions), sm, 'application/json')
    
    def _internal_validate_request(self, document_id):
        request, errors = self.internal_generate_request(document_id)
        result = 'Passed!'
        msg = 'Validation Passed!&#13;&#10;'
            
        try:
            schema = { "$ref" : "https://schema.catalog.sd2e.org/schemas/structured_request.json" }
            validate(request, schema)
            
            reagent_with_no_uri = intent_parser_utils.get_reagent_with_no_uri(request)
            for reagent in reagent_with_no_uri:
                msg += 'Warning: %s does not have a SynbioHub URI specified!&#13;&#10;' % reagent
            
            if len(errors) > 0:
                msg = 'The provided structured request is faulty. Invalid information will be ignored.\n'
                msg += '\n'.join(errors)
                result = 'Failed!'  
            else:      
                result = 'Passed!'
            
        except ValidationError as err:
            msg = 'Validation Failed!\n'
            msg += 'Schema Validation Error: {0}\n'.format(err).replace('\n', '&#13;&#10;')
            result = 'Failed!'
    
        return result, msg
    
    def internal_generate_request(self, document_id):
        """
        Generates a structured request for a given doc id
        """

        try:
            doc = self.google_accessor.get_document(document_id=document_id)
        except Exception as ex:
            self.logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
            raise ConnectionException('404', 'Not Found','Failed to access document ' + document_id)

        output_doc = { "experiment_reference_url" : "https://docs.google.com/document/d/%s" % document_id }
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
            self.logger.info('WARNING: Failed to map experiment reference for doc id %s!' % document_id)
            titleToks = doc['title'].split(sep='-')
            if len(titleToks) > 1:
                experiment_reference = doc['title'].split(sep='-')[1].strip()
            else:
                experiment_reference = doc['title']
            experiment_reference_url = 'https://docs.google.com/document/d/' + document_id
            # This will return a parent list, which should have one or more Ids of parent directories
            # We want to navigate those and see if they are a close match to a challenge problem ID
            parent_list = self.google_accessor.get_document_parents(document_id=document_id)
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
        errors = []
        doc_tables = self.get_element_type(doc, 'table')
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
            errors = errors + meas_table.get_validation_errors()

        if lab_table_idx >= 0:
            table = doc_tables[lab_table_idx]

            lab_table = LabTable()
            lab = lab_table.parse_table(table)
        
        if parameter_table_idx >=0:
            table = doc_tables[parameter_table_idx]
            parameter_table = ParameterTable(self.strateos_mapping)
            parameter = parameter_table.parse_table(table)
            errors = errors + parameter_table.get_validation_errors()
            
        request = {}
        request['name'] = doc['title']
        request['experiment_id'] = experiment_id
        request['challenge_problem'] = cp_id
        request['experiment_reference'] = experiment_reference
        request['experiment_reference_url'] = experiment_reference_url
        request['experiment_version'] = 1
        request['lab'] = lab
        request['runs'] = [{ 'measurements' : measurements}]
            
        if parameter:
            request['parameters'] = [parameter] 

        return request, errors
    
             
    
    def process_validate_and_generate_structured_request(self, httpMessage, sm):
        '''
        Validates then generates an HTML link to retrieve a structured request.
        '''
        stuctured_request_link = ''
        result = 'Passed!'
        text_area_rows = 33
        height = 600
        json_body = self.get_json_body(httpMessage)
        http_host = httpMessage.get_header('Host')
        if json_body is None or http_host is None:
            result = 'Failed!'
            msg = 'Unable to get information from Google document.'
        else:
            document_id = json_body['documentId']
            result, msg = self._internal_validate_request(document_id)
            stuctured_request_link += 'Download Structured Request '
            stuctured_request_link += '<a href=http://' + http_host + '/document_request?' + document_id + ' target=_blank>here</a> \n\n'
        
        if result == 'Passed!':
            height = 300
            text_area_rows = 15
        elif result == 'Failed!':
            height = 600
       
        if stuctured_request_link:
            msg = stuctured_request_link + "<textarea cols='80' rows='%d'> %s </textarea>" % (text_area_rows, msg)
        else:
            msg = "<textarea cols='80' rows='%d'> %s </textarea>" % (text_area_rows, msg)
            
        buttons = [('Ok', 'process_nop')]
        dialog_action = self.simple_modal_dialog(msg, buttons, 'Structured request validation: %s' % result, 500, height)
        actionList = [dialog_action]
        actions = {'actions': actionList}
        self.send_response(200, 'OK', json.dumps(actions), sm, 'application/json')
        
    
    def process_generate_request(self, httpMessage, sm):
        """
        Handles a request to generate a structured request json
        """
        start = time.time()

        resource = httpMessage.get_resource()
        document_id = resource.split('?')[1]
        request, errors = self.internal_generate_request(document_id)
        
        end = time.time()

        self.logger.info('Generated request in %0.2fms, %s, %s' %((end - start) * 1000, document_id, time.time()))

        self.send_response(200, 'OK', json.dumps(request), sm, 'application/json')


    def process_generate_report(self, httpMessage, sm):
        """
        Handles a request to generate a report
        """
        resource = httpMessage.get_resource()
        document_id = resource.split('?')[1]
        #client_state = {}

        start = time.time()

        try:
            doc = self.google_accessor.get_document(
                document_id=document_id
                )
        except Exception as ex:
            self.logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
            raise ConnectionException('404', 'Not Found',
                                      'Failed to access document ' +
                                      document_id)

        text_runs = self.get_element_type(doc, 'textRun')
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

        #client_state = {}
        #client_state['doc'] = doc
        #client_state['document_id'] = document_id
        #client_state['user_id'] = userId
        #self.analyze_document(client_state, doc, 0)

        report = {}
        report['challenge_problem_id'] = 'undefined'
        report['experiment_reference_url'] = \
            'https://docs.google.com/document/d/' + document_id
        report['labs'] = []

        report['mapped_names'] = mapped_names

        end = time.time()

        self.logger.info('Generated report in %0.2fms, %s, %s' %((end - start) * 1000, document_id, time.time()))

        self.send_response(200, 'OK', json.dumps(report), sm,
                           'application/json')

    def process_message(self, httpMessage, sm):
        json_body = self.get_json_body(httpMessage)
        if 'message' in json_body:
            self.logger.info(json_body['message'])
        self.send_response(200, 'OK', '{}', sm,
                           'application/json')


    def get_client_state(self, httpMessage):
        json_body = self.get_json_body(httpMessage)

        if 'documentId' not in json_body:
            raise ConnectionException('400', 'Bad Request',
                                      'Missing documentId')
        document_id = json_body['documentId']

        try:
            client_state = self.get_connection(document_id)
        except:
            client_state = None

        return (json_body, client_state)


    def process_update_exp_results(self, httpMessage, sm):
        """
        This function will scan SynbioHub for experiments related to this document, and updated an
        "Experiment Results" section with information about completed experiments.
        """
        start = time.time()

        json_body = self.get_json_body(httpMessage)

        if 'documentId' not in json_body:
            raise ConnectionException('400', 'Bad Request', 'Missing documentId')

        document_id = json_body['documentId']

        try:
            doc = self.google_accessor.get_document(document_id=document_id)
        except Exception as ex:
            self.logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
            raise ConnectionException('404', 'Not Found', 'Failed to access document ' + document_id)

        # For test documents, replace doc id with corresponding production doc
        if document_id in self.test_doc_id_map:
            source_doc_uri = 'https://docs.google.com/document/d/' + self.test_doc_id_map[document_id]
        else:
            source_doc_uri = 'https://docs.google.com/document/d/' + document_id

        # Search SBH to get data
        target_collection = self.sbh_url + '/user/%s/experiment_test/experiment_test_collection/1' % self.sbh_collection_user
        intent_parser_sbh = IntentParserSBH()
       
        exp_collection = intent_parser_sbh.query_experiments(self.sbh, target_collection, self.sbh_spoofing_prefix, self.sbh_url)
        data = {}
        for exp in exp_collection:
            exp_uri = exp['uri']
            timestamp = exp['timestamp']
            title = exp['title']
            request_doc = intent_parser_sbh.query_experiment_request(self.sbh, exp_uri, self.sbh_spoofing_prefix, self.sbh_url)  # Get the reference to the Google request doc
            if source_doc_uri == request_doc:
                source_uri = intent_parser_sbh.query_experiment_source(self.sbh, exp_uri, self.sbh_spoofing_prefix, self.sbh_url)  # Get the reference to the source document with lab data
                data[exp_uri] = {'timestamp' : timestamp, 'agave' : source_uri[0], 'title' : title}

        #data = self.get_synbiohub_exp_data(document_id)
        #data = {'exp1' : '6/30/2019', 'exp2' : '7/30/2019', 'exp3' : '8/30/2019', 'exp4' : '9/30/2019'}

        exp_data = []
        exp_links = []
        for exp in data:
            exp_data.append((data[exp]['title'], ' updated on ', data[exp]['timestamp'], ', ', 'Agave link', '\n'))
            exp_links.append((exp, '', '', '',  data[exp]['agave'], ''))

        if exp_data == '':
            exp_data = ['No currently run experiments.']

        body = doc.get('body');
        doc_content = body.get('content')
        paragraphs = self.get_paragraphs(doc_content)

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

        action = {}
        action['action'] = 'updateExperimentResults'
        action['headerIdx'] = headerIdx
        action['contentIdx'] = contentIdx
        action['expData'] = exp_data
        action['expLinks'] = exp_links

        actions = {'actions': [action]}

        end = time.time()
        self.logger.info('Updated experiment results in %0.2fms, %s, %s' %((end - start) * 1000, document_id, time.time()))

        self.send_response(200, 'OK', json.dumps(actions), sm, 'application/json')

    def process_analyze_document(self, httpMessage, sm):
        """
        This function will initiate an analysis if the document isn't currently being analyzed and
        then it will report on the progress of that document's analysis until it is done.  Once it's done
        this function will notify the client that the document is ready.
        """
        json_body = self.get_json_body(httpMessage)

        if 'documentId' not in json_body:
            raise ConnectionException('400', 'Bad Request',
                                      'Missing documentId')
        document_id = json_body['documentId']

        self.analyze_processing_map_lock.acquire()
        docBeingProcessed = document_id in self.analyze_processing_map
        self.analyze_processing_map_lock.release()

        if docBeingProcessed: # Doc being processed, check progress
            time.sleep(self.analyze_progress_period)

            self.analyze_processing_map_lock.acquire()
            progress_percent = self.analyze_processing_map[document_id]
            self.analyze_processing_map_lock.release()

            if progress_percent < 100: # Not done yet, update client
                action = {}
                action['action'] = 'updateProgress'
                action['progress'] = str(int(progress_percent * 100))
                actions = {'actions': [action]}
                self.send_response(200, 'OK', json.dumps(actions), sm, 'application/json')
            else: # Document is analyzed, start navigating results
                try:
                    self.analyze_processing_lock[document_id].acquire() # This ensures we've waited for the processing thread to release the client connection
                    (__, client_state) = self.get_client_state(httpMessage)
                    actionList = self.report_search_results(client_state)
                    actions = {'actions': actionList}
                    self.send_response(200, 'OK', json.dumps(actions), sm, 'application/json')
                finally:
                    self.analyze_processing_map.pop(document_id)
                    self.analyze_processing_lock[document_id].release()
                    self.release_connection(client_state)
        else: # Doc not being processed, spawn new processing thread
            self.analyze_processing_map[document_id] = 0
            analyze_thread = threading.Thread(
                target=self.process_analyze_document_thread,
                args=(httpMessage,)  # without comma you'd get a... TypeError
            )
            analyze_thread.start()
            dialogAction = self.progress_sidebar_dialog()
            actions = {'actions': [dialogAction]}
            self.send_response(200, 'OK', json.dumps(actions), sm, 'application/json')

    def process_analyze_document_thread(self, httpMessage):
        """
        This function does the actual work of analyzing the document, and is designed to be run in a separate thread.
        This will process the document and update a status container.  The client will keep pinging the server for status
        while the document is being analyzed and the server will either return the progress percentage, or indicate that the
        results are ready.
        """

        start = time.time()
        json_body = self.get_json_body(httpMessage)

        if 'documentId' not in json_body:
            raise ConnectionException('400', 'Bad Request', 'Missing documentId')
        document_id = json_body['documentId']

        try:
            doc = self.google_accessor.get_document(document_id=document_id)
        except Exception as ex:
            self.logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
            raise ConnectionException('404', 'Not Found', 'Failed to access document ' + document_id)

        self.analyze_processing_lock[document_id] = threading.Lock()
        self.analyze_processing_lock[document_id].acquire()

        user = json_body['user']
        userEmail = json_body['userEmail']

        if not userEmail is '':
            userId = userEmail
        elif user:
            userId = user
        else:
            userId = document_id

        client_state = self.new_connection(document_id)
        client_state['doc'] = doc
        client_state['user_id'] = userId

        if 'data' in json_body:
            body = doc.get('body');
            doc_content = body.get('content')
            paragraphs = self.get_paragraphs(doc_content)

            data = json_body['data']
            paragraph_index = data['paragraphIndex']
            offset = data['offset']
            paragraph = paragraphs[ paragraph_index ]
            first_element = paragraph['elements'][0]
            paragraph_offset = first_element['startIndex']
            start_offset = paragraph_offset + offset
        else:
            start_offset = 0

        try:
            self.analyze_document(client_state, doc, start_offset)
            end = time.time()
            self.logger.info('Analyzed entire document in %0.2fms, %s, %s' %((end - start) * 1000, document_id, time.time()))
        except Exception as e:
            raise e

        finally:
            # Just in case analyze_document failed and didn't finish
            # this will prevent an endless wait
            self.analyze_processing_map_lock.acquire()
            self.analyze_processing_map[client_state['document_id']] = 100
            self.analyze_processing_map_lock.release()

            self.release_connection(client_state)
            self.analyze_processing_lock[document_id].release()

    def add_link(self, search_result, new_link=None):
        """
        """
        paragraph_index = search_result['paragraph_index']
        offset = search_result['offset']
        end_offset = search_result['end_offset']
        if new_link is None:
            link = search_result['uri']
        else:
            link = new_link
        search_result['link'] = link

        action = self.link_text(paragraph_index, offset,
                                end_offset, link)

        return [action]

    def report_search_results(self, client_state):
        """
        """
        while True:
            search_results = client_state['search_results']
            search_result_index = client_state['search_result_index']
            if search_result_index >= len(search_results):
                dialogAction = self.simple_sidebar_dialog('Finished Analyzing Document.', [])
                return [dialogAction]

            client_state['search_result_index'] += 1

            search_result = search_results[ search_result_index ]
            paragraph_index = search_result['paragraph_index']
            offset = search_result['offset']
            term = search_result['term']
            uri = search_result['uri']
            link = search_result['link']
            content_term = search_result['text']
            end_offset = search_result['end_offset']

            actions = []

            self.item_map_lock.acquire()
            item_map = self.item_map
            self.item_map_lock.release()

            if link is not None and link == item_map[term]:
                continue

            highlightTextAction = self.highlight_text(paragraph_index, offset,
                                                      end_offset)
            actions.append(highlightTextAction)

            buttons = [('Yes', 'process_analyze_yes', 'Creates a hyperlink for the highlighted text, using the suggested URL.'),
                       ('No', 'process_analyze_no', 'Skips this term without creating a link.'),
                       ('Yes to All', 'process_link_all', 'Creates a hyperlink for the highilghted text and every instance of it in the document, using the suggested URL.'),
                       ('No to All', 'process_no_to_all', 'Skips this term and every other instance of it in the document.'),
                       ('Never Link', 'process_never_link', 'Never suggest links to this term, in this document or any other.')]

            buttonHTML = ''
            buttonScript = ''
            for button in buttons:
                buttonHTML += '<input id=' + button[1] + 'Button value="'
                buttonHTML += button[0] + '" type="button" title="'
                buttonHTML += button[2] + '" onclick="'
                buttonHTML += button[1] + 'Click()" />\n'

                buttonScript += 'function ' + button[1] + 'Click() {\n'
                buttonScript += '  google.script.run.withSuccessHandler'
                buttonScript += '(onSuccess).buttonClick(\''
                buttonScript += button[1]  + '\')\n'
                buttonScript += '}\n\n'

            buttonHTML += '<input id=EnterLinkButton value="Manually Enter Link" type="button" title="Enter a link for this term manually." onclick="EnterLinkClick()" />'
            # Script for the EnterLinkButton is already in the HTML

            html = self.analyze_html

            # Update parameters in html
            html = html.replace('${SELECTEDTERM}', term)
            html = html.replace('${SELECTEDURI}', uri)
            html = html.replace('${CONTENT_TERM}', content_term)
            html = html.replace('${TERM_URI}', uri)
            html = html.replace('${DOCUMENTID}', client_state['document_id'])
            html = html.replace('${BUTTONS}', buttonHTML)
            html = html.replace('${BUTTONS_SCRIPT}', buttonScript)

            dialogAction = self.sidebar_dialog(html)

            actions.append(dialogAction)

            return actions

    def get_paragraphs(self, element):
        return self.get_element_type(element, 'paragraph')

    def get_element_type(self, element, element_type):
        elements = []
        if type(element) is dict:
            for key in element:
                if key == element_type:
                    elements.append(element[key])

                elements += self.get_element_type(element[key],
                                                  element_type)

        elif type(element) is list:
            for entry in element:
                elements += self.get_element_type(entry,
                                                  element_type)

        return elements

    def get_challenge_problem_id(self, text):
        """
        Find the closest matching measurement type to the given type, and return that as a string
        """
        # challenge problem ids have underscores, so replace spaces with underscores to make the inputs match better
        text = text.replace(' ', '_')
        best_match_type = None
        best_match_size = 0
        for cid in self.challenge_ids:
            matches = intent_parser_utils.find_common_substrings(text.lower(), cid.lower(), 1, 0)
            for m in matches:
                if m.size > best_match_size and m.size > int(0.25 * len(cid)):
                    best_match_type = cid
                    best_match_size = m.size
        return best_match_type

    def fetch_spreadsheet_data(self):
        tab_data = {}
        for tab in self.spreadsheet_tabs:
            tab_data[tab] = self.google_accessor.get_row_data(tab=tab)
            self.logger.info('Fetched data from tab ' + tab)

        return tab_data

    def analyze_document(self, client_state, doc, start_offset):
        self.analyze_processing_map_lock.acquire()
        self.analyze_processing_map[client_state['document_id']] = 0
        self.analyze_processing_map_lock.release()

        body = doc.get('body');
        doc_content = body.get('content')
        doc_id = client_state['document_id']
        paragraphs = self.get_paragraphs(doc_content)

        self.item_map_lock.acquire()
        item_map = self.item_map
        self.item_map_lock.release()
        analyze_inputs = []
        progress_per_term = 1.0 / len(item_map)
        if client_state['user_id'] in self.analyze_never_link:
            link_prefs = self.analyze_never_link[client_state['user_id']]
        else:
            link_prefs = {}
        for term in item_map.keys():
            analyze_inputs.append([term, start_offset, paragraphs, self.partial_match_min_size, self.partial_match_thresh, item_map[term]])
        search_results = []
        with Pool(self.multiprocessing_pool_size) as p:
            for __, result in enumerate(p.imap_unordered(intent_parser_utils.analyze_term, analyze_inputs), 1):
                if len(result) > 0:
                    for r in result:
                        do_not_link = False
                        if r['term'] in link_prefs and r['text'] in link_prefs[r['term']]:
                            do_not_link = True
                        if not do_not_link:
                            search_results.append(r)
                self.analyze_processing_map_lock.acquire()
                self.analyze_processing_map[doc_id] += progress_per_term
                self.analyze_processing_map[doc_id] = min(100, self.analyze_processing_map[doc_id])
                self.analyze_processing_map_lock.release()
            p.close()
            p.join()

        # Remove any matches that overlap, taking the longest match
        search_results = self.cull_overlapping(search_results);

        search_results = sorted(search_results,key=itemgetter('paragraph_index','offset'))

        client_state['search_results'] = search_results
        client_state['search_result_index'] = 0

        self.analyze_processing_map_lock.acquire()
        self.analyze_processing_map[client_state['document_id']] = 100
        self.analyze_processing_map_lock.release()

    def cull_overlapping(self, search_results):
        """
        Find any results that overlap and take the one with the largest term.
        """
        new_results = []
        ignore_idx = set()
        for idx in range(0, len(search_results)):
            #if idx in ignore_idx:
            #    continue;

            overlaps, max_idx, overlap_idx = intent_parser_utils.find_overlaps(idx, search_results)
            if len(overlaps) > 1:
                if max_idx not in ignore_idx:
                    new_results.append(search_results[max_idx])
                ignore_idx = ignore_idx.union(overlap_idx)
            else:
                if idx not in ignore_idx:
                    new_results.append(search_results[idx])
        return new_results

    def process_analyze_yes(self, json_body, client_state):
        """
        Handle "Yes" button as part of analyze document.
        """
        search_results = client_state['search_results']
        search_result_index = client_state['search_result_index'] - 1
        search_result = search_results[search_result_index]

        if type(json_body['data']['buttonId']) is dict:
            new_link = json_body['data']['buttonId']['link']
        else:
            new_link = None

        actions = self.add_link(search_result, new_link);
        actions += self.report_search_results(client_state)
        return actions

    def process_analyze_no(self, json_body, client_state):
        """
        Handle "No" button as part of analyze document.
        """
        json_body # Remove unused warning
        return self.report_search_results(client_state)

    def process_link_all(self, json_body, client_state):
        """
        Handle "Link all" button as part of analyze document.
        """
        search_results = client_state['search_results']
        search_result_index = client_state['search_result_index'] - 1
        search_result = search_results[search_result_index]
        term = search_result['term']
        term_search_results = list(filter(lambda x : x['term'] == term,
                                          search_results))

        if type(json_body['data']['buttonId']) is dict:
            new_link = json_body['data']['buttonId']['link']
        else:
            new_link = None

        actions = []

        for term_result in term_search_results:
            actions += self.add_link(term_result, new_link);

        actions += self.report_search_results(client_state)

        return actions

    def process_no_to_all(self, json_body, client_state):
        """
        Handle "No to all" button as part of analyze document.
        """
        json_body # Remove unused warning
        curr_idx = client_state['search_result_index'] - 1
        next_idx = curr_idx + 1
        search_results = client_state['search_results']
        while next_idx < len(search_results) and search_results[curr_idx]['term'] == search_results[next_idx]['term']:
            next_idx = next_idx + 1
        # Are we at the end? Then just exit
        if next_idx >= len(search_results):
            return []

        term_to_ignore = search_results[curr_idx]['term']
        # Generate results without term to ignore
        new_search_results = [r for r in search_results if not r['term'] == term_to_ignore ]

        # Find out what term to point to
        new_idx = new_search_results.index(search_results[next_idx])
        # Update client state
        client_state['search_results'] = new_search_results
        client_state['search_result_index'] = new_idx

        return self.report_search_results(client_state)

    def process_never_link(self, json_body, client_state):
        """
        Handle "Never Link" button as part of analyze document.
        This works like "No to all" but also stores the association to ignore it in subsequent runs.
        """
        json_body # Remove unused warning

        curr_idx = client_state['search_result_index'] - 1
        search_results = client_state['search_results']

        dict_term = search_results[curr_idx]['term']
        content_text = search_results[curr_idx]['text']

        userId = client_state['user_id']

        # Make sure we have a list of link preferences for this userId
        if not userId in self.analyze_never_link:
            link_pref_file = os.path.join(self.link_pref_path, userId + '.json')
            if os.path.exists(link_pref_file):
                try:
                    with open(link_pref_file, 'r') as fin:
                        self.analyze_never_link[userId] = json.load(fin)
                        self.logger.info('Loaded link preferences for userId, path: %s' % link_pref_file)
                except:
                    self.logger.error('ERROR: Failed to load link preferences file!')
            else:
                self.analyze_never_link[userId] = {}

        # Update link preferences
        if dict_term in self.analyze_never_link[userId]:
            # Append text to list of no-link preferences
            self.analyze_never_link[userId][dict_term].append(content_text)
        else:
            # If no prefs for this dict term, start a new list with the current text
            self.analyze_never_link[userId][dict_term] = [content_text]

        link_pref_file = os.path.join(self.link_pref_path, userId + '.json')
        try:
            with open(link_pref_file, 'w') as fout:
                json.dump(self.analyze_never_link[userId], fout)
        except:
            self.logger.error('ERROR: Failed to write link preferences file!')

        # Remove all of these associations from the results
        # This is different from "No to All", because that's only termed based
        # This depends on the term and the text
        next_idx = curr_idx + 1
        while next_idx < len(search_results) and search_results[curr_idx]['term'] == search_results[next_idx]['term'] and search_results[curr_idx]['text'] == search_results[next_idx]['text']:
            next_idx = next_idx + 1

        # Are we at the end? Then just exit
        if next_idx >= len(search_results):
            return []

        term_to_ignore = search_results[curr_idx]['term']
        text_to_ignore = search_results[curr_idx]['text']
        # Generate results without term to ignore
        new_search_results = [r for r in search_results if not r['term'] == term_to_ignore and not r['text'] == text_to_ignore]

        # Find out what term to point to
        new_idx = new_search_results.index(search_results[next_idx])
        # Update client state
        client_state['search_results'] = new_search_results
        client_state['search_result_index'] = new_idx

        return self.report_search_results(client_state)

    def highlight_text(self, paragraph_index, offset, end_offset):
        highlight_text = {}
        highlight_text['action'] = 'highlightText'
        highlight_text['paragraph_index'] = paragraph_index
        highlight_text['offset'] = offset
        highlight_text['end_offset'] = end_offset

        return highlight_text

    def link_text(self, paragraph_index, offset, end_offset, url):
        link_text = {}
        link_text['action'] = 'linkText'
        link_text['paragraph_index'] = paragraph_index
        link_text['offset'] = offset
        link_text['end_offset'] = end_offset
        link_text['url'] = url

        return link_text

    def progress_sidebar_dialog(self):
        """
        Generate the HTML to display analyze progress in a sidebar.
        """
        htmlMessage  = '''
<script>
    var interval = 1250; // ms
    var expected = Date.now() + interval;
    setTimeout(progressUpdate, 10);
    function progressUpdate() {
        var dt = Date.now() - expected; // the drift (positive for overshooting)
        if (dt > interval) {
            // something really bad happened. Maybe the browser (tab) was inactive?
            // possibly special handling to avoid futile "catch up" run
        }

        google.script.run.withSuccessHandler(refreshProgress).getAnalyzeProgress();

        expected += interval;
        setTimeout(progressUpdate, Math.max(0, interval - dt)); // take into account drift
    }

    function refreshProgress(prog) {
        var table = document.getElementById('progressTable')
        table.innerHTML = '<i>Analyzing, ' + prog + '% complete</i>'
    }

    var table = document.getElementById('progressTable')
    table.innerHTML = '<i>Analyzing, 0% complete</i>'
</script>

<center>
  <table stype="width:100%" id="progressTable">
  </table>
</center>
        '''

        action = {}
        action['action'] = 'showProgressbar'
        action['html'] = htmlMessage

        return action

    def simple_sidebar_dialog(self, message, buttons):
        htmlMessage  = '<script>\n\n'
        htmlMessage += 'function onSuccess() { \n\
                         google.script.host.close()\n\
                      }\n\n'
        for button in buttons:
            if 'click_script' in button: # Special buttons, define own script
                htmlMessage += button['click_script']
            else: # Regular buttons, generate script automatically
                htmlMessage += 'function ' + button['id'] + 'Click() {\n'
                htmlMessage += '  google.script.run.withSuccessHandler'
                htmlMessage += '(onSuccess).buttonClick(\''
                htmlMessage += button['id']  + '\')\n'
                htmlMessage += '}\n\n'
        htmlMessage += '</script>\n\n'

        htmlMessage += '<p>' + message + '<p>\n'
        htmlMessage += '<center>'
        for button in buttons:
            if 'click_script' in button: # Special buttons, define own script
                htmlMessage += '<input id=' + button['id'] + 'Button value="'
                htmlMessage += button['value'] + '" type="button"'
                if 'title' in button:
                    htmlMessage += 'title="' + button['title'] + '"'
                htmlMessage += ' onclick="' + button['id'] + 'Click()" />\n'
            else:
                htmlMessage += '<input id=' + button['id'] + 'Button value="'
                htmlMessage += button['value'] + '" type="button"'
                if 'title' in button:
                    htmlMessage += 'title="' + button['title'] + '"'
                htmlMessage += 'onclick="' + button['id'] + 'Click()" />\n'
        htmlMessage += '</center>'

        action = {}
        action['action'] = 'showSidebar'
        action['html'] = htmlMessage

        return action

    def simple_modal_dialog(self, message, buttons, title, width, height):
        htmlMessage = '<script>\n\n'
        htmlMessage += 'function onSuccess() { \n\
                         google.script.host.close()\n\
                      }\n\n'
        for button in buttons:
            htmlMessage += 'function ' + button[1] + 'Click() {\n'
            htmlMessage += '  google.script.run.withSuccessHandler'
            htmlMessage += '(onSuccess).buttonClick(\''
            htmlMessage += button[1]  + '\')\n'
            htmlMessage += '}\n\n'
        htmlMessage += '</script>\n\n'

        htmlMessage += '<p>' + message + '</p>\n'
        htmlMessage += '<center>'
        for button in buttons:
            htmlMessage += '<input id=' + button[1] + 'Button value="'
            htmlMessage += button[0] + '" type="button" onclick="'
            htmlMessage += button[1] + 'Click()" />\n'
        htmlMessage += '</center>'

        return self.modal_dialog(htmlMessage, title, width, height)

    def modal_dialog(self, html, title, width, height):
        action = {}
        action['action'] = 'showModalDialog'
        action['html'] = html
        action['title'] = title
        action['width'] = width
        action['height'] = height

        return action

    def sidebar_dialog(self, htmlMessage):
        action = {}
        action['action'] = 'showSidebar'
        action['html'] = htmlMessage

        return action

    def find_exact_text(self, text, starting_pos, paragraphs):
        """
        Search through the whole document, beginning at starting_pos and return the first exact match to text.
        """
        elements = []

        for paragraph_index in range( len(paragraphs )):
            paragraph = paragraphs[ paragraph_index ]
            elements = paragraph['elements']

            for element_index in range( len(elements) ):
                element = elements[ element_index ]

                if 'textRun' not in element:
                    continue
                text_run = element['textRun']

                end_index = element['endIndex']
                if end_index < starting_pos:
                    continue

                start_index = element['startIndex']
                if start_index < starting_pos:
                    find_start = starting_pos - start_index
                else:
                    find_start = 0

                content = text_run['content']
                offset = content.lower().find(text.lower(), find_start)

                # Check for whitespace before found text
                if offset > 0 and content[offset-1].isalpha():
                    continue

                # Check for whitespace after found text
                next_offset = offset + len(text)
                if next_offset < len(content) and content[next_offset].isalpha():
                    continue

                if offset < 0:
                    continue

                content_text = content[offset:(offset+len(text))]

                first_index = elements[0]['startIndex']
                offset += start_index - first_index

                link = None

                if 'textStyle' in text_run:
                    text_style = text_run['textStyle']
                    if 'link' in text_style:
                        link = text_style['link']
                        if 'url' in link:
                            link = link['url']

                pos = first_index + offset
                return (paragraph_index, offset, pos, link,
                        content_text)

        return None

    def handleGET(self, httpMessage, sm):
        resource = httpMessage.get_path()

        if resource == "/status":
            self.send_response(200, 'OK', 'Intent Parser Server is Up and Running\n', sm)
        elif resource == '/document_report':
            self.process_generate_report(httpMessage, sm)
        elif resource == '/document_request':
            self.process_generate_request(httpMessage, sm)
        else:
            self.logger.warning('Did not find ' + resource)
            raise ConnectionException(404, 'Not Found', 'Resource Not Found')

    def new_connection(self, document_id):
        self.client_state_lock.acquire()
        if document_id in self.client_state_map:
            if self.client_state_map[document_id]['locked']:
                self.client_state_lock.release()
                raise ConnectionException(503, 'Service Unavailable',
                                          'This document is busy')

        client_state = {}
        client_state['document_id'] = document_id
        client_state['locked'] = True

        self.client_state_map[document_id] = client_state

        self.client_state_lock.release()

        return client_state

    def get_connection(self, document_id):
        self.client_state_lock.acquire()
        if document_id not in self.client_state_map:
            self.client_state_lock.release()
            raise ConnectionException(404, 'Bad Request',
                                      'Invalid session')

        client_state = self.client_state_map[document_id]

        if client_state['locked']:
            self.client_state_lock.release()
            raise ConnectionException(503, 'Service Unavailable',
                                      'This document is busy')
        client_state['locked'] = True
        self.client_state_lock.release()

        return client_state

    def release_connection(self, client_state):
        if client_state is None:
            return

        self.client_state_lock.acquire()

        document_id = client_state['document_id']

        if document_id in self.client_state_map:
            client_state = self.client_state_map[document_id]
            if not client_state['locked']:
                self.logger.error('Error: releasing client_state, but it is not locked! doc_id: %s, called by %s' % (document_id, inspect.currentframe().f_back.f_code.co_name))
            client_state['locked'] = False

        self.client_state_lock.release()

    def stop(self):
        ''' Stop the intent parser server
        '''
        if self.sbh is not None:
            self.sbh.stop()

        self.logger.info('Signaling shutdown...')
        self.shutdownThread = True
        self.event.set()

        if self.server is not None:
            self.logger.info('Closing server...')
            try:
                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()
            except OSError as ex:
                return
            for key in self.curr_running_threads:
                client_thread = self.curr_running_threads[key]
                if client_thread.isAlive():
                    client_thread.join()
                    
        self.logger.info('Shutdown complete')

    def housekeeping(self):
        while True:
            self.event.wait(3600)
            if self.shutdownThread:
                return

            try:
                item_map = self.generate_item_map(use_cache=False)
            except Exception as ex:
                self.logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))

            self.item_map_lock.acquire()
            self.item_map = item_map
            self.item_map_lock.release()

    def cache_json_data(self):
        """
        Function that reads various json schemas and caches the data.
        """

        # Challenge Problem IDs
        response = urllib.request.urlopen('https://schema.catalog.sd2e.org/schemas/challenge_problem_id.json',timeout=60)
        data = json.loads(response.read().decode('utf-8'))

        self.challenge_ids = []
        for cid in data['enum']:
            self.challenge_ids.append(cid)

        # File types
        response = urllib.request.urlopen('https://schema.catalog.sd2e.org/schemas/filetype_label.json',timeout=60)
        data = json.loads(response.read().decode('utf-8'))

        self.file_types = []
        for cid in data['enum']:
            self.file_types.append(cid)

        # Measurement types
        response = urllib.request.urlopen('https://schema.catalog.sd2e.org/schemas/measurement_type.json',timeout=60)
        data = json.loads(response.read().decode('utf-8'))

        self.measurement_types = []
        for cid in data['enum']:
            self.measurement_types.append(cid)

        # Time units
        response = urllib.request.urlopen('https://schema.catalog.sd2e.org/schemas/time_unit.json',timeout=60)
        data = json.loads(response.read().decode('utf-8'))

        self.time_units = []
        for cid in data['enum']:
            self.time_units.append(cid)

        # Fluid units
        response = urllib.request.urlopen('https://schema.catalog.sd2e.org/schemas/fluid_unit.json',timeout=60)
        data = json.loads(response.read().decode('utf-8'))

        self.fluid_units = []
        for cid in data['enum']:
            self.fluid_units.append(cid)

        # Temperature units
        response = urllib.request.urlopen('https://schema.catalog.sd2e.org/schemas/temperature_unit.json',timeout=60)
        data = json.loads(response.read().decode('utf-8'))

        self.temp_units = []
        for cid in data['enum']:
            self.temp_units.append(cid)
            
        # Volume units
        response = urllib.request.urlopen('https://schema.catalog.sd2e.org/schemas/volume_unit.json',timeout=60)
        data = json.loads(response.read().decode('utf-8'))

        self.volume_units = []
        for cid in data['enum']:
            self.volume_units.append(cid)

        # Lab Ids
        response = urllib.request.urlopen('https://schema.catalog.sd2e.org/schemas/lab.json',timeout=60)
        data = json.loads(response.read().decode('utf-8'))

        self.lab_ids = []
        for cid in data['enum']:
            self.lab_ids.append(cid)
        self.lab_ids = sorted(self.lab_ids)
    
        
    def generate_item_map(self, *, use_cache=True):
        item_map = {}
        self.logger.info('Generating item map, %d' % time.time())
        if use_cache:
            try:
                f = open(self.my_path + '/item-map.json', 'r')
                item_map = json.loads(f.read())
                f.close()
                self.logger.info('Num items in item_map: %d' % len(item_map))
                return item_map

            except:
                pass

        lab_uid_src_map = {}
        lab_uid_common_map = {}
        sheet_data = self.fetch_spreadsheet_data()
        for tab in sheet_data:
            for row in sheet_data[tab]:
                if not 'Common Name' in row :
                    continue

                if len(row['Common Name']) == 0 :
                    continue

                if not 'SynBioHub URI' in row :
                    continue

                if len(row['SynBioHub URI']) == 0 :
                    continue

                common_name = row['Common Name']
                uri = row['SynBioHub URI']
                # Add common name to the item map
                item_map[common_name] = uri
                # There are also UIDs for each lab to add
                for lab_uid in self.lab_ids_list:
                    # Ignore if the spreadsheet doesn't contain this lab
                    if not lab_uid in row or row[lab_uid] == '':
                        continue
                    # UID can be a CSV list, parse each value
                    for uid_str in row[lab_uid].split(sep=','):
                        # Make sure the UID matches the min len threshold, or is in the exception list
                        if len(uid_str) >= self.uid_length_threshold or uid_str in self.uid_length_exception:
                            # If the UID isn't in the item map, add it with this URI
                            if uid_str not in item_map:
                                item_map[uid_str] = uri
                                lab_uid_src_map[uid_str] = lab_uid
                                lab_uid_common_map[uid_str] = common_name
                            else: # Otherwise, we need to check for an error
                                # If the UID has been used  before, we might have a conflict
                                if uid_str in lab_uid_src_map:
                                    # If the common name was the same for different UIDs, this won't have an effect
                                    # But if they differ, we have a conflict
                                    if not lab_uid_common_map[uid_str] == common_name:
                                        self.logger.error('Trying to add %s %s for common name %s, but the item map already contains %s from %s for common name %s!' %
                                                          (lab_uid, uid_str, common_name, uid_str, lab_uid_src_map[uid_str], lab_uid_common_map[uid_str]))
                                else: # If the UID wasn't used before, then it matches the common name and adding it would be redundant
                                    pass
                                    # If it matches the common name, that's fine
                                    #self.logger.error('Trying to add %s %s, but the item map already contains %s from common name!' % (lab_uid, uid_str, uid_str))
                        else:
                            self.logger.debug('Filtered %s %s for length' % (lab_uid, uid_str))

        f = open(self.my_path + '/item-map.json', 'w')
        f.write(json.dumps(item_map))
        f.close()

        self.logger.info('Num items in item_map: %d' % len(item_map))

        return item_map

    def generate_html_options(self, options):
        options_html = ''
        for item_type in options:
            options_html += '          '
            options_html += '<option>'
            options_html += item_type
            options_html += '</option>\n'

        return options_html

    def generate_existing_link_html(self, title, target, two_col = False):
        if two_col:
            width = 175
        else:
            width = 350

        html  = '<tr>\n'
        html += '  <td style="max-width: %dpx; word-wrap: break-word; padding:5px">\n' % width
        html += '    <a href=' + target + ' target=_blank name="theLink">' + title + '</a>\n'
        html += '  </td>\n'
        html += '  <td>\n'
        html += '    <input type="button" name=' + target + ' value="Link"\n'
        html += '    title="Create a link with this URL." onclick="linkItem(thisForm, this.name)">\n'
        if not two_col:
            html += '  </td>\n'
            html += '  <td>\n'
        else:
            html += '  <br/>'
        html += '    <input type="button" name=' + target + ' value="Link All"\n'
        html += '    title="Create a link with this URL and apply it to all matching terms." onclick="linkAll(thisForm, this.name)">\n'
        html += '  </td>\n'
        html += '</tr>\n'

        return html

    def generate_results_pagination_html(self, offset, count):
        curr_set_str = '%d - %d' % (offset, offset + self.sparql_limit)
        firstHTML = '<a onclick="refreshList(%d)" href="#first" >First</a>' % 0
        lastHTML  = '<a onclick="refreshList(%d)" href="#last" >Last</a>' % (count - self.sparql_limit)
        prevHTML  = '<a onclick="refreshList(%d)" href="#previous" >Previous</a>' % max(0, offset - self.sparql_limit - 1)
        nextHTML  = '<a onclick="refreshList(%d)" href="#next" >Next</a>'  % min(count - self.sparql_limit, offset + self.sparql_limit + 1)

        html  = '<tr>\n'
        html += '  <td align="center" colspan = 3 style="max-width: 250px; word-wrap: break-word;">\n'
        html += '    Showing %s of %s\n' % (curr_set_str, count)
        html += '  </td>\n'
        html += '</tr>\n'
        html += '<tr>\n'
        html += '  <td align="center" colspan = 3 style="max-width: 250px; word-wrap: break-word;">\n'
        html += '    %s, %s, %s, %s\n' % (firstHTML, prevHTML, nextHTML, lastHTML)
        html += '  </td>\n'
        html += '</tr>\n'

        return html

    def process_create_table_template(self,  httpMessage, sm):
        """
        """
        try:
            json_body = self.get_json_body(httpMessage)

            data = json_body['data']
            cursor_child_index = str(data['childIndex'])
            table_type = data['tableType']

            html = None
            if table_type == 'measurements':
                html = self.create_measurements_table_html

                local_file_types = self.file_types.copy()
                local_file_types.insert(0,'---------------')
                local_file_types.insert(0,'CSV')
                local_file_types.insert(0,'PLAIN')
                local_file_types.insert(0,'FASTQ')
                local_file_types.insert(0,'FCS')

                lab_ids_html = self.generate_html_options(self.lab_ids)
                measurement_types_html = self.generate_html_options(self.measurement_types)
                file_types_html = self.generate_html_options(local_file_types)

                measurement_types_html = measurement_types_html.replace('\n', ' ')
                file_types_html = file_types_html.replace('\n', ' ')

                # Update parameters in html
                html = html.replace('${CURSOR_CHILD_INDEX}', cursor_child_index)
                html = html.replace('${LABIDSOPTIONS}', lab_ids_html)
                html = html.replace('${MEASUREMENTOPTIONS}', measurement_types_html)
                html = html.replace('${FILETYPEOPTIONS}', file_types_html)

            else :
                self.logger.warning('WARNING: unsupported table type: %s' % table_type)

            actionList = []
            if html is not None:
                dialog_action = self.modal_dialog(html, 'Create Measurements Table', 600, 600)
                actionList.append(dialog_action)

            actions = {'actions': actionList}
            self.send_response(200, 'OK', json.dumps(actions), sm, 'application/json')
        except Exception as e:
            raise e

    def process_add_to_syn_bio_hub(self, httpMessage, sm):
        try:
            json_body = self.get_json_body(httpMessage)

            data = json_body['data']
            start = data['start']
            end = data['end']
            document_id = json_body['documentId']

            start_paragraph = start['paragraphIndex'];
            end_paragraph = end['paragraphIndex'];

            start_offset = start['offset']
            end_offset = end['offset']

            dialog_action = self.internal_add_to_syn_bio_hub(document_id, start_paragraph, end_paragraph,
                                                             start_offset, end_offset)
            actionList = [dialog_action]
            actions = {'actions': actionList}

            self.send_response(200, 'OK', json.dumps(actions), sm, 'application/json')

            self.logger.info('Add entry to SynBiohub, %s, %s' %(document_id, time.time()))
        except Exception as e:
            raise e


    def internal_add_to_syn_bio_hub(self, document_id, start_paragraph, end_paragraph, start_offset, end_offset, isSpellcheck=False):
        try:

            item_type_list = []
            for sbol_type in self.item_types:
                item_type_list += self.item_types[sbol_type].keys()

            item_type_list = sorted(item_type_list)
            item_types_html = self.generate_html_options(item_type_list)

            lab_ids_html = self.generate_html_options(self.lab_ids_list)

            try:
                doc = self.google_accessor.get_document(
                    document_id=document_id
                )
            except Exception as ex:
                self.logger.error(''.join(traceback.format_exception(etype=type(ex),
                                                         value=ex,
                                                         tb=ex.__traceback__)))
                raise ConnectionException('404', 'Not Found',
                                          'Failed to access document ' +
                                          document_id)

            body = doc.get('body');
            doc_content = body.get('content')
            paragraphs = self.get_paragraphs(doc_content)

            paragraph_text = intent_parser_utils.get_paragraph_text(
                paragraphs[start_paragraph])


            selection = paragraph_text[start_offset:end_offset + 1]
            # Remove leading/trailing space
            selection = selection.strip()
            display_id = self.sanitize_name_to_display_id(selection)

            html = self.add_html

            # Update parameters in html
            html = html.replace('${COMMONNAME}', selection)
            html = html.replace('${DISPLAYID}', display_id)
            html = html.replace('${STARTPARAGRAPH}', str(start_paragraph))
            html = html.replace('${STARTOFFSET}', str(start_offset))
            html = html.replace('${ENDPARAGRAPH}', str(end_paragraph))
            html = html.replace('${ENDOFFSET}', str(end_offset))
            html = html.replace('${ITEMTYPEOPTIONS}', item_types_html)
            html = html.replace('${LABIDSOPTIONS}', lab_ids_html)
            html = html.replace('${SELECTEDTERM}', selection)
            html = html.replace('${DOCUMENTID}', document_id)
            html = html.replace('${ISSPELLCHECK}', str(isSpellcheck))

            if isSpellcheck:
                replaceButtonHtml = """
        <input type="button" value="Submit" id="submitButton" onclick="submitToSynBioHub()">
        <input type="button" value="Submit, Link All" id="submitButtonLinkAll" onclick="submitToSynBioHubAndLinkAll()">
                """
                html = html.replace('${SUBMIT_BUTTON}', replaceButtonHtml)
            else:
                html = html.replace('${SUBMIT_BUTTON}', '        <input type="button" value="Submit" id="submitButton" onclick="submitToSynBioHub()">')

            dialog_action = self.modal_dialog(html, 'Add to SynBioHub',
                                              600, 600)
            return dialog_action
        except Exception as e:
            raise e

    def char_is_not_wordpart(self, ch):
        """ Determines if a character is part of a word or not
        This is used when parsing the text to tokenize words.
        """
        return ch is not '\'' and not ch.isalnum()

    def strip_leading_trailing_punctuation(self, word):
        """ Remove any leading of trailing punctuation (non-alphanumeric characters
        """
        start_index = 0
        end_index = len(word)
        while start_index < len(word) and not word[start_index].isalnum():
            start_index +=1
        while end_index > 0 and not word[end_index - 1].isalnum():
            end_index -= 1

        # If the word was only non-alphanumeric, we could get into a strange case
        if (end_index <= start_index):
            return ''
        else:
            return word[start_index:end_index]

    def should_ignore_token(self, word):
        """ Determines if a token/word should be ignored
        For example, if a token contains no alphabet characters, we should ignore it.
        """

        contains_alpha = False
        # This was way too slow
        #term_exists_in_sbh = len(self.simple_syn_bio_hub_search(word)) > 0
        term_exists_in_sbh = False
        for ch in word:
            contains_alpha |= ch.isalpha()

        return not contains_alpha  or term_exists_in_sbh

    def process_add_by_spelling(self, http_message, sm):
        """ Function that sets up the results for additions by spelling
        This will start from a given offset (generally 0) and searches the rest of the
        document, looking for words that are not in the dictionary.  Any words that
        don't match are then used as suggestions for additions to SynBioHub.

        Users can add words to the dictionary, and added words are saved by a user id.
        This comes from the email address, but if that's not available the document id
        is used instead.
        """
        try:
            client_state = None
            json_body = self.get_json_body(http_message)

            document_id = json_body['documentId']
            user = json_body['user']
            userEmail = json_body['userEmail']

            if not userEmail is '':
                userId = userEmail
            elif user:
                userId = user
            else:
                userId = document_id

            if not userId in self.spellCheckers:
                self.spellCheckers[userId] = SpellChecker()
                dict_path = os.path.join(self.dict_path, userId + '.json')
                if os.path.exists(dict_path):
                    self.logger.info('Loaded dictionary for userId, path: %s' % dict_path)
                    self.spellCheckers[userId].word_frequency.load_dictionary(dict_path)

            try:
                doc = self.google_accessor.get_document(
                    document_id=document_id
                )
            except Exception as ex:
                self.logger.error(''.join(traceback.format_exception(etype=type(ex),
                                                         value=ex,
                                                         tb=ex.__traceback__)))
                raise ConnectionException('404', 'Not Found',
                                          'Failed to access document ' +
                                          document_id)

            if 'data' in json_body:
                body = doc.get('body');
                doc_content = body.get('content')
                paragraphs = self.get_paragraphs(doc_content)

                data = json_body['data']
                paragraph_index = data['paragraphIndex']
                offset = data['offset']
                paragraph = paragraphs[ paragraph_index ]
                first_element = paragraph['elements'][0]
                paragraph_offset = first_element['startIndex']
                starting_pos = paragraph_offset + offset
            else:
                starting_pos = 0

            # Used to store session information
            client_state = self.new_connection(document_id)
            client_state['doc'] = doc
            client_state['user_id'] = userId

            body = doc.get('body');
            doc_content = body.get('content')
            paragraphs = self.get_paragraphs(doc_content)

            start = time.time()

            spellCheckResults = [] # Store results metadata
            missedTerms = [] # keep track of lists of misspelt words
            # Second list can help us remove results by word

            for pIdx in range(0, len(paragraphs)):
                paragraph = paragraphs[ pIdx ]
                elements = paragraph['elements']
                firstIdx = elements[0]['startIndex']
                for element_index in range( len(elements) ):
                    element = elements[ element_index ]

                    if 'textRun' not in element:
                        continue
                    text_run = element['textRun']

                    end_index = element['endIndex']
                    if end_index < starting_pos:
                        continue

                    start_index = element['startIndex']

                    if start_index < starting_pos:
                        wordStart = starting_pos - start_index
                    else:
                        wordStart = 0

                    # If this text run is already linked, we don't need to process it
                    if 'textStyle' in text_run and 'link' in text_run['textStyle']:
                        continue

                    content = text_run['content']
                    endIdx = len(content);
                    currIdx = wordStart + 1
                    while currIdx < endIdx:
                        # Check for end of word
                        if self.char_is_not_wordpart(content[currIdx]):
                            word = content[wordStart:currIdx]
                            word = self.strip_leading_trailing_punctuation(word)
                            word = word.lower()
                            if not word in self.spellCheckers[userId] and not self.should_ignore_token(word):
                                # Convert from an index into the content string,
                                # to an offset into the paragraph string
                                absoluteIdx =  wordStart + (start_index - firstIdx)
                                result = {
                                   'term' : word,
                                   'select_start' : {'paragraph_index' : pIdx,
                                                        'cursor_index' : absoluteIdx,
                                                        'element_index': element_index},
                                   'select_end' : {'paragraph_index' : pIdx,
                                                        'cursor_index' : absoluteIdx + len(word) - 1,
                                                        'element_index': element_index}
                                   }
                                spellCheckResults.append(result)
                                missedTerms.append(word)
                            # Find start of next word
                            while currIdx < endIdx and self.char_is_not_wordpart(content[currIdx]):
                                currIdx += 1
                            # Store word start
                            wordStart = currIdx
                            currIdx += 1
                        else: # continue until we find word end
                            currIdx += 1

                    # Check for tailing word that wasn't processed
                    if currIdx - wordStart > 1:
                        word = content[wordStart:currIdx]
                        word = self.strip_leading_trailing_punctuation(word)
                        word = word.lower()
                        if not word in self.spellCheckers[userId]:
                            absoluteIdx =  wordStart + (start_index - firstIdx)
                            result = {
                               'term' : word,
                               'select_start' : {'paragraph_index' : pIdx,
                                                    'cursor_index' : absoluteIdx,
                                                    'element_index': element_index},
                               'select_end' : {'paragraph_index' : pIdx,
                                                    'cursor_index' : absoluteIdx + len(word) - 1,
                                                    'element_index': element_index}
                               }
                            spellCheckResults.append(result)
                            missedTerms.append(word)
            end = time.time()
            self.logger.info('Scanned entire document in %0.2fms, %s, %s' %((end - start) * 1000, document_id, time.time()))

            # If we have a spelling mistake, highlight text and update user
            if len(spellCheckResults) > 0:
                client_state['spelling_results'] = spellCheckResults
                client_state['spelling_index'] = 0
                client_state['spelling_size'] = len(spellCheckResults)
                actionList = self.report_spelling_results(client_state)
                actions = {'actions': actionList}
                self.send_response(200, 'OK', json.dumps(actions), sm, 'application/json')
            else: # No spelling mistakes!
                buttons = [('Ok', 'process_nop')]
                dialog_action = self.simple_modal_dialog('Found no words not in spelling dictionary!', buttons, 'No misspellings!', 400, 450)
                actionList = [dialog_action]
                actions = {'actions': actionList}
                self.send_response(200, 'OK', json.dumps(actions), sm,
                                   'application/json')
        except Exception as e:
            raise e

        finally:
            if not client_state is None:
                self.release_connection(client_state)

    def report_spelling_results(self, client_state):
        """Generate actions for client, given the current spelling results index
        """
        spellCheckResults = client_state['spelling_results']
        resultIdx = client_state['spelling_index']

        actionList = []

        start_par = spellCheckResults[resultIdx]['select_start']['paragraph_index']
        start_cursor = spellCheckResults[resultIdx]['select_start']['cursor_index']
        end_par = spellCheckResults[resultIdx]['select_end']['paragraph_index']
        end_cursor = spellCheckResults[resultIdx]['select_end']['cursor_index']
        if not start_par == end_par:
            self.logger.error('Received a highlight request across paragraphs, which is currently unsupported!')
        highlightTextAction = self.highlight_text(start_par, start_cursor, end_cursor)
        actionList.append(highlightTextAction)

        html  = ''
        html += '<center>'
        html += 'Term ' + spellCheckResults[resultIdx]['term'] + ' not found in dictionary, potential addition? ';
        html += '</center>'

        manualLinkScript = """

    function EnterLinkClick() {
        google.script.run.withSuccessHandler(enterLinkHandler).enterLinkPrompt('Manually enter a SynbioHub link for this term.', 'Enter URI:');
    }

    function enterLinkHandler(result) {
        var shouldProcess = result[0];
        var text = result[1];
        if (shouldProcess) {
            var data = {'buttonId' : 'spellcheck_link',
                     'link' : text}
            google.script.run.withSuccessHandler(onSuccess).buttonClick(data)
        }
    }

        """

        buttons = [{'value': 'Ignore', 'id': 'spellcheck_add_ignore', 'title' : 'Skip the current term.'},
                   {'value': 'Ignore All', 'id': 'spellcheck_add_ignore_all', 'title' : 'Skip the current term and any other instances of it.'},
                   {'value': 'Add to Spellchecker Dictionary', 'id': 'spellcheck_add_dictionary', 'title' : 'Add term to the spellchecking dictionary, so it won\'t be considered again.'},
                   {'value': 'Add to SynBioHub', 'id': 'spellcheck_add_synbiohub', 'title' : 'Bring up dialog to add current term to SynbioHub.'},
                   {'value': 'Manually Enter Link', 'id': 'EnterLink', 'click_script' : manualLinkScript, 'title' : 'Manually enter URL to link for this term.'},
                   {'value': 'Include Previous Word', 'id': 'spellcheck_add_select_previous', 'title' : 'Move highlighting to include the word before the highlighted word(s).'},
                   {'value': 'Include Next Word', 'id': 'spellcheck_add_select_next', 'title' : 'Move highlighting to include the word after the highlighted word(s).'},
                   {'value': 'Remove First Word', 'id': 'spellcheck_add_drop_first', 'title' : 'Move highlighting to remove the word at the beggining of the highlighted words.'},
                   {'value': 'Remove Last Word', 'id': 'spellcheck_add_drop_last', 'title' : 'Move highlighting to remove the word at the end of the highlighted words.'}]

        # If this entry was previously linked, add a button to reuse that link
        if 'prev_link' in spellCheckResults[resultIdx]:
            buttons.insert(4, {'value' : 'Reuse previous link', 'id': 'spellcheck_reuse_link', 'title' : 'Reuse the previous link: %s' % spellCheckResults[resultIdx]['prev_link']})

        dialogAction = self.simple_sidebar_dialog(html, buttons)
        actionList.append(dialogAction)
        return actionList

    def spellcheck_remove_term(self, client_state):
        """ Removes the current term from the result set, returning True if a term was removed else False.
        False will be returned if there are no terms after the term being removed.
        """
        curr_idx = client_state['spelling_index']
        next_idx = curr_idx + 1
        spelling_results = client_state['spelling_results']
        while next_idx < client_state['spelling_size'] and spelling_results[curr_idx]['term'] == spelling_results[next_idx]['term']:
            next_idx = next_idx + 1
        # Are we at the end? Then just exit
        if next_idx >= client_state['spelling_size']:
            client_state['spelling_index'] = client_state['spelling_size']
            return False

        term_to_ignore = spelling_results[curr_idx]['term']
        # Generate results without term to ignore
        new_spelling_results = [r for r in spelling_results if not r['term'] == term_to_ignore ]

        # Find out what term to point to
        new_idx = new_spelling_results.index(spelling_results[next_idx])
        # Update client state
        client_state['spelling_results'] = new_spelling_results
        client_state['spelling_index'] = new_idx
        client_state['spelling_size'] = len(new_spelling_results)
        return True

    def spellcheck_add_ignore(self, json_body, client_state):
        """ Ignore button action for additions by spelling
        """
        json_body # Remove unused warning
        client_state['spelling_index'] += 1
        if client_state['spelling_index'] >= client_state['spelling_size']:
            # We are at the end, nothing else to do
            return []
        else:
            return self.report_spelling_results(client_state)

    def spellcheck_add_ignore_all(self, json_body, client_state):
        """ Ignore All button action for additions by spelling
        """
        json_body # Remove unused warning
        if self.spellcheck_remove_term(client_state):
            return self.report_spelling_results(client_state)

    def spellcheck_add_synbiohub(self, json_body, client_state):
        """ Add to SBH button action for additions by spelling
        """
        json_body # Remove unused warning

        doc_id = client_state['document_id']
        spell_index = client_state['spelling_index']
        spell_check_result = client_state['spelling_results'][spell_index]
        select_start = spell_check_result['select_start']
        select_end = spell_check_result['select_end']

        start_paragraph = select_start['paragraph_index']
        start_offset = select_start['cursor_index']

        end_paragraph = select_end['cursor_index']
        end_offset = select_end['cursor_index']

        dialog_action = self.internal_add_to_syn_bio_hub(doc_id, start_paragraph, end_paragraph,
                                                             start_offset, end_offset, isSpellcheck=True)

        actionList = [dialog_action]

        # Show side bar with current entry, in case the dialog is canceled
        # If the form is successully submitted, the next term will get displayed at that time
        for action in self.report_spelling_results(client_state):
            actionList.append(action)

        return actionList

    def spellcheck_add_dictionary(self, json_body, client_state):
        """ Add to spelling dictionary button action for additions by spelling
        """
        json_body # Remove unused warning
        user_id = client_state['user_id']

        spell_index = client_state['spelling_index']
        spell_check_result = client_state['spelling_results'][spell_index]
        new_word = spell_check_result['term']

        # Add new word to frequency list
        self.spellCheckers[user_id].word_frequency.add(new_word)

        # Save updated frequency list for later loading
        # We could probably do this later, but it ensures no updated state is lost
        dict_path = os.path.join(self.dict_path, user_id + '.json')
        self.spellCheckers[user_id].export(dict_path)

        # Since we are adding this term to the spelling dict, we want to ignore any other results
        self.spellcheck_remove_term(client_state)
        # Removing the term automatically updates the spelling index
        #client_state["spelling_index"] += 1
        if client_state['spelling_index'] >= client_state['spelling_size']:
            # We are at the end, nothing else to do
            return []

        return self.report_spelling_results(client_state)

    def spellcheck_reuse_link(self, json_body, client_state):
        """
        Handle reuse previous link button as part of additions by spelling.
        """
        json_body # Remove unused warning
        spell_index = client_state['spelling_index']
        spell_check_result = client_state['spelling_results'][spell_index]

        if 'prev_link' in spell_check_result:
            new_link = spell_check_result['prev_link']
        else:
            new_link = None
            self.logger.error('spellcheck_reuse_link call without prev_link in spell_check_result!')

        start_par = spell_check_result['select_start']['paragraph_index']
        start_cursor = spell_check_result['select_start']['cursor_index']
        end_cursor = spell_check_result['select_end']['cursor_index']

        actions = [self.link_text(start_par, start_cursor, end_cursor, new_link)]
        client_state['spelling_index'] += 1
        if client_state['spelling_index'] < client_state['spelling_size']:
            for action in self.report_spelling_results(client_state):
                actions.append(action)
        return actions

    def spellcheck_link(self, json_body, client_state):
        """
        Handle manual link button as part of additions by spelling.
        """
        spell_index = client_state['spelling_index']
        spell_check_result = client_state['spelling_results'][spell_index]

        if type(json_body['data']['buttonId']) is dict:
            new_link = json_body['data']['buttonId']['link']
        else:
            new_link = None
            self.logger.error('spellcheck_link received a json_body without a link in it!')

        start_par = spell_check_result['select_start']['paragraph_index']
        start_cursor = spell_check_result['select_start']['cursor_index']
        end_cursor = spell_check_result['select_end']['cursor_index']

        # store the link for any other matching results
        for result in client_state['spelling_results']:
            if result['term'] == spell_check_result['term']:
                result['prev_link'] = new_link

        actions = [self.link_text(start_par, start_cursor, end_cursor, new_link)]
        client_state['spelling_index'] += 1
        if client_state['spelling_index'] < client_state['spelling_size']:
            for action in self.report_spelling_results(client_state):
                actions.append(action)
        return actions

    def spellcheck_add_select_previous(self, json_body, client_state):
        """ Select previous word button action for additions by spelling
        """
        json_body # Remove unused warning
        return self.spellcheck_select_word_from_text(client_state, True, True)

    def spellcheck_add_select_next(self, json_body, client_state):
        """ Select next word button action for additions by spelling
        """
        json_body # Remove unused warning
        return self.spellcheck_select_word_from_text(client_state, False, True)

    def spellcheck_add_drop_first(self, json_body, client_state):
        """ Remove selection previous word button action for additions by spelling
        """
        json_body # Remove unused warning
        return self.spellcheck_select_word_from_text(client_state, True, False)

    def spellcheck_add_drop_last(self, json_body, client_state):
        """ Remove selection next word button action for additions by spelling
        """
        json_body # Remove unused warning
        return self.spellcheck_select_word_from_text(client_state, False, False)

    def spellcheck_select_word_from_text(self, client_state, isPrev, isSelect):
        """ Given a client state with a selection from a spell check result,
        select or remove the selection on the next or previous word, based upon parameters.
        """
        if isPrev:
            select_key = 'select_start'
        else:
            select_key = 'select_end'

        spell_index = client_state['spelling_index']
        spell_check_result = client_state['spelling_results'][spell_index]

        starting_pos = spell_check_result[select_key]['cursor_index']
        para_index = spell_check_result[select_key]['paragraph_index']
        doc = client_state['doc']
        body = doc.get('body');
        doc_content = body.get('content')
        paragraphs = self.get_paragraphs(doc_content)
        # work on the paragraph text directly
        paragraph_text = intent_parser_utils.get_paragraph_text(paragraphs[para_index])
        para_text_len = len(paragraph_text)

        # Determine which directions to search in, based on selection or removal, prev/next
        if isSelect:
            if isPrev:
                edge_check = lambda x : x > 0
                increment = -1
            else:
                edge_check = lambda x : x < para_text_len
                increment = 1
            firstCheck = self.char_is_not_wordpart
            secondCheck = lambda x : not self.char_is_not_wordpart(x)
        else:
            if isPrev:
                edge_check = lambda x : x < para_text_len
                increment = 1
            else:
                edge_check = lambda x : x > 0
                increment = -1
            secondCheck = self.char_is_not_wordpart
            firstCheck = lambda x : not self.char_is_not_wordpart(x)

        if starting_pos < 0:
            self.logger.error('Error: got request to select previous, but the starting_pos was negative!')
            return

        if para_text_len < starting_pos:
            self.logger.error('Error: got request to select previous, but the starting_pos was past the end!')
            return

        # Move past the end/start of the current word
        currIdx = starting_pos + increment

        # Skip over space/non-word parts to the next word
        while edge_check(currIdx) and firstCheck(paragraph_text[currIdx]):
            currIdx += increment
        # Find the beginning/end of word
        while edge_check(currIdx) and secondCheck(paragraph_text[currIdx]):
            currIdx += increment

        # If we don't hit the beginning, we need to cut off the last space
        if currIdx > 0 and isPrev and isSelect:
            currIdx += 1

        if not isPrev and isSelect and paragraph_text[currIdx].isspace():
            currIdx += -1

        spell_check_result[select_key]['cursor_index'] = currIdx

        return self.report_spelling_results(client_state)

    def simple_syn_bio_hub_search(self, term, offset=0, filter_uri=None):
        """
        Search for similar terms in SynbioHub, using the cached sparql similarity query.
        This query requires the specification of a term, a limit on the number of results, and an offset.
        """
        if filter_uri is None:
            extra_filter = ''
        else:
            extra_filter = 'FILTER( !regex(?member, "%s"))' % filter_uri

        if offset == 0 or not term in self.sparql_similar_count_cache:
            start = time.time()
            sparql_count = self.sparql_similar_count.replace('${TERM}', term).replace('${EXTRA_FILTER}', extra_filter)
            query_results = self.sbh.sparqlQuery(sparql_count)
            bindings = query_results['results']['bindings']
            self.sparql_similar_count_cache[term] = bindings[0]['count']['value']
            end = time.time()
            self.logger.info('Simple SynbioHub count for %s took %0.2fms (found %s results)' %(term, (end - start) * 1000, bindings[0]['count']['value']))

        start = time.time()
        sparql_query = self.sparql_similar_query.replace('${TERM}', term).replace('${LIMIT}', str(self.sparql_limit)).replace('${OFFSET}', str(offset)).replace('${EXTRA_FILTER}', extra_filter)
        query_results = self.sbh.sparqlQuery(sparql_query)
        bindings = query_results['results']['bindings']
        search_results = []
        for binding in bindings:
            title = binding['title']['value']
            target = binding['member']['value']
            if self.sbh_spoofing_prefix is not None:
                target = target.replace(self.sbh_spoofing_prefix, self.sbh_url)
            search_results.append({'title': title, 'target': target})

        end = time.time()
        self.logger.info('Simple SynbioHub search for %s took %0.2fms' %(term, (end - start) * 1000))
        return search_results, self.sparql_similar_count_cache[term]

    def sanitize_name_to_display_id(self, name):
        displayIDfirstChar = '[a-zA-Z_]'
        displayIDlaterChar = '[a-zA-Z0-9_]'

        sanitized = ''
        for i in range(len(name)):
            character = name[i]
            if i==0:
                if re.match(displayIDfirstChar, character):
                    sanitized += character
                else:
                    sanitized += '_' # avoid starting with a number
                    if re.match(displayIDlaterChar, character):
                        sanitized += character
                    else:
                        sanitized += '0x{:x}'.format(ord(character))
            else:
                if re.match(displayIDlaterChar, character):
                    sanitized += character;
                else:
                    sanitized += '0x{:x}'.format(ord(character))

        return sanitized

    def set_item_properties(self, entity, data):
        item_type = data['itemType']
        item_name = data['commonName']
        item_definition_uri = data['definitionURI']
        item_lab_ids = data['labId']

        sbol.TextProperty(entity, 'http://purl.org/dc/terms/title', '0', '1',
                          item_name)

        time_stamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S-00')
        sbol.TextProperty(entity, 'http://purl.org/dc/terms/created', '0', '1',
                          time_stamp)
        sbol.TextProperty(entity, 'http://purl.org/dc/terms/modified', '0', '1',
                          time_stamp)

        if item_type in self.item_types['collection']:
            return

        if len(item_definition_uri) > 0:
            if item_type == 'CHEBI':
                if not item_definition_uri.startswith('http://identifiers.org/chebi/CHEBI'):
                    item_definition_uri = 'http://identifiers.org/chebi/CHEBI:' + \
                        item_definition_uri
            else:
                sbol.URIProperty(entity, 'http://www.w3.org/ns/prov#wasDerivedFrom',
                                 '0', '1', item_definition_uri)

        if len(item_lab_ids) > 0:
            lab_id_tag = data['labIdSelect'].replace(' ', '_')
            tp = None
            for item_lab_id in item_lab_ids.split(','):
                if tp is None:
                    tp = sbol.TextProperty(entity, 'http://sd2e.org#' + lab_id_tag, '0', '1',
                                           item_lab_id)
                else:
                    tp.add(item_lab_id)

    def operation_failed(self, message):
        return {'results': {'operationSucceeded': False,
                            'message': message}
        }

    def create_dictionary_entry(self, data, document_url, item_definition_uri):
        item_type = data['itemType']
        item_name = data['commonName']
        item_lab_ids = data['labId']
        item_lab_id_tag = data['labIdSelect']

        #sbh_uri_prefix = self.sbh_uri_prefix
        if self.sbh_spoofing_prefix is not None:
            item_uri = document_url.replace(self.sbh_url,
                                            self.sbh_spoofing_prefix)
        else:
            item_uri = document_url

        tab_name = self.type2tab[item_type]

        try:
            tab_data = self.google_accessor.get_row_data(tab=tab_name)
        except:
            raise Exception('Failed to access dictionary spreadsheet')

        # Get common names
        item_map = {}
        for row_data in tab_data:
            common_name = row_data['Common Name']
            if common_name is None or len(common_name) == 0:
                continue
            item_map[common_name] = row_data

        if item_name in item_map:
            raise Exception('"' + item_name + '" already exists in dictionary spreadsheet')

        dictionary_entry = {}
        dictionary_entry['tab'] = tab_name
        dictionary_entry['row'] = len(tab_data) + 3
        dictionary_entry['Common Name'] = item_name
        dictionary_entry['Type'] = item_type
        if tab_name == 'Reagent':
            dictionary_entry['Definition URI / CHEBI ID'] = \
                item_definition_uri
        else:
            dictionary_entry['Definition URI'] = \
                item_definition_uri

        if item_type != 'Attribute':
            dictionary_entry['Stub Object?'] = 'YES'

        dictionary_entry[item_lab_id_tag] = item_lab_ids
        dictionary_entry['SynBioHub URI'] = item_uri

        try:
            self.google_accessor.set_row_data(dictionary_entry)
        except:
            raise Exception('Failed to add entry to the dictionary spreadsheet')

    def create_sbh_stub(self, data):
        # Extract some fields from the form
        try:
            item_type = data['itemType']
            item_name = data['commonName']
            item_definition_uri = data['definitionURI']
            item_display_id = data['displayId']

        except Exception as e:
            return self.operation_failed('Form sumission missing key: ' + str(e))

        # Make sure Common Name was specified
        if len(item_name) == 0:
            return self.operation_failed('Common Name must be specified')

        # Sanitize the display id
        if len(item_display_id) > 0:
            display_id = self.sanitize_name_to_display_id(item_display_id)
            if display_id != item_display_id:
                return self.operation_failed('Illegal display_id')
        else:
            display_id = self.sanitize_name_to_display_id(item_name)

        # Derive document URL
        document_url = self.sbh_uri_prefix + display_id + '/1'

        # Make sure document does not already exist
        try:
            if self.sbh.exists(document_url):
                return self.operation_failed('"' + display_id +
                                             '" already exists in SynBioHub')
        except:
            return self.operation_failed('Failed to access SynBioHub')

        # Look up sbol type uri
        sbol_type = None
        for sbol_type_key in self.item_types:
            sbol_type_map = self.item_types[ sbol_type_key ]
            if item_type in sbol_type_map:
                sbol_type = sbol_type_key
                break;

        # Fix CHEBI URI
        if item_type == 'CHEBI':
            if len(item_definition_uri) == 0:
                item_definition_uri = sbol_type_map[ item_type ]
            else:
                if not item_definition_uri.startswith('http://identifiers.org/chebi/CHEBI'):
                    item_definition_uri = 'http://identifiers.org/chebi/CHEBI:' + \
                        item_definition_uri

        # Create a dictionary entry for the item
        try:
            self.create_dictionary_entry(data, document_url, item_definition_uri)

        except Exception as e:
            return self.operation_failed(str(e))

        # Create an entry in SynBioHub
        try:
            document = sbol.Document()
            document.addNamespace('http://sd2e.org#', 'sd2')
            document.addNamespace('http://purl.org/dc/terms/', 'dcterms')
            document.addNamespace('http://www.w3.org/ns/prov#', 'prov')

            if sbol_type == 'component':
                if item_type == 'CHEBI':
                    item_sbol_type = item_definition_uri
                else:
                    item_sbol_type = sbol_type_map[ item_type ]

                component = sbol.ComponentDefinition(display_id, item_sbol_type)

                sbol.TextProperty(component, 'http://sd2e.org#stub_object', '0', '1', 'true')
                self.set_item_properties(component, data)

                document.addComponentDefinition(component)

            elif sbol_type == 'module':
                module = sbol.ModuleDefinition(display_id)
                sbol.TextProperty(module, 'http://sd2e.org#stub_object', '0', '1', 'true')

                module.roles = sbol_type_map[ item_type ]
                self.set_item_properties(module, data)

                document.addModuleDefinition(module)

            elif sbol_type == 'external':
                top_level = sbol.TopLevel('http://http://sd2e.org/types/#attribute', display_id)
                self.set_item_properties(top_level, data)

                document.addTopLevel(top_level)

            elif sbol_type == 'collection':
                collection = sbol.Collection(display_id)
                self.set_item_properties(collection, data)
                document.addCollection(collection)

            else:
                raise Exception()

            self.sbh.submit(document, self.sbh_collection_uri, 3)

            paragraph_index = data['selectionStartParagraph']
            offset = data['selectionStartOffset']
            end_offset = data['selectionEndOffset']

            action = self.link_text(paragraph_index, offset,
                                    end_offset, document_url)

        except Exception as e:
            self.logger.error(''.join(traceback.format_exception(etype=type(e),
                                                     value=e,
                                                     tb=e.__traceback__)))

            message = 'Failed to add "' + display_id + '" to SynBioHub'
            return self.operation_failed(message)

        return_info = {'actions': [action],
                       'results': {'operationSucceeded': True}
                      }

        return return_info

    def process_nop(self, httpMessage, sm):
        httpMessage # Fix unused warning
        sm # Fix unused warning
        return []

    def process_submit_form(self, httpMessage, sm):
        (json_body, client_state) = self.get_client_state(httpMessage)
        try:
            data = json_body['data']
            action = data['extra']['action']

            result = {}

            if action == 'submit':
                result = self.create_sbh_stub(data)
                if result['results']['operationSucceeded'] and data['isSpellcheck'] == 'True':
                    # store the link for any other matching results
                    curr_term = client_state['spelling_results'][ client_state["spelling_index"]]['term']
                    for r in client_state['spelling_results']:
                        if r['term'] == curr_term:
                            r['prev_link'] = result['actions'][0]['url']

                    client_state["spelling_index"] += 1
                    if client_state['spelling_index'] < client_state['spelling_size']:
                        for action in self.report_spelling_results(client_state):
                            result['actions'].append(action)
            elif action == 'submitLinkAll':
                result = self.create_sbh_stub(data)
                if result['results']['operationSucceeded']:
                    uri = result['actions'][0]['url']
                    data['extra']['link'] = uri
                    # Drop the link action, since we will add it again
                    result['actions'] = []
                    linkActions = self.process_form_link_all(data)
                    for action in linkActions:
                        result['actions'].append(action)
                    if bool(data['isSpellcheck']):
                        if self.spellcheck_remove_term(client_state):
                            reportActions = self.report_spelling_results(client_state)
                            for action in reportActions:
                                result['actions'].append(action)
            elif action == 'link':
                search_result = \
                    {'paragraph_index' : data['selectionStartParagraph'],
                     'offset'          : int(data['selectionStartOffset']),
                     'end_offset'      : int(data['selectionEndOffset']),
                     'uri'             : data['extra']['link']
                    }
                actions = self.add_link(search_result)
                result = {'actions': actions,
                          'results': {'operationSucceeded': True}
                }
                if data['isSpellcheck'] == 'True':
                    client_state["spelling_index"] += 1
                    if client_state['spelling_index'] < client_state['spelling_size']:
                        for action in self.report_spelling_results(client_state):
                            result['actions'].append(action)
            elif action == 'linkAll':
                actions = self.process_form_link_all(data)
                result = {'actions': actions,
                          'results': {'operationSucceeded': True}
                }
                if data['isSpellcheck'] == 'True':
                    if self.spellcheck_remove_term(client_state):
                        reportActions = self.report_spelling_results(client_state)
                        for action in reportActions:
                            result['actions'].append(action)

            elif action == 'createMeasurementTable':
                actions = self.process_create_measurement_table(data)
                result = {'actions': actions,
                          'results': {'operationSucceeded': True}
                }
            elif action == 'createParameterTable':
                actions.self.process_create_parameter_table(data)
                result = {'actions': actions,
                          'results': {'operationSucceeded': True}
                }
            else:
                self.logger.error('Unsupported form action: {}'.format(action))

            self.send_response(200, 'OK', json.dumps(result), sm,
                               'application/json')
        finally:
            self.release_connection(client_state)

    def process_create_measurement_table(self, data):
        """
        Process create measurement table
        """

        lab = "Lab: %s" % data['lab']
        num_reagents = int(data['numReagents'])
        has_temp = data['temperature']
        has_time = data['timepoint']
        has_ods  = data['ods']
        has_notes = data['notes']
        num_rows = int(data['numRows'])
        measurement_types = data['measurementTypes']
        file_types = data['fileTypes']

        num_cols = num_reagents + 4
        if has_time:
            num_cols += 1
        if has_temp:
            num_cols += 1

        col_sizes = []
        table_data = []
        header = []
        for __ in range(num_reagents):
            header.append('')
            col_sizes.append(4)

        header.append(constants.COL_HEADER_MEASUREMENT_TYPE)
        header.append(constants.COL_HEADER_FILE_TYPE)
        header.append(constants.COL_HEADER_REPLICATE)
        header.append(constants.COL_HEADER_STRAIN)

        col_sizes.append(len(constants.COL_HEADER_MEASUREMENT_TYPE) + 1)
        col_sizes.append(len(constants.COL_HEADER_FILE_TYPE) + 1)
        col_sizes.append(len(constants.COL_HEADER_REPLICATE) + 1)
        col_sizes.append(len(constants.COL_HEADER_STRAIN) + 1)
        if has_ods:
            header.append(constants.COL_HEADER_ODS)
            col_sizes.append(len(constants.COL_HEADER_ODS) + 1)
        if has_time:
            header.append(constants.COL_HEADER_TIMEPOINT)
            col_sizes.append(len(constants.COL_HEADER_TIMEPOINT) + 1)
        if has_temp:
            header.append(constants.COL_HEADER_TEMPERATURE)
            col_sizes.append(len(constants.COL_HEADER_TEMPERATURE) + 1)

        if has_notes:
            header.append(constants.COL_HEADER_NOTES)
            col_sizes.append(len(constants.COL_HEADER_NOTES) + 1)

        table_data.append(header)

        for r in range(num_rows):
            measurement_row = []
            for __ in range(num_reagents):
                measurement_row.append('')
            measurement_row.append(measurement_types[r]) # Measurement Type col
            measurement_row.append(file_types[r]) # File type col
            measurement_row.append('') # Replicate Col
            measurement_row.append('') # Strain col
            if has_ods:
                measurement_row.append('')
            if has_time:
                measurement_row.append('')
            if has_temp:
                measurement_row.append('')
            #measurement_row.append('') # Samples col
            if has_notes:
                measurement_row.append('')
            table_data.append(measurement_row)

        create_table = {}
        create_table['action'] = 'addTable'
        create_table['cursorChildIndex'] = data['cursorChildIndex']
        create_table['tableData'] = table_data
        create_table['tableType'] = 'measurements'
        create_table['tableLab'] = [[lab]]
        create_table['colSizes'] = col_sizes

        return [create_table]
    
    def process_create_parameter_table(self, data):
        col_sizes = [2]
        table_data = []
        
        header = [constants.COL_HEADER_PARAMETER, constants.COL_HEADER_PARAMETER_VALUE]
        table_data.append(header)
        
        for parameter_field in self.strateos_mapping:
            table_data.append([parameter_field, '']) 
                
        
        create_table = {}
        create_table['action'] = 'addTable'
        create_table['cursorChildIndex'] = data['cursorChildIndex']
        create_table['tableData'] = table_data
        create_table['tableType'] = 'parameters'
        create_table['colSizes'] = col_sizes
    
    def process_form_link_all(self, data):
        document_id = data['documentId']
        doc = self.google_accessor.get_document(
            document_id=document_id
        )
        body = doc.get('body');
        doc_content = body.get('content')
        paragraphs = self.get_paragraphs(doc_content)
        selected_term = data['selectedTerm']
        uri = data['extra']['link']

        actions = []

        pos = 0
        while True:
            result = self.find_exact_text(selected_term, pos, paragraphs)

            if result is None:
                break

            search_result = { 'paragraph_index' : result[0],
                              'offset'          : result[1],
                              'end_offset'      : result[1] + len(selected_term) - 1,
                              'term'            : selected_term,
                              'uri'             : uri,
                              'link'            : result[3],
                              'text'            : result[4]}
            # Only link terms that don't already have links
            if  search_result['link'] is None:
                actions += self.add_link(search_result)

            pos = result[2] + len(selected_term)

        return actions

    def process_search_syn_bio_hub(self, httpMessage, sm):
        json_body = self.get_json_body(httpMessage)
        data = json_body['data']

        try:
            offset = 0
            if 'offset' in data:
                offset = int(data['offset'])
            # Bounds check offset value
            if offset < 0:
                offset = 0
            if data['term'] in self.sparql_similar_count_cache:
                # Ensure offset isn't past the end of the results
                if offset > int(self.sparql_similar_count_cache[data['term']]) - self.sparql_limit:
                    offset = max(0, int(self.sparql_similar_count_cache[data['term']]) - self.sparql_limit)
            else:
                # Don't allow a non-zero offset if we haven't cached the size of the query
                if offset > 0:
                    offset = 0

            if 'analyze' in data:
                analyze = True
                filter_uri = data['selected_uri']
            else:
                analyze = False
                filter_uri = None

            search_results, results_count = self.simple_syn_bio_hub_search(data['term'], offset, filter_uri)

            table_html = ''
            for search_result in search_results:
                title = search_result['title']
                target = search_result['target']
                table_html += self.generate_existing_link_html(title, target, analyze)
            table_html += self.generate_results_pagination_html(offset, int(results_count))

            response = {'results':
                        {'operationSucceeded': True,
                         'search_results': search_results,
                         'table_html': table_html
                        }}


        except Exception as err:
            self.logger.error(str(err))
            response = self.operation_failed('Failed to search SynBioHub')

        self.send_response(200, 'OK', json.dumps(response), sm,
                           'application/json')

spreadsheet_id = '1oLJTTydL_5YPyk-wY-dspjIw_bPZ3oCiWiK0xtG8t3g' # Sd2 Program dict
# spreadsheet_id = '1wHX8etUZFMrvmsjvdhAGEVU1lYgjbuRX5mmYlKv7kdk' # Intent parser test dict
# spreadsheet_id = '1r3CIyv75vV7A7ghkB0od-TM_16qSYd-byAbQ1DhRgB0' #sd2 unit test dictionary 
sbh_spoofing_prefix=None
sbh_collection_uri = 'https://hub-staging.sd2e.org/user/sd2e/intent_parser/intent_parser_collection/1'
bind_port = 8081
bind_host = '0.0.0.0'

def usage():
    print('')
    print('intent_parser_server.py: [options]')
    print('')
    print('    -h --help            - show this message')
    print('    -p --pasword         - SynBioHub password')
    print('    -u --username        - SynBioHub username')
    print('    -c --collection      - collection url (default={})'.format(sbh_collection_uri))
    print('    -i --spreadsheet-id  - dictionary spreadsheet id (default={})'.format(spreadsheet_id))
    print('    -s --spoofing-prefix - SBH spoofing prefix (default={})'.format(sbh_spoofing_prefix))
    print('    -b --bind-host       - IP address to bind to (default={})'.format(bind_host))
    print('    -l --bind-port       - TCP Port to listen on (default={})'.format(bind_port))
    print('    -a --authn           - Authorization token for datacatalog (default=\'\')')
    print('')

def main(argv):
    sbh_username = None
    sbh_password = None

    global spreadsheet_id
    global sbh_spoofing_prefix
    global sbh_collection_uri
    global bind_port
    global bind_host
    global sbhPlugin
    global authn

    try:
        opts, __ = getopt.getopt(argv, "u:p:hc:i:s:b:l:a:",
                                   ["username=",
                                    "password=",
                                    "help",
                                    "collection=",
                                    "spreadsheet-id=",
                                    "spoofing-prefix=",
                                    "bind-host=",
                                    "bind-port=",
                                    "authn="])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2);

    for opt,arg in opts:
        if opt in ('-u', '--username'):
            sbh_username = arg

        elif opt in ('-p', '--password'):
            sbh_password = arg

        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)

        elif opt in ('-c', '--collection'):
            sbh_collection_uri = arg

        elif opt in ('-i', '--spreadsheet-id'):
            spreadsheet_id = arg

        elif opt in ('-s', '--spoofing-prefix'):
            sbh_spoofing_prefix = arg

        elif opt in ('-b', '--bind-host'):
            bind_host = arg

        elif opt in ('-l', '--bind-port'):
            bind_port = int(arg)

        elif opt in ('-a', '--authn'):
            authn = arg

    setup_logging()

    try:
        sbhPlugin = IntentParserServer(sbh_collection_uri=sbh_collection_uri,
                                       sbh_spoofing_prefix=sbh_spoofing_prefix,
                                       sbh_username=sbh_username,
                                       sbh_password=sbh_password,
                                       spreadsheet_id=spreadsheet_id,
                                       bind_ip=bind_host,
                                       bind_port=bind_port,
                                       datacatalog_authn=authn)
    except Exception as e:
        print(e)
        usage()
        sys.exit(5)

    sbhPlugin.serverRunLoop()

def setup_logging(
    default_path='logging.json',
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """
    Setup logging configuration
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'r') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level, format="[%(levelname)-8s] %(asctime)-24s %(filename)-23s line:%(lineno)-4s  %(message)s")
    logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.CRITICAL)
    logging.getLogger("googleapiclient.discovery").setLevel(logging.CRITICAL)

def signal_int_handler(sig, frame):
    '''  Handling SIG_INT: shutdown intent parser server and wait for it to finish.
    '''
    global sbhPlugin
    global sigIntCount

    sigIntCount += 1
    sig # Remove unused warning
    frame # Remove unused warning

    # Try to cleanly exit on the first try
    if sigIntCount == 1:
        print('\nStopping intent parser server...')
        sbhPlugin.stop()
    # If we receive enough SIGINTs, die
    if sigIntCount > 3:
        sys.exit(0)

signal.signal(signal.SIGINT, signal_int_handler)
sigIntCount = 0


if __name__ == "__main__":
    main(sys.argv[1:])