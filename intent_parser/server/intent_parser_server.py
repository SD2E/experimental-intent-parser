from http import HTTPStatus
from intent_parser.accessor.google_accessor import GoogleAccessor
from intent_parser.accessor.mongo_db_accessor import TA4DBAccessor
from intent_parser.accessor.strateos_accessor import StrateosAccessor
from intent_parser.accessor.sbol_dictionary_accessor import SBOLDictionaryAccessor
from intent_parser.accessor.tacc_go_accessor import TACCGoAccessor
from intent_parser.intent_parser_exceptions import ConnectionException, DictionaryMaintainerException, IntentParserException, TableException
from intent_parser.intent_parser_factory import IntentParserFactory
from intent_parser.intent_parser_sbh import IntentParserSBH
from intent_parser.table.intent_parser_table_type import TableType
from intent_parser.table.table_creator import TableCreator
from intent_parser.server.socket_manager import SocketManager
from multiprocessing import Pool
from operator import itemgetter
from spellchecker import SpellChecker
import intent_parser.server.http_message as http_message
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.constants.ip_app_script_constants as ip_addon_constants
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.utils.intent_parser_utils as intent_parser_utils
import intent_parser.utils.intent_parser_view as intent_parser_view
import argparse
import inspect
import json
import logging.config
import os
import socket
import threading
import time
import traceback

logger = logging.getLogger(__name__)


class IntentParserServer(object):

    dict_path = 'dictionaries'
    link_pref_path = 'link_pref'

    _curr_path = os.path.dirname(os.path.realpath(__file__))

    # Defines a period of time to wait to send analyze progress updates, in seconds
    ANALYZE_PROGRESS_PERIOD = 2.5

    # Defines how many processes are in the pool, for parallelisocket_manager
    MULTIPROCESSING_POOL_SIZE = 8

    # Terms below a certain size should be force to have an exact match
    PARTIAL_MATCH_MIN_SIZE = 3

    # Define the percentage of length of the search term that must
    # be matched in order to have a valid partial match
    PARTIAL_MATCH_THRESH = 0.75

    def __init__(self,
                 sbh, 
                 sbol_dictionary,
                 strateos_accessor,
                 intent_parser_factory,
                 bind_port,
                 bind_ip):
        self.sbh = sbh
        self.sbol_dictionary = sbol_dictionary
        self.strateos_accessor = strateos_accessor 
        self.intent_parser_factory = intent_parser_factory
        self.bind_port = bind_port
        self.bind_ip = bind_ip
       
        self.socket = None
        self.shutdownThread = False
        self.event = threading.Event()
        self.curr_running_threads = {}
        self.client_thread_lock = threading.Lock()

        if not os.path.exists(self.dict_path):
            os.makedirs(self.dict_path)
        if not os.path.exists(self.link_pref_path):
            os.makedirs(self.link_pref_path)

        self.sparql_similar_query = intent_parser_utils.load_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'findSimilar.sparql'))
        self.sparql_similar_count = intent_parser_utils.load_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'findSimilarCount.sparql'))
        self.sparql_similar_count_cache = {}

        self.spellCheckers = {}
        # Dictionary per-user that stores analyze associations to ignore
        self.analyze_never_link = {}
        self.analyze_processing_map = {}
        self.analyze_processing_map_lock = threading.Lock() # Used to lock the map
        self.analyze_processing_lock = {} # Used to indicate if the processing thread has finished, mapped to each doc_id
        self.client_state_map = {}
        self.client_state_lock = threading.Lock()
        self.initialized = False

    def initialize_server(self, init_sbh=True):
        """
        Initialize the server.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.socket.bind((self.bind_ip, self.bind_port))

        self.socket.listen(5)
        logger.info('listening on {}:{}'.format(self.bind_ip, self.bind_port))
        
        self.sbol_dictionary.start_synchronizing_spreadsheet()
        self.strateos_accessor.start_synchronize_protocols()

        if init_sbh:
            self.sbh.initialize_sbh()
        self.initialized = True
        
    def start(self, *, background=False):
        if not self.initialized:
            raise RuntimeError('Server has not been initialized.')
        if background:
            run_thread = threading.Thread(target=self.start)
            logger.info('Start background thread')
            run_thread.start()
            return

        logger.info('Start Listener')

        while True:
            try:
                if self.shutdownThread:
                    return

                client_sock, __ = self.socket.accept()
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
        logger.info('Connection')
        socket_manager = SocketManager(client_socket)
        try:
            while True:
                httpMessage = http_message.HttpMessage(socket_manager)

                if httpMessage.get_state() == http_message.State.ERROR:
                    client_socket.close()
                    return

                method = httpMessage.get_method()

                try:
                    if method == 'POST':
                        self.handle_POST(httpMessage, socket_manager)
                    elif method == 'GET':
                        self.handle_GET(httpMessage, socket_manager)
                    else:
                        response = self._create_http_response(HTTPStatus.NOT_IMPLEMENTED, 'Unrecognized request method\n')
                        response.send(socket_manager)
                except ConnectionException as ex:
                    response = self._create_http_response(ex.http_status, ex.content)
                    response.send(socket_manager)
                except Exception as ex:
                    logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
                    response = self._create_http_response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal Server Error\n')
                    response.send(socket_manager)
        except Exception as e:
            logger.info(''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)))

        client_socket.close()
        client_socket.shutdown(socket.SHUT_RDWR)
        
    def _create_http_response(self, http_status, content, content_type='text/html'):
        response = http_message.HttpMessage()
        response.set_response_code(http_status.value, http_status.name)
        response.set_header('content-type', content_type)
        response.set_body(content.encode('utf-8'))
        return response
    
    def handle_GET(self, http_message, socket_manager):
        resource = http_message.get_path()
        start = time.time() 
        if resource == "/status":
            response = self._create_http_response(HTTPStatus.OK, 'Intent Parser Server is Up and Running\n')
        elif resource == '/document_report':
            response = self.process_document_report(http_message)
        elif resource == '/document_request':
            response = self.process_document_request(http_message)
        elif resource =='/run_experiment':
            response = self.process_run_experiment(http_message)
        elif resource == '/experiment_request_documents':
            response = self.process_experiment_request_documents(http_message)
        elif resource == '/experiment_status':
            response = self.process_experiment_status(http_message)
        elif resource == '/update_experiment_status':
            response = self.process_update_experiment_status(http_message)
        elif resource == '/insert_table_hints':
            response = self.process_table_hints(http_message)
        else:
            response = self._create_http_response(HTTPStatus.NOT_FOUND, 'Resource Not Found')
            logger.warning('Did not find ' + resource)
        end = time.time()
        
        response.send(socket_manager)
        logger.info('Generated GET request for %s in %0.2fms' %(resource, (end - start) * 1000))
        
    def process_document_report(self, http_message):
        """
        Handles a request to generate a report
        """
        resource = http_message.get_resource()
        document_id = resource.split('?')[1]
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        report = intent_parser.generate_report() 
        return self._create_http_response(HTTPStatus.OK, json.dumps(report), 'application/json')

    def process_document_request(self, http_message):
        """
        Handles a request to generate a structured request 
        """
        resource = http_message.get_resource()
        document_id = resource.split('?')[1]
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        intent_parser.process_structure_request()
        if len(intent_parser.get_validation_errors()) > 0:
            return self._create_http_response(HTTPStatus.BAD_REQUEST,
                                              json.dumps({'errors': intent_parser.get_validation_errors()}),
                                              'application/json')
        
        return self._create_http_response(HTTPStatus.OK, json.dumps(intent_parser.get_structured_request()), 'application/json')

    def process_experiment_request_documents(self, http_message):
        """
        Retrieve experiment request documents.
        """
        drive_accessor = GoogleAccessor().get_google_drive_accessor(version=3)
        er_docs = drive_accessor.get_all_docs(intent_parser_constants.GOOGLE_DRIVE_EXPERIMENT_REQUEST_FOLDER)
        return self._create_http_response(HTTPStatus.OK,
                                          json.dumps({'docId': er_docs}),
                                          'application/json')

    def process_experiment_status(self, http_message):
        """
        Retrieve the statuses of an experiment from a google document.
        """
        resource = http_message.get_resource()
        document_id = resource.split('?')[1]
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        intent_parser.process_experiment_status_request()
        if len(intent_parser.get_validation_errors()) > 0:
            return self._create_http_response(HTTPStatus.BAD_REQUEST,
                                              json.dumps({'errors': intent_parser.get_validation_errors()}),
                                              'application/json')
        experiment_status = intent_parser.get_experiment_status_request()
        result = {dc_constants.LAB: experiment_status[dc_constants.LAB],
                  dc_constants.EXPERIMENT_ID: experiment_status[dc_constants.EXPERIMENT_ID]}
        for table_id, status_table in experiment_status[dc_constants.STATUS_ELEMENT].items():
            result[table_id] = status_table.to_dict()
        return self._create_http_response(HTTPStatus.OK,
                                          json.dumps(result),
                                          'application/json')

    def process_run_experiment(self, http_message):
        resource = http_message.get_resource()
        document_id = resource.split('?')[1]
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        intent_parser.process_experiment_run_request()
        if len(intent_parser.get_validation_errors()) > 0:
            errors = [intent_parser.get_validation_errors()]
            warnings = [intent_parser.get_validation_warnings()]
            return self._create_http_response(HTTPStatus.BAD_REQUEST,
                                              json.dumps({'errors': errors, 'warnings': warnings}),
                                              'application/json')

        request_data = intent_parser.get_experiment_request()
        experiment_response = TACCGoAccessor().execute_experiment(request_data)
        return self._create_http_response(HTTPStatus.OK, json.dumps({'result': experiment_response}),
                                          'application/json')

    def process_experiment_execution_status(self, json_body, client_state):
        execution_id = 'ZzL5p65NgyXw' # TODO: placeholder to assume authentication was successful. Will need to update to correct execution_id
        tacc_accessor = TACCGoAccessor()
        status = tacc_accessor.get_status_of_experiment(execution_id)
        return [intent_parser_view.message_dialog('Submission Status', status)]

    def process_execute_experiment(self, http_message):
        json_body = intent_parser_utils.get_json_body(http_message)
        http_host = http_message.get_header('Host')
        validation_errors = []
        validation_warnings = []
        if json_body is None or http_host is None:
            validation_errors.append('Unable to get information from Google document.')
        else:
            document_id = intent_parser_utils.get_document_id_from_json_body(json_body)
            intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
            intent_parser.process_experiment_run_request()
            validation_warnings.extend(intent_parser.get_validation_warnings())
            validation_errors.extend(intent_parser.get_validation_errors())

        action_list = []
        if len(validation_errors) == 0:
            request_data = intent_parser.get_experiment_request()
            response = TACCGoAccessor().execute_experiment(request_data)
            link = response.url
            action_list.append(intent_parser_view.create_execute_experiment_dialog(link, response.text))
        else:
            all_messages = []
            all_messages.extend(validation_warnings)
            all_messages.extend(validation_errors)
            dialog_action = intent_parser_view.invalid_request_model_dialog('Failed to execute experiment',
                                                                               all_messages)
            action_list.append(dialog_action)
        actions = {'actions': action_list}
        return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')

    def handle_POST(self, http_message, socket_manager):
        resource = http_message.get_resource()
        start = time.time()
        if resource == '/analyzeDocument':
            response = self.process_analyze_document(http_message)
        elif resource == '/addBySpelling':
            response = self.process_add_by_spelling(http_message)
        elif resource == '/addToSynBioHub':
            response = self.process_add_to_syn_bio_hub(http_message)
        elif resource == '/buttonClick':
            response = self.process_button_click(http_message)
        elif resource == '/calculateSamples':
            response = self.process_calculate_samples(http_message)
        elif resource == '/createTableTemplate':
            response = self.process_create_table_template(http_message)
        elif resource == '/executeExperiment':
            response = self.process_execute_experiment(http_message)
        elif resource == 'experimentExecutionStatus':
            response = self.process_experiment_execution_status(http_message)
        elif resource == '/generateStructuredRequest':
            response = self.process_generate_structured_request(http_message)
        elif resource == '/message':
            response = self.process_message(http_message)
        elif resource == '/reportExperimentStatus':
            response = self.process_report_experiment_status(http_message)
        elif resource == '/searchSynBioHub':
            response = self.process_search_syn_bio_hub(http_message)
        elif resource == '/submitForm':
            response = self.process_submit_form(http_message)
        elif resource == '/updateExperimentalResults':
            response = self.process_update_exp_results(http_message)
        elif resource == '/validateStructuredRequest':
            response = self.process_validate_structured_request(http_message)
        else:
            response = self._create_http_response(HTTPStatus.NOT_FOUND, 'Resource Not Found\n')
        end = time.time()
        response.send(socket_manager)
        logger.info('Generated POST request in %0.2fms, %s' %((end - start) * 1000, time.time()))

    def process_analyze_document(self, http_message):
        """
        This function will initiate an analysis if the document isn't currently being analyzed and
        then it will report on the progress of that document's analysis until it is done.  Once it's done
        this function will notify the client that the document is ready.
        """
        json_body = intent_parser_utils.get_json_body(http_message)
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body)

        self.analyze_processing_map_lock.acquire()
        docBeingProcessed = document_id in self.analyze_processing_map
        self.analyze_processing_map_lock.release()

        if docBeingProcessed:  # Doc being processed, check progress
            time.sleep(self.ANALYZE_PROGRESS_PERIOD)

            self.analyze_processing_map_lock.acquire()
            progress_percent = self.analyze_processing_map[document_id]
            self.analyze_processing_map_lock.release()

            if progress_percent < 100:  # Not done yet, update client
                action = {}
                action['action'] = 'updateProgress'
                action['progress'] = str(int(progress_percent * 100))
                actions = {'actions': [action]}
                return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
            else:  # Document is analyzed, start navigating results
                try:
                    self.analyze_processing_lock[
                        document_id].acquire()  # This ensures we've waited for the processing thread to release the client connection
                    (__, client_state) = self.get_client_state(http_message)
                    actionList = self.report_search_results(client_state)
                    actions = {'actions': actionList}
                    return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
                finally:
                    self.analyze_processing_map.pop(document_id)
                    self.analyze_processing_lock[document_id].release()
                    self.release_connection(client_state)
        else:  # Doc not being processed, spawn new processing thread
            self.analyze_processing_map[document_id] = 0
            analyze_thread = threading.Thread(
                target=self._initiate_document_analysis,
                args=(http_message,)  # without comma you'd get a... TypeError
            )
            analyze_thread.start()
            dialogAction = intent_parser_view.progress_sidebar_dialog()
            actions = {'actions': [dialogAction]}
            return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')

    def report_search_results(self, client_state):
        search_results = client_state['search_results']
        item_map = self.sbol_dictionary.get_common_names_to_uri()

        for search_result in search_results:
            term = search_result['term']
            link = search_result['link']
            
            if link != item_map[term]:
                document_id = client_state['document_id']
                uri = search_result['uri']
                content_term = search_result['text']
                paragraph_index = search_result['paragraph_index']
                offset = search_result['offset']
                end_offset = search_result['end_offset']
                return intent_parser_view.create_search_result_dialog(term, uri, content_term, document_id, paragraph_index, offset, end_offset)
                
        return [intent_parser_view.simple_sidebar_dialog('Finished Analyzing Document.', [])]
        
    def process_update_exp_results(self, http_message):
        """
        This function will scan SynbioHub for experiments related to this document, and updated an
        "Experiment Results" section with information about completed experiments.
        """
        json_body = intent_parser_utils.get_json_body(http_message)
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body) 
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        experimental_results = intent_parser.update_experimental_results()
        actions = {'actions': [experimental_results]}
        return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
        
    def process_calculate_samples(self, http_message):
        """
        Find all measurements tables and update the samples columns, or add the samples column if it doesn't exist.
        """
        json_body = intent_parser_utils.get_json_body(http_message)
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body) 
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        samples = intent_parser.calculate_samples()
        actions = {'actions': [samples]} 
        return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
    
    def process_submit_form(self, http_message):
        (json_body, client_state) = self.get_client_state(http_message)
        try:
            data = json_body['data']
            action = data['extra']['action']

            result = {}

            if action == 'submit':
                result = self.sbh.create_sbh_stub(data)
                if result['results']['operationSucceeded'] and data['isSpellcheck'] == 'True':
                    # store the link for any other matching results
                    curr_term = client_state['spelling_results'][ client_state["spelling_index"]]['term']
                    for r in client_state['spelling_results']:
                        if r['term'] == curr_term:
                            r['prev_link'] = result['actions'][0]['url']

                    client_state["spelling_index"] += 1
                    if client_state['spelling_index'] < client_state['spelling_size']:
                        for action in intent_parser_view.report_spelling_results(client_state):
                            result['actions'].append(action)
            elif action == 'submitLinkAll':
                result = self.sbh.create_sbh_stub(data)
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
                            reportActions = intent_parser_view.report_spelling_results(client_state)
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
                        for action in intent_parser_view.report_spelling_results(client_state):
                            result['actions'].append(action)
            elif action == 'linkAll':
                actions = self.process_form_link_all(data)
                result = {'actions': actions,
                          'results': {'operationSucceeded': True}
                }
                if data['isSpellcheck'] == 'True':
                    if self.spellcheck_remove_term(client_state):
                        reportActions = intent_parser_view.report_spelling_results(client_state)
                        for action in reportActions:
                            result['actions'].append(action)
            elif action == 'createControlsTable':
                actions = self.process_controls_table(data, json_body['documentId'])
                result = {'actions': actions,
                          'results': {'operationSucceeded': True}
                }
            elif action == 'createMeasurementTable':
                actions = self.process_create_measurement_table(data)
                result = {'actions': actions,
                          'results': {'operationSucceeded': True}
                }
            elif action == 'createParameterTable':
                actions = self.process_create_parameter_table(data)
                result = {'actions': actions,
                          'results': {'operationSucceeded': True}
                }
            else:
                logger.error('Unsupported form action: {}'.format(action))
            logger.info('Action: %s' % result)
            return self._create_http_response(HTTPStatus.OK, json.dumps(result), 'application/json')
        except (Exception, DictionaryMaintainerException) as err:
            logger.info('Action: %s resulted in exception %s' % (action, err))
            return self._create_http_response(HTTPStatus.INTERNAL_SERVER_ERROR, json.dumps(result), 'application/json')
        finally:
            self.release_connection(client_state)

    def spellcheck_add_ignore(self, json_body, client_state):
        """ Ignore button action for additions by spelling
        """
        json_body  # Remove unused warning
        client_state['spelling_index'] += 1
        if client_state['spelling_index'] >= client_state['spelling_size']:
            # We are at the end, nothing else to do
            return []
        else:
            return intent_parser_view.report_spelling_results(client_state)

    def spellcheck_add_ignore_all(self, json_body, client_state):
        """ Ignore All button action for additions by spelling
        """
        json_body  # Remove unused warning
        if self.spellcheck_remove_term(client_state):
            return intent_parser_view.report_spelling_results(client_state)

    def spellcheck_add_dictionary(self, json_body, client_state):
        """ Add to spelling dictionary button action for additions by spelling
        """
        json_body  # Remove unused warning
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
        # client_state["spelling_index"] += 1
        if client_state['spelling_index'] >= client_state['spelling_size']:
            # We are at the end, nothing else to do
            return []

        return intent_parser_view.report_spelling_results(client_state)

    def spellcheck_add_synbiohub(self, json_body, client_state):
        """ Add to SBH button action for additions by spelling
        """
        json_body  # Remove unused warning

        doc_id = client_state['document_id']
        spell_index = client_state['spelling_index']
        spell_check_result = client_state['spelling_results'][spell_index]
        select_start = spell_check_result['select_start']
        select_end = spell_check_result['select_end']

        start_paragraph = select_start['paragraph_index']
        start_offset = select_start['cursor_index']

        end_paragraph = select_end['cursor_index']
        end_offset = select_end['cursor_index'] + 1

        dialog_action = self.internal_add_to_syn_bio_hub(doc_id, start_paragraph, end_paragraph,
                                                         start_offset, end_offset)

        actionList = [dialog_action]

        client_state["spelling_index"] += 1
        if client_state['spelling_index'] < client_state['spelling_size']:
            for action in intent_parser_view.report_spelling_results(client_state):
                actionList.append(action)

        return actionList

    def internal_add_to_syn_bio_hub(self, document_id, start_paragraph, end_paragraph, start_offset, end_offset):
        try:

            item_type_list = []
            for sbol_type in intent_parser_constants.ITEM_TYPES:
                item_type_list += intent_parser_constants.ITEM_TYPES[sbol_type].keys()

            item_type_list = sorted(item_type_list)
            item_types_html = intent_parser_view.generate_html_options(item_type_list)

            lab_ids_html = intent_parser_view.generate_html_options(intent_parser_constants.LAB_IDS_LIST)

            try:
                lab_experiment = self.intent_parser_factory.create_lab_experiment(document_id)
                doc = lab_experiment.load_from_google_doc()
            except Exception as ex:
                errorMessage = (''.join(traceback.format_exception(etype=type(ex),
                                                         value=ex,
                                                         tb=ex.__traceback__)))
                raise ConnectionException(HTTPStatus.NOT_FOUND, errorMessage)

            body = doc.get('body');
            doc_content = body.get('content')
            paragraphs = self.get_paragraphs(doc_content)

            paragraph_text = self.get_paragraph_text(
                paragraphs[start_paragraph])

            selection = paragraph_text[start_offset:end_offset]
            # Remove leading/trailing space
            selection = selection.strip()
            display_id = self.sbh.sanitize_name_to_display_id(selection)
            dialog_action = intent_parser_view.create_add_to_synbiohub_dialog(selection,
                                   display_id,
                                   start_paragraph,
                                   start_offset,
                                   end_paragraph,
                                   end_offset,
                                   item_types_html,
                                   lab_ids_html,
                                   document_id,
                                   False)
            return dialog_action
        except Exception as e:
            raise e

    def get_paragraph_text(self, paragraph):
        elements = paragraph['elements']
        paragraph_text = ''

        for element_index in range(len(elements)):
            element = elements[element_index]

            if 'textRun' not in element:
                continue
            text_run = element['textRun']

            # end_index = element['endIndex']
            # start_index = element['startIndex']

            paragraph_text += text_run['content']

        return paragraph_text

    def char_is_not_wordpart(self, ch):
        """ Determines if a character is part of a word or not
        This is used when parsing the text to tokenize words.
        """
        return ch is not '\'' and not ch.isalnum()

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
        paragraph_text = self.get_paragraph_text(paragraphs[para_index])
        para_text_len = len(paragraph_text)

        # Determine which directions to search in, based on selection or removal, prev/next
        if isSelect:
            if isPrev:
                edge_check = lambda x: x > 0
                increment = -1
            else:
                edge_check = lambda x: x < para_text_len
                increment = 1
            firstCheck = self.char_is_not_wordpart
            secondCheck = lambda x: not self.char_is_not_wordpart(x)
        else:
            if isPrev:
                edge_check = lambda x: x < para_text_len
                increment = 1
            else:
                edge_check = lambda x: x > 0
                increment = -1
            secondCheck = self.char_is_not_wordpart
            firstCheck = lambda x: not self.char_is_not_wordpart(x)

        if starting_pos < 0:
            print('Error: got request to select previous, but the starting_pos was negative!')
            return

        if para_text_len < starting_pos:
            print('Error: got request to select previous, but the starting_pos was past the end!')
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

        return intent_parser_view.report_spelling_results(client_state)

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

    def get_paragraphs(self, element):
        return self.get_element_type(element, 'paragraph')

    def spellcheck_add_select_previous(self, json_body, client_state):
        """ Select previous word button action for additions by spelling
        """
        json_body  # Remove unused warning
        return self.spellcheck_select_word_from_text(client_state, True, True)

    def spellcheck_add_select_next(self, json_body, client_state):
        """ Select next word button action for additions by spelling
        """
        json_body  # Remove unused warning
        return self.spellcheck_select_word_from_text(client_state, False, True)

    def spellcheck_add_drop_first(self, json_body, client_state):
        """ Remove selection previous word button action for additions by spelling
        """
        json_body  # Remove unused warning
        return self.spellcheck_select_word_from_text(client_state, True, False)

    def spellcheck_add_drop_last(self, json_body, client_state):
        """ Remove selection next word button action for additions by spelling
        """
        json_body  # Remove unused warning
        return self.spellcheck_select_word_from_text(client_state, False, False)

    def process_form_link_all(self, data):
        document_id = data['documentId']
        lab_experiment = self.intent_parser_factory.create_lab_experiment(document_id)
        lab_experiment.load_from_google_doc()
        paragraphs = lab_experiment.paragraphs() 
        selected_term = data['selectedTerm']
        uri = data['extra']['link']

        actions = []

        pos = 0
        while True:
            result = intent_parser_utils.find_exact_text(selected_term, pos, paragraphs)

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

    def _get_button_id(self, data):
        if ip_addon_constants.BUTTON_ID not in data:
            error_message = 'Expected to get %s assigned to this HTTP data: %s but none was found.' % (ip_addon_constants.BUTTON_ID, data)
            raise ConnectionException(HTTPStatus.BAD_REQUEST, error_message)

        if type(data[ip_addon_constants.BUTTON_ID]) is dict:
            buttonDat = data[ip_addon_constants.BUTTON_ID]
            button_id = buttonDat[ip_addon_constants.BUTTON_ID]
            return button_id
        return data[ip_addon_constants.BUTTON_ID]

    def process_button_click(self, http_message):
        (json_body, client_state) = self.get_client_state(http_message)

        if 'data' not in json_body:
            error_message = 'Missing data'
            raise ConnectionException(HTTPStatus.BAD_REQUEST, error_message)
        data = json_body['data']

        button_id = self._get_button_id(data)
        method = getattr(self, button_id)

        try:
            action_list = method(json_body, client_state)
            actions = {'actions': action_list}
            return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
        except Exception as e:
            raise e
        finally:
            self.release_connection(client_state)
            
    def process_nop(self, http_message, sm):
        http_message # Fix unused warning
        sm # Fix unused warning
        return []
            
    def process_message(self, http_message):
        json_body = self.get_json_body(http_message)
        if 'message' in json_body:
            logger.info(json_body['message'])
        return self._create_http_response(HTTPStatus.OK, '{}', 'application/json')
    
    def process_validate_structured_request(self, http_message):
        """
        Generate a structured request from a given document, then run it against the validation.
        """
        json_body = intent_parser_utils.get_json_body(http_message)
        validation_errors = []
        validation_warnings = []
        if json_body is None:
            validation_errors.append('Unable to get information from Google document.')
        else:
            document_id = intent_parser_utils.get_document_id_from_json_body(json_body) 
            if 'data' in json_body and 'bookmarks' in json_body['data']:
                intent_parser = self.intent_parser_factory.create_intent_parser(document_id, bookmarks=json_body['data']['bookmarks'])
            else:
                intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
            intent_parser.process_structure_request()
            validation_warnings.extend(intent_parser.get_validation_warnings())
            validation_errors.extend(intent_parser.get_validation_errors())
        
        if len(validation_errors) == 0:
            dialog_action = intent_parser_view.valid_request_model_dialog(validation_warnings)
        else:
            all_errors = validation_warnings + validation_errors
            dialog_action = intent_parser_view.invalid_request_model_dialog('Structured request validation: Failed!', all_errors)
            
        actionList = [dialog_action]
        actions = {'actions': actionList}
        return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
    
    def process_generate_structured_request(self, http_message):
        """
        Validates then generates an HTML link to retrieve a structured request.
        """
        json_body = intent_parser_utils.get_json_body(http_message)
        http_host = http_message.get_header('Host')
        validation_errors = []
        validation_warnings = []
        if json_body is None or http_host is None:
            validation_errors.append('Unable to get information from Google document.')
        else:
            document_id = intent_parser_utils.get_document_id_from_json_body(json_body) 
            if 'data' in json_body and 'bookmarks' in json_body['data']:
                intent_parser = self.intent_parser_factory.create_intent_parser(document_id, bookmarks=json_body['data']['bookmarks'])
            else:
                intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
            intent_parser.process_structure_request()
            validation_warnings.extend(intent_parser.get_validation_warnings())
            validation_errors.extend(intent_parser.get_validation_errors())
       
        if len(validation_errors) == 0:
            dialog_action = intent_parser_view.valid_request_model_dialog(validation_warnings, intent_parser_view.get_download_link(http_host, document_id))
        else:
            all_messages = []
            all_messages.extend(validation_warnings)
            all_messages.extend(validation_errors)
            dialog_action = intent_parser_view.invalid_request_model_dialog('Structured request validation: Failed!', all_messages)
        actionList = [dialog_action]
        actions = {'actions': actionList}
        return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')

    def process_analyze_yes(self, json_body, client_state):
        """
        Handle "Yes" button as part of analyze document.
        """
        search_results = client_state[ip_addon_constants.ANALYZE_SEARCH_RESULTS]
        search_result_index = client_state[ip_addon_constants.ANALYZE_SEARCH_RESULT_INDEX]
        search_result = search_results[search_result_index]

        if type(json_body[ip_addon_constants.DATA][ip_addon_constants.BUTTON_ID]) is dict:
            new_link = json_body[ip_addon_constants.DATA][ip_addon_constants.BUTTON_ID][ip_addon_constants.ANALYZE_LINK]
        else:
            new_link = None

        actions = self.add_link(search_result, new_link)
        curr_idx = client_state[ip_addon_constants.ANALYZE_SEARCH_RESULT_INDEX]
        next_idx = curr_idx + 1
        new_search_results = search_results[1:]
        if len(new_search_results) < 1:
            return [intent_parser_view.simple_sidebar_dialog('Finished Analyzing Document.', [])]
        new_idx = new_search_results.index(search_results[next_idx])
        # Update client state
        client_state[ip_addon_constants.ANALYZE_SEARCH_RESULTS] = new_search_results
        client_state[ip_addon_constants.ANALYZE_SEARCH_RESULT_INDEX] = new_idx
        actions += self.report_search_results(client_state)
        return actions

    def process_analyze_no(self, json_body, client_state):
        """
        Handle "No" button as part of analyze document.
        """
        # Find out what term to point to
        curr_idx = client_state[ip_addon_constants.ANALYZE_SEARCH_RESULT_INDEX]
        next_idx = curr_idx + 1
        search_results = client_state[ip_addon_constants.ANALYZE_SEARCH_RESULTS]

        new_search_results = search_results[1:]
        if len(new_search_results) < 1:
            return [intent_parser_view.simple_sidebar_dialog('Finished Analyzing Document.', [])]
        new_idx = new_search_results.index(search_results[next_idx])
        # Update client state
        client_state[ip_addon_constants.ANALYZE_SEARCH_RESULTS] = new_search_results
        client_state[ip_addon_constants.ANALYZE_SEARCH_RESULT_INDEX] = new_idx
        return self.report_search_results(client_state)

    def process_link_all(self, json_body, client_state):
        """
        Handle "Link all" button as part of analyze document.
        """
        search_results = client_state['search_results']
        search_result_index = client_state['search_result_index']
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
        curr_idx = client_state['search_result_index']
        next_idx = curr_idx + 1
        search_results = client_state['search_results']
        while next_idx < len(search_results) and search_results[curr_idx]['term'] == search_results[next_idx]['term']:
            next_idx = next_idx + 1
        # Are we at the end? Then just exit
        if next_idx >= len(search_results):
            return [intent_parser_view.simple_sidebar_dialog('Finished Analyzing Document.', [])]

        term_to_ignore = search_results[curr_idx]['term']
        # Generate results without term to ignore
        new_search_results = [r for r in search_results if r['term'] != term_to_ignore]

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
        curr_idx = client_state[ip_addon_constants.ANALYZE_SEARCH_RESULT_INDEX]
        search_results = client_state[ip_addon_constants.ANALYZE_SEARCH_RESULTS]

        dict_term = search_results[curr_idx][ip_addon_constants.ANALYZE_TERM]
        content_text = search_results[curr_idx]['text']

        userId = client_state[ip_addon_constants.USER_ID]

        # Make sure we have a list of link preferences for this userId
        if userId not in self.analyze_never_link:
            link_pref_file = os.path.join(self.link_pref_path, userId + '.json')
            if os.path.exists(link_pref_file):
                try:
                    with open(link_pref_file, 'r') as fin:
                        self.analyze_never_link[userId] = json.load(fin)
                        logger.info('Loaded link preferences for userId, path: %s' % link_pref_file)
                except Exception as e:
                    logger.error('ERROR: Failed to load link preferences file!')
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
        except Exception as e:
            logger.error('ERROR: Failed to write link preferences file!')

        # Remove all of these associations from the results
        # This is different from "No to All", because that's only termed based
        # This depends on the term and the text
        next_idx = curr_idx + 1
        while next_idx < len(search_results) and search_results[curr_idx]['term'] == search_results[next_idx]['term'] and search_results[curr_idx]['text'] == search_results[next_idx]['text']:
            next_idx = next_idx + 1

        # Are we at the end? Then just exit
        if next_idx >= len(search_results):
            return [intent_parser_view.simple_sidebar_dialog('Finished Analyzing Document.', [])]

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
    
    def process_search_syn_bio_hub(self, http_message):
        json_body = intent_parser_utils.get_json_body(http_message)
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
                if offset > int(self.sparql_similar_count_cache[data['term']]) - intent_parser_constants.SPARQL_LIMIT:
                    offset = max(0, int(self.sparql_similar_count_cache[data['term']]) - intent_parser_constants.SPARQL_LIMIT)
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
                table_html += intent_parser_view.generate_existing_link_html(title, target, analyze)
            table_html += intent_parser_view.generate_results_pagination_html(offset, int(results_count))

            response = {'results':
                        {'operationSucceeded': True,
                         'search_results': search_results,
                         'table_html': table_html
                        }}


        except Exception as err:
            logger.error(str(err))
            return self._create_http_response(HTTPStatus.OK, json.dumps(intent_parser_view.operation_failed('Failed to search SynBioHub')), 'application/json')

        return self._create_http_response(HTTPStatus.OK, json.dumps(response), 'application/json')
        
    def process_create_table_template(self, http_message):
        """
        Process create table templates.
        """
        try:
            json_body = intent_parser_utils.get_json_body(http_message)
            data = json_body['data']
            cursor_child_index = str(data['childIndex'])
            table_type = data[ip_addon_constants.TABLE_TYPE]

            actionList = []
            if table_type == ip_addon_constants.TABLE_TYPE_CONTROLS:
                dialog_action = intent_parser_view.create_controls_table_dialog(cursor_child_index)
                actionList.append(dialog_action)
            elif table_type == ip_addon_constants.TABLE_TYPE_MEASUREMENTS:
                dialog_action = intent_parser_view.create_measurement_table_dialog(cursor_child_index)
                actionList.append(dialog_action)
            elif table_type == ip_addon_constants.TABLE_TYPE_PARAMETERS:
                protocol_options = list(intent_parser_constants.PROTOCOL_NAMES.values())
                dialog_action = intent_parser_view.create_parameter_table_dialog(cursor_child_index, protocol_options)
                actionList.append(dialog_action)
            else:
                logger.warning('WARNING: unsupported table type: %s' % table_type)

            actions = {'actions': actionList}
            return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
        except Exception as e:
            raise e

    def process_add_to_syn_bio_hub(self, http_message):
        try:
            json_body = intent_parser_utils.get_json_body(http_message)

            data = json_body['data']
            start = data['start']
            end = data['end']
            document_id = intent_parser_utils.get_document_id_from_json_body(json_body) 

            start_paragraph = start['paragraphIndex'];
            end_paragraph = end['paragraphIndex'];

            start_offset = start['offset']
            end_offset = end['offset']

            dialog_action = self._add_to_syn_bio_hub(document_id, start_paragraph, end_paragraph,
                                                             start_offset, end_offset)
            actionList = [dialog_action]
            actions = {'actions': actionList}
            return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')

        except Exception as e:
            raise e
    
    def _add_to_syn_bio_hub(self, document_id, start_paragraph, end_paragraph, start_offset, end_offset, isSpellcheck=False):
        try:

            item_type_list = []
            for sbol_type in intent_parser_constants.ITEM_TYPES:
                item_type_list += intent_parser_constants.ITEM_TYPES[sbol_type].keys()

            item_type_list = sorted(item_type_list)
            item_types_html = intent_parser_view.generate_html_options(item_type_list)
            lab_ids_html = intent_parser_view.generate_html_options(intent_parser_constants.LAB_IDS_LIST)

            ip = self.intent_parser_factory.create_intent_parser(document_id)
            selection, display_id = ip.generate_displayId_from_selection(start_paragraph, start_offset, end_offset)
            return intent_parser_view.create_add_to_synbiohub_dialog(selection, 
                                   display_id, 
                                   start_paragraph, 
                                   start_offset, 
                                   end_paragraph, 
                                   end_offset, 
                                   item_types_html,
                                   lab_ids_html, 
                                   document_id, 
                                   isSpellcheck)
        except Exception as e:
            raise e

    def process_add_by_spelling(self, http_message):
        """ 
        Function that sets up the results for additions by spelling
        This will start from a given offset (generally 0) and searches the rest of the
        document, looking for words that are not in the dictionary.  Any words that
        don't match are then used as suggestions for additions to SynBioHub.

        Users can add words to the dictionary, and added words are saved by a user id.
        This comes from the email address, but if that's not available the document id
        is used instead.
        """
        try:
            client_state = None
            json_body = intent_parser_utils.get_json_body(http_message)
            document_id = intent_parser_utils.get_document_id_from_json_body(json_body) 
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
                    logger.info('Loaded dictionary for userId, path: %s' % dict_path)
                    self.spellCheckers[userId].word_frequency.load_dictionary(dict_path)

            lab_experiment = self.intent_parser_factory.create_lab_experiment(document_id)
            doc = lab_experiment.load_from_google_doc()
            paragraphs = lab_experiment.paragraphs() 
            if 'data' in json_body:
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
                    endIdx = len(content)
                    currIdx = wordStart + 1
                    while currIdx < endIdx:
                        # Check for end of word
                        if intent_parser_utils.char_is_not_wordpart(content[currIdx]):
                            word = content[wordStart:currIdx]
                            word = intent_parser_utils.strip_leading_trailing_punctuation(word)
                            word = word.lower()
                            if not word in self.spellCheckers[userId] and not intent_parser_utils.should_ignore_token(word):
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
                            while currIdx < endIdx and intent_parser_utils.char_is_not_wordpart(content[currIdx]):
                                currIdx += 1
                            # Store word start
                            wordStart = currIdx
                            currIdx += 1
                        else: # continue until we find word end
                            currIdx += 1

                    # Check for tailing word that wasn't processed
                    if currIdx - wordStart > 1:
                        word = content[wordStart:currIdx]
                        word = intent_parser_utils.strip_leading_trailing_punctuation(word)
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

            # If we have a spelling mistake, highlight text and update user
            if len(spellCheckResults) > 0:
                client_state['spelling_results'] = spellCheckResults
                client_state['spelling_index'] = 0
                client_state['spelling_size'] = len(spellCheckResults)
                actionList = intent_parser_view.report_spelling_results(client_state)
                actions = {'actions': actionList}
                return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
            else: # No spelling mistakes!
                buttons = [('Ok', 'process_nop')]
                dialog_action = intent_parser_view.simple_modal_dialog('Found no words not in spelling dictionary!', buttons, 'No misspellings!', 400, 450)
                actionList = [dialog_action]
                actions = {'actions': actionList}  
                return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')

        except Exception as e:
            raise e

        finally:
            if client_state is not None:
                self.release_connection(client_state)
                
    def process_create_measurement_table(self, data):
        lab_data = self.process_lab_table(data)
        table_template = []
        header_row = [intent_parser_constants.HEADER_MEASUREMENT_TYPE_VALUE,
                      intent_parser_constants.HEADER_FILE_TYPE_VALUE,
                      intent_parser_constants.HEADER_REPLICATE_VALUE,
                      intent_parser_constants.HEADER_STRAINS_VALUE]
        if data[ip_addon_constants.HTML_BATCH]:
            header_row.append(intent_parser_constants.HEADER_BATCH_VALUE)
        if data[ip_addon_constants.HTML_TEMPERATURE]:
            header_row.append(intent_parser_constants.HEADER_TEMPERATURE_VALUE)
        if data[ip_addon_constants.HTML_TIMEPOINT]:
            header_row.append(intent_parser_constants.HEADER_TIMEPOINT_VALUE)
        if data[ip_addon_constants.HTML_ODS]:
            header_row.append(intent_parser_constants.HEADER_ODS_VALUE)
        if data[ip_addon_constants.HTML_NOTES]:
            header_row.append(intent_parser_constants.HEADER_NOTES_VALUE)
        if data[ip_addon_constants.HTML_CONTROLS]:
            header_row.append(intent_parser_constants.HEADER_CONTROL_VALUE)
        if data[ip_addon_constants.HTML_COL_ID]:
            header_row.append(intent_parser_constants.HEADER_COLUMN_ID_VALUE)
        if data[ip_addon_constants.HTML_ROW_ID]:
            header_row.append(intent_parser_constants.HEADER_ROW_ID_VALUE)
        if data[ip_addon_constants.HTML_LAB_ID]:
            header_row.append(intent_parser_constants.HEADER_LAB_ID_VALUE)
        if data[ip_addon_constants.HTML_NUM_OF_REAGENTS] and \
           data[ip_addon_constants.HTML_REAGENT_TIMEPOINT_VALUE] and \
           data[ip_addon_constants.HTML_REAGENT_TIMEPOINT_UNIT]:
            timepoint_value = data[ip_addon_constants.HTML_REAGENT_TIMEPOINT_VALUE]
            timepoint_unit = data[ip_addon_constants.HTML_REAGENT_TIMEPOINT_UNIT]
            num_of_reagent = data[ip_addon_constants.HTML_NUM_OF_REAGENTS]
            header_row.extend(['Reagent %d @ %s %s' % (reagent_index+1, timepoint_value, timepoint_unit) for reagent_index in range(int(num_of_reagent))])
        table_template.append(header_row)

        measurement_types = data[ip_addon_constants.HTML_MEASUREMENT_TYPES]
        file_types = data[ip_addon_constants.HTML_FILE_TYPES]
        # column_offset = column size - # of columns with generated default value
        column_offset = len(header_row) - 2
        for row_index in range(int(data[ip_addon_constants.HTML_NUM_OF_ROW])):
            curr_row = [measurement_types[row_index],
                        file_types[row_index]]
            curr_row.extend(['' for _ in range(column_offset)])
            table_template.append(curr_row)
        default_col_width = 4
        column_width = [len(header) if len(header) != 0 else default_col_width for header in header_row]
        return intent_parser_view.create_table_template(data[ip_addon_constants.CURSOR_CHILD_INDEX],
                                                        table_template,
                                                        ip_addon_constants.TABLE_TYPE_MEASUREMENTS,
                                                        column_width,
                                                        additional_info={ip_addon_constants.TABLE_TYPE_LAB: lab_data})

    def process_lab_table(self, data):
        table_template = []
        lab_name = "%s: %s" % (intent_parser_constants.HEADER_LAB_VALUE, data[ip_addon_constants.HTML_LAB])
        experiment_id = '%s: ' % intent_parser_constants.HEADER_EXPERIMENT_ID_VALUE
        table_template.append([lab_name])
        table_template.append([experiment_id])
        return table_template

    def _process_new_table_index(self, document_id):
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        intent_parser.process_table_indices()
        return intent_parser.get_largest_table_index()+1
    
    def process_controls_table(self, data, document_id):
        table_index = self._process_new_table_index(document_id)
        table_template = []
        header_row = [intent_parser_constants.HEADER_CONTROL_TYPE_VALUE,
                      intent_parser_constants.HEADER_STRAINS_VALUE]
        if data[ip_addon_constants.HTML_CHANNEL]:
            header_row.append(intent_parser_constants.HEADER_CHANNEL_VALUE)
        if data[ip_addon_constants.HTML_CONTENT]:
            header_row.append(intent_parser_constants.HEADER_CONTENTS_VALUE)
        if data[ip_addon_constants.HTML_TIMEPOINT]:
            header_row.append(intent_parser_constants.HEADER_TIMEPOINT_VALUE)
        
        # column_offset = column size - # of columns with generated default value
        column_offset = len(header_row) - 1
        if data[ip_addon_constants.HTML_CAPTION]:
            table_caption = ['Table %d: Control' % table_index]
            table_caption.extend(['' for _ in range(column_offset)])
            table_template.append(table_caption)
        table_template.append(header_row)
        for control_type in data[ip_addon_constants.HTML_CONTROL_TYPES]:
            curr_row = [control_type]
            curr_row.extend(['' for _ in range(column_offset)])
            table_template.append(curr_row)
        column_width = [len(header) for header in header_row]
        return intent_parser_view.create_table_template(data[ip_addon_constants.CURSOR_CHILD_INDEX],
                                                        table_template,
                                                        ip_addon_constants.TABLE_TYPE_CONTROLS,
                                                        column_width)

    def process_update_experiment_status(self, http_message):
        resource = http_message.get_resource()
        document_id = resource.split('?')[1]
        try:
            self._report_experiment_status(document_id)
        except (IntentParserException, TableException) as err:
            all_errors = [err.get_message()]
            return self._create_http_response(HTTPStatus.OK,
                                              json.dumps({'status': 'updated',
                                                          'messages': all_errors}),
                                              'application/json')

        return self._create_http_response(HTTPStatus.OK,
                                          json.dumps({'status': 'updated',
                                                      'messages': []}),
                                          'application/json')

    def _create_experiment_specification_table(self, document_id, experiment_specification_table):
        table_creator = TableCreator()
        table_creator.create_experiment_specification_table(document_id, experiment_specification_table)

    def _update_experiment_specification_table(self, document_id, experiment_specification_table, new_spec_table):
        table_creator = TableCreator()
        table_creator.update_experiment_specification_table(document_id, experiment_specification_table, new_spec_table)

    def _update_experiment_status_table(self, document_id, experiment_status_table, db_statuses_table):
        table_creator = TableCreator()
        table_creator.update_experiment_status_table(document_id, experiment_status_table, db_statuses_table)

    def _add_experiment_status_table(self, document_id, new_table):
        table_creator = TableCreator()
        table_creator.create_experiment_status_table(document_id, new_table)

    def _report_experiment_status(self, document_id):
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        intent_parser.process_experiment_status_request()
        experiment_status = intent_parser.get_experiment_status_request()
        lab_name = experiment_status[dc_constants.LAB]
        exp_id_to_ref_table = experiment_status[dc_constants.EXPERIMENT_ID]
        ref_table_to_statuses = experiment_status[dc_constants.STATUS_ELEMENT]

        db_exp_id_to_statuses = TA4DBAccessor().get_experiment_status(document_id, lab_name)
        if not db_exp_id_to_statuses:
            experiment_ref = intent_parser_constants.GOOGLE_DOC_URL_PREFIX + document_id
            raise IntentParserException(
                'TA4\'s pipeline has no information to report for %s under experiment %s.' % (lab_name, experiment_ref))

        if exp_id_to_ref_table:
            self._delete_experiment_status_from_document(intent_parser, document_id)
        self._process_new_experiment_status(db_exp_id_to_statuses, intent_parser, document_id)

    def _delete_experiment_status_from_document(self, intent_parser, document_id):
        ip_tables = intent_parser.get_tables_by_type()
        tables_to_delete = ip_tables[TableType.EXPERIMENT_SPECIFICATION]
        tables_to_delete.extend(ip_tables[TableType.EXPERIMENT_STATUS])
        table_creator = TableCreator()
        table_creator.delete_tables(tables_to_delete, document_id)

    def _process_new_experiment_status(self, db_exp_id_to_statuses, intent_parser, document_id):
        created_statuses = {}
        for db_experiment_id, db_statuses_table in db_exp_id_to_statuses.items():
            new_table = intent_parser.create_experiment_status_table(db_statuses_table.get_statuses())
            self._add_experiment_status_table(document_id, new_table)
            created_statuses[db_experiment_id] = new_table.get_table_caption()
        self._process_new_experiment_specification(created_statuses, intent_parser, document_id)

    def _process_new_experiment_specification(self, created_statuses, intent_parser, document_id):
        new_spec_table = intent_parser.create_experiment_specification_table(experiment_id_with_indices=created_statuses)
        self._create_experiment_specification_table(document_id, new_spec_table)

    def process_report_experiment_status(self, http_message):
        """Report the status of an experiment by inserting experiment specification and status tables."""
        json_body = intent_parser_utils.get_json_body(http_message)
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body)
        logger.warning('Processing document id: %s' % document_id)

        action_list = []
        try:
            self._report_experiment_status(document_id)
            action_list.append(intent_parser_view.message_dialog('Report Experiment Status', 'Complete'))
        except (IntentParserException, TableException) as err:
            all_errors = [err.get_message()]
            dialog_action = intent_parser_view.invalid_request_model_dialog('Failed to report experiment status',
                                                                            all_errors)
            action_list = [dialog_action]
        actions = {'actions': action_list}
        return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')

    def process_create_experiment_specification_table(self, status_tables, table_index=None):
        table_template = []
        table_caption = ['Table %d: Experiment Specification' % table_index]
        table_caption.extend(['' for _ in range(1)])
        header_row = [intent_parser_constants.HEADER_EXPERIMENT_ID_VALUE,
                      intent_parser_constants.HEADER_EXPERIMENT_STATUS_VALUE]
        table_template.append(header_row)

        for experiment_id, status_table_index in status_tables.items():
            table_template.append([experiment_id, 'Table %d' % status_table_index])
        column_width = [len(header) for header in header_row]
        return table_template, column_width

    def process_create_parameter_table(self, data):
        table_template = []
        header_row = [intent_parser_constants.HEADER_PARAMETER_VALUE,
                      intent_parser_constants.HEADER_PARAMETER_VALUE_VALUE]
        table_template.append(header_row)
        selected_protocol = data[ip_addon_constants.HTML_PROTOCOL]
        protocols = [key for key, value in intent_parser_constants.PROTOCOL_NAMES.items() if value == selected_protocol]
        strateos_protocol = protocols[0]
        if strateos_protocol not in intent_parser_constants.PROTOCOL_NAMES.keys():
            raise ConnectionException(HTTPStatus.BAD_REQUEST, 'Invalid protocol specified.')

        table_template.append([intent_parser_constants.PARAMETER_PROTOCOL, strateos_protocol])
        protocol_default_value = self.strateos_accessor.get_protocol(strateos_protocol)
        for protocol_key, protocol_value in protocol_default_value.items():
            common_name = self.sbol_dictionary.get_common_name_from_transcriptic_id(protocol_key)
            if common_name:
                table_template.append([common_name, protocol_value])
            else:
                logger.warning('Unable to locate %s as a Strateos UID in SBOL Dictionary.' % protocol_key)

        column_width = [len(header) for header in header_row]
        return intent_parser_view.create_table_template(data[ip_addon_constants.CURSOR_CHILD_INDEX],
                                                        table_template,
                                                        ip_addon_constants.TABLE_TYPE_PARAMETERS,
                                                        column_width)

    def get_client_state(self, http_message):
        json_body = intent_parser_utils.get_json_body(http_message)
        if ip_addon_constants.DOCUMENT_ID not in json_body:
            raise ConnectionException(HTTPStatus.BAD_REQUEST,
                                      'Expecting to get a %s from this http_message: %s but none was given' % (ip_addon_constants.DOCUMENT_ID, http_message))
        document_id = json_body[ip_addon_constants.DOCUMENT_ID]
        try:
            client_state = self.get_connection(document_id)
        except:
            client_state = None

        return (json_body, client_state)
    
    def add_link(self, search_result, new_link=None):
        """ Add a hyperlink to the desired search_result
        """
        paragraph_index = search_result[ip_addon_constants.ANALYZE_PARAGRAPH_INDEX]
        offset = search_result[ip_addon_constants.ANALYZE_OFFSET]
        end_offset = search_result[ip_addon_constants.ANALYZE_END_OFFSET]
        if new_link is None:
            link = search_result['uri']
        else:
            link = new_link
        search_result[ip_addon_constants.ANALYZE_LINK] = link

        action = intent_parser_view.link_text(paragraph_index, offset,
                                end_offset, link)

        return [action]
    
    def _initiate_document_analysis(self, http_message):
        """
        This function does the actual work of analyzing the document, and is designed to be run in a separate thread.
        This will process the document and update a status container.  The client will keep pinging the server for status
        while the document is being analyzed and the server will either return the progress percentage, or indicate that the
        results are ready.
        """
        json_body = intent_parser_utils.get_json_body(http_message)
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body) 
        
        lab_experiment = self.intent_parser_factory.create_lab_experiment(document_id)
        doc = lab_experiment.load_from_google_doc()
         
        self.analyze_processing_lock[document_id] = threading.Lock()
        self.analyze_processing_lock[document_id].acquire()

        user = json_body['user']
        userEmail = json_body['userEmail']

        if userEmail:
            userId = userEmail
        elif user:
            userId = user
        else:
            userId = document_id

        client_state = self.new_connection(document_id)
        client_state['doc'] = doc
        client_state['user_id'] = userId

        paragraphs = lab_experiment.paragraphs() 
        if 'data' in json_body:
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
            self._analyze_document(client_state, start_offset)
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

    def _analyze_document(self, client_state, start_offset):
        self.analyze_processing_map_lock.acquire()
        self.analyze_processing_map[client_state['document_id']] = 0
        self.analyze_processing_map_lock.release()

        doc_id = client_state['document_id']
        lab_experiment = self.intent_parser_factory.create_lab_experiment(doc_id)
        lab_experiment.load_from_google_doc()
        paragraphs = lab_experiment.paragraphs()

        item_map = self.sbol_dictionary.get_common_names_to_uri()

        analyze_inputs = []
        item_map_size = len(item_map) if len(item_map) > 0 else 1
        progress_per_term = 1.0 / item_map_size
        if client_state['user_id'] in self.analyze_never_link:
            link_prefs = self.analyze_never_link[client_state['user_id']]
        else:
            link_prefs = {}
        for term in item_map.keys():
            analyze_inputs.append([term, start_offset, paragraphs, self.PARTIAL_MATCH_MIN_SIZE, self.PARTIAL_MATCH_THRESH, item_map[term]])
        search_results = []
        with Pool(self.MULTIPROCESSING_POOL_SIZE) as p:
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
        search_results = intent_parser_utils.cull_overlapping(search_results);
        search_results = sorted(search_results,key=itemgetter('paragraph_index','offset'))

        client_state['search_results'] = search_results
        client_state['search_result_index'] = 0

        self.analyze_processing_map_lock.acquire()
        self.analyze_processing_map[client_state['document_id']] = 100
        self.analyze_processing_map_lock.release()
    
    def new_connection(self, document_id):
        self.client_state_lock.acquire()
        if document_id in self.client_state_map:
            if self.client_state_map[document_id]['locked']:
                self.client_state_lock.release()
                raise ConnectionException(HTTPStatus.SERVICE_UNAVAILABLE, 'This document is busy')

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
            raise ConnectionException(HTTPStatus.BAD_REQUEST,
                                      'Invalid session')

        client_state = self.client_state_map[document_id]

        if client_state['locked']:
            self.client_state_lock.release()
            raise ConnectionException(HTTPStatus.SERVICE_UNAVAILABLE, 'This document is busy')
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
                logger.error('Error: releasing client_state, but it is not locked! doc_id: %s, called by %s' % (document_id, inspect.currentframe().f_back.f_code.co_name))
            client_state['locked'] = False

        self.client_state_lock.release()

    def stop(self):
        """Stop all jobs running on intent table server
        """
        self.initialized = False
        logger.info('Signaling shutdown...')
        self.shutdownThread = True
        self.event.set()
        if self.sbh is not None:
            self.sbh.stop()
            logger.info('Stopped SynBioHub')
        if self.sbol_dictionary is not None:
            self.sbol_dictionary.stop_synchronizing_spreadsheet()
            logger.info('Stopped caching SBOL Dictionary.')
        if self.strateos_accessor is not None:
            self.strateos_accessor.stop_synchronizing_protocols()
            logger.info('Stopped caching Strateos protocols.')
        if self.socket is not None:
            logger.info('Closing server...')
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except OSError:
                return
            for key in self.curr_running_threads.keys():
                client_thread = self.curr_running_threads[key]
                if client_thread.is_alive():
                    client_thread.join()
                    
        logger.info('Shutdown complete')

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

  
    def simple_syn_bio_hub_search(self, term, offset=0, filter_uri=None):
        """
        Search for similar terms in SynbioHub, using the cached sparql similarity query.
        This query requires the specification of a term, a limit on the number of results, and an offset.
        """
        if filter_uri is None:
            extra_filter = ''
        else:
            extra_filter = 'FILTER( !regex(?member, "%s"))' % filter_uri

        if offset == 0 or term not in self.sparql_similar_count_cache:
            sparql_count = self.sparql_similar_count.replace('${TERM}', term).replace('${EXTRA_FILTER}', extra_filter)
            query_results = self.sbh.query(sparql_count)
            bindings = query_results['results']['bindings']
            self.sparql_similar_count_cache[term] = bindings[0]['count']['value']

        sparql_query = self.sparql_similar_query.replace('${TERM}', term).replace('${LIMIT}', str(intent_parser_constants.SPARQL_LIMIT)).replace('${OFFSET}', str(offset)).replace('${EXTRA_FILTER}', extra_filter)
        query_results = self.sbh.query(sparql_query)
        bindings = query_results['results']['bindings']
        search_results = []
        for binding in bindings:
            title = binding['title']['value']
            target = binding['member']['value']
            if self.sbh.get_sbh_spoofing_prefix() is not None:
                target = target.replace(self.sbh.get_sbh_spoofing_prefix(), self.sbh.get_sbh_url())
            search_results.append({'title': title, 'target': target})

        return search_results, self.sparql_similar_count_cache[term]

def setup_logging(
    default_path='logging.json',
    default_level=logging.DEBUG,
    env_key='LOG_CFG'):
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
    
    logger.addHandler(logging.FileHandler('intent_parser_server.log'))
    logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.CRITICAL)
    logging.getLogger("googleapiclient.discovery").setLevel(logging.CRITICAL)

def main():
    parser = argparse.ArgumentParser(description='Processes an experimental design.')
    parser.add_argument('-a', '--authn', nargs='?',
                            required=True, help='Authorization token for data catalog.')
    
    parser.add_argument('-b', '--bind-host', nargs='?', default='0.0.0.0',
                            required=False, help='IP address to bind to.')
    
    parser.add_argument('-c', '--collection', nargs='?',
                            required=True, help='Collection url.')
    
    parser.add_argument('-i', '--spreadsheet-id', nargs='?', default=intent_parser_constants.SD2_SPREADSHEET_ID,
                            required=False, help='Dictionary spreadsheet id.')
    
    parser.add_argument('-l', '--bind-port', nargs='?', type=int, default=8081, 
                            required=False, help='TCP Port to listen on.')
    
    parser.add_argument('-p', '--password', nargs='?', 
                            required=True, help='SynBioHub password.')
    
    parser.add_argument('-s', '--spoofing-prefix', nargs='?', 
                            required=False, help='SBH spoofing prefix.')

    parser.add_argument('-t', '--transcriptic', nargs='?', 
                            required=False, help='Path to transcriptic configuration file.')

    parser.add_argument('-e', '--execute_experiment', nargs='?',
                        required=False, help='Nonce credential used for authorizing an API endpoint to execute an experiment.')

    parser.add_argument('-u', '--username', nargs='?', 
                            required=True, help='SynBioHub username.')
    
    input_args = parser.parse_args()
    setup_logging()
    intent_parser_server = None
    try:
        sbh = IntentParserSBH(sbh_collection_uri=input_args.collection,
                 spreadsheet_id=intent_parser_constants.SD2_SPREADSHEET_ID,
                 sbh_username=input_args.username, 
                 sbh_password=input_args.password,
                 sbh_spoofing_prefix=input_args.spoofing_prefix)
        sbol_dictionary = SBOLDictionaryAccessor(intent_parser_constants.SD2_SPREADSHEET_ID, sbh) 
        datacatalog_config = {"mongodb": {"database": "catalog_staging", "authn": input_args.authn}}
        strateos_accessor = StrateosAccessor(input_args.transcriptic)
        intent_parser_factory = IntentParserFactory(datacatalog_config, sbh, sbol_dictionary)
        intent_parser_server = IntentParserServer(sbh, sbol_dictionary, strateos_accessor, intent_parser_factory,
                                                  bind_ip=input_args.bind_host,
                                                  bind_port=input_args.bind_port)
        intent_parser_server.initialize_server()
        intent_parser_server.start() 
    except (KeyboardInterrupt, SystemExit) as ex:
        return
    except Exception as ex:
        logger.warning(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
    finally:
        if intent_parser_server is not None:
            intent_parser_server.stop()

if __name__ == "__main__":
    main()
