from http import HTTPStatus
from intent_parser_exceptions import ConnectionException, DictionaryMaintainerException
from intent_parser_factory import IntentParserFactory
from intent_parser_sbh import IntentParserSBH
from multiprocessing import Pool
from operator import itemgetter
from sbol_dictionary_accessor import SBOLDictionaryAccessor
from socket_manager import SocketManager
from spellchecker import SpellChecker
from strateos_accessor import StrateosAccessor
import argparse
import http_message
import inspect
import intent_parser_constants
import intent_parser_utils
import intent_parser_view 
import json
import logging.config
import os
import signal
import socket
import sys
import threading
import time
import traceback

class IntentParserServer:

    logger = logging.getLogger('intent_parser_server')

    DICT_PATH = 'dictionaries'
    LINK_PREF_PATH = 'link_pref'

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
        self.strateos_accessor = strateos_accessor #TODO: add to config file login account
        self.intent_parser_factory = intent_parser_factory
        
        self.bind_port = bind_port
        self.bind_ip = bind_ip
        fh = logging.FileHandler('intent_parser_server.log')
        self.logger.addHandler(fh)
       
        self.socket = None
        self.shutdownThread = False
        self.event = threading.Event()
        self.curr_running_threads = {}
        self.client_thread_lock = threading.Lock() 
        self.sparql_similar_count_cache = {}
        self.spellCheckers = {}
        # Dictionary per-user that stores analyze associations to ignore
        self.analyze_never_link = {}
        self.analyze_processing_map = {}
        self.analyze_processing_map_lock = threading.Lock() # Used to lock the map
        self.analyze_processing_lock = {} # Used to indicate if the processing thread has finished, mapped to each doc_id
        self.client_state_map = {}
        self.client_state_lock = threading.Lock()
        self.item_map_lock = threading.Lock()
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
        self.logger.info('listening on {}:{}'.format(self.bind_ip, self.bind_port))
        
        self.item_map_lock.acquire()
        self.item_map = self.sbol_dictionary.generate_item_map()
        self.item_map_lock.release()
        
        self.strateos_accessor.start_synchronize_protocols()

        self.housekeeping_thread = threading.Thread(target=self.housekeeping)
        self.housekeeping_thread.start()
        
        if init_sbh:
            self.sbh.initialize_sbh()
        self.initialized = True
        
    def start(self, *, background=False):
        if not self.initialized:
            raise RuntimeError('Server has not been initialized.')
        if background:
            run_thread = threading.Thread(target=self.start)
            self.logger.info('Start background thread')
            run_thread.start()
            return

        self.logger.info('Start Listener')

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
        self.logger.info('Connection')
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
                    self.logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
                    response = self._create_http_response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal Server Error\n')
                    response.send(socket_manager)

        except Exception as e:
#             self.logger.info('Exception: {}'.format(e))
            self.logger.info(''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)))

        client_socket.close()
        client_socket.shutdown(socket.SHUT_RDWR)
        
    def _create_http_response(self, http_status, content, content_type='text/html'):
        response = http_message.HttpMessage()
        response.set_response_code(http_status.value, http_status.name)
        response.set_header('content-type', content_type)
        response.set_body(content.encode('utf-8'))
        return response
    
    def handle_GET(self, httpMessage, socket_manager):
        resource = httpMessage.get_path() 
        start = time.time() 
        if resource == "/status":
            response = self._create_http_response(HTTPStatus.OK, 'Intent Parser Server is Up and Running\n')
        elif resource == '/document_report':
            response = self.process_document_report(httpMessage)
        elif resource == '/document_request':
            response = self.process_document_request(httpMessage)
        else:
            response = self._create_http_response(HTTPStatus.NOT_FOUND, 'Resource Not Found')
            self.logger.warning('Did not find ' + resource)
        end = time.time()
        
        response.send(socket_manager)
        self.logger.info('Generated GET request for %s in %0.2fms' %(resource, (end - start) * 1000))
        
    def process_document_report(self, httpMessage):
        """
        Handles a request to generate a report
        """
        resource = httpMessage.get_resource()
        document_id = resource.split('?')[1]
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        report = intent_parser.generate_report() 
        return self._create_http_response(HTTPStatus.OK, json.dumps(report), 'application/json')

    def process_document_request(self, httpMessage):
        """
        Handles a request to generate a structured request 
        """
        resource = httpMessage.get_resource()
        document_id = resource.split('?')[1]
        
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        intent_parser.process()
        
        if len(intent_parser.get_validation_errors()) > 0:
            return self._create_http_response(HTTPStatus.BAD_REQUEST, json.dumps({'errors' : intent_parser.get_validation_errors()}), 'application/json')
        
        return self._create_http_response(HTTPStatus.OK, json.dumps(intent_parser.get_structured_request()), 'application/json')

    def handle_POST(self, httpMessage, socket_manager):
        resource = httpMessage.get_resource()
        start = time.time() 
        if resource == '/analyzeDocument':
            response = self.process_analyze_document(httpMessage) 
        elif resource == '/updateExperimentalResults':
            response = self.process_update_exp_results(httpMessage)
        elif resource == '/calculateSamples':
            response = self.process_calculate_samples(httpMessage)
        elif resource == '/buttonClick':
            response = self.process_button_click(httpMessage)
        elif resource == '/message':
            response = self.process_message(httpMessage) #TODO: remove
        elif resource == '/addToSynBioHub':
            response = self.process_add_to_syn_bio_hub(httpMessage) 
        elif resource == '/addBySpelling':
            response = self.process_add_by_spelling(httpMessage)
        elif resource == '/searchSynBioHub':
            response = self.process_search_syn_bio_hub(httpMessage)
        elif resource == '/submitForm':
            response = self.process_submit_form(httpMessage)
        elif resource == '/createTableTemplate':
            response = self.process_create_table_template(httpMessage)
        elif resource == '/validateStructuredRequest':
            response = self.process_validate_structured_request(httpMessage)
        elif resource == '/generateStructuredRequest':
            response = self.process_generate_structured_request(httpMessage)
        else:
            response = self._create_http_response(HTTPStatus.NOT_FOUND, 'Resource Not Found\n')
        end = time.time()
        response.send(socket_manager)
        self.logger.info('Generated POST request in %0.2fms, %s' %((end - start) * 1000, time.time()))

    def process_analyze_document(self, httpMessage):
        """
        This function will initiate an analysis if the document isn't currently being analyzed and
        then it will report on the progress of that document's analysis until it is done.  Once it's done
        this function will notify the client that the document is ready.
        """
        json_body = intent_parser_utils.get_json_body(httpMessage)
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body)

        self.analyze_processing_map_lock.acquire()
        docBeingProcessed = document_id in self.analyze_processing_map
        self.analyze_processing_map_lock.release()

        if docBeingProcessed: # Doc being processed, check progress
            time.sleep(self.ANALYZE_PROGRESS_PERIOD)

            self.analyze_processing_map_lock.acquire()
            progress_percent = self.analyze_processing_map[document_id]
            self.analyze_processing_map_lock.release()

            if progress_percent < 100: # Not done yet, update client
                action = {}
                action['action'] = 'updateProgress'
                action['progress'] = str(int(progress_percent * 100))
                actions = {'actions': [action]}
                return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
            else: # Document is analyzed, start navigating results
                try:
                    self.analyze_processing_lock[document_id].acquire() # This ensures we've waited for the processing thread to release the client connection
                    (__, client_state) = self.get_client_state(httpMessage)
                    actionList = self.report_search_results(client_state)
                    actions = {'actions': actionList}
                    return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
                finally:
                    self.analyze_processing_map.pop(document_id)
                    self.analyze_processing_lock[document_id].release()
                    self.release_connection(client_state)
        else: # Doc not being processed, spawn new processing thread
            self.analyze_processing_map[document_id] = 0
            analyze_thread = threading.Thread(
                target=self._initiate_document_analysis,
                args=(httpMessage,)  # without comma you'd get a... TypeError
            )
            analyze_thread.start()
            dialogAction = intent_parser_view.progress_sidebar_dialog()
            actions = {'actions': [dialogAction]}
            return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
    
    def report_search_results(self, client_state):
        search_results = client_state['search_results']
       
        self.item_map_lock.acquire()
        item_map = self.item_map.copy()
        self.item_map_lock.release()
         
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
        
    def process_update_exp_results(self, httpMessage):
        """
        This function will scan SynbioHub for experiments related to this document, and updated an
        "Experiment Results" section with information about completed experiments.
        """
        json_body = intent_parser_utils.get_json_body(httpMessage)
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body) 
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        experimental_results = intent_parser.update_experimental_results()
        actions = {'actions': [experimental_results]}
        return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
        
    def process_calculate_samples(self, httpMessage):
        """
        Find all measurements tables and update the samples columns, or add the samples column if it doesn't exist.
        """
        json_body = intent_parser_utils.get_json_body(httpMessage)
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body) 
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        samples = intent_parser.calculate_samples()
        actions = {'actions': [samples]} 
        return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
    
    def process_submit_form(self, httpMessage):
        (json_body, client_state) = self.get_client_state(httpMessage)
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
                self.logger.error('Unsupported form action: {}'.format(action))
            self.logger.info('Action: %s' % result)
            return self._create_http_response(HTTPStatus.OK, json.dumps(result), 'application/json')
        except (Exception, DictionaryMaintainerException) as err:
            self.logger.info('Action: %s resulted in exception %s' % (action, err))
            return self._create_http_response(HTTPStatus.INTERNAL_SERVER_ERROR, json.dumps(result), 'application/json')
        finally:
            self.release_connection(client_state)
            
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

    
    def process_button_click(self, httpMessage):
        (json_body, client_state) = self.get_client_state(httpMessage)

        if 'data' not in json_body:
            errorMessage = 'Missing data'
            raise ConnectionException(HTTPStatus.BAD_REQUEST, errorMessage)
        data = json_body['data']

        if 'buttonId' not in data:
            errorMessage = 'data missing buttonId'
            raise ConnectionException(HTTPStatus.BAD_REQUEST, errorMessage)
        if type(data['buttonId']) is dict:
            buttonDat = data['buttonId']
            buttonId = buttonDat['buttonId']
        else:
            buttonId = data['buttonId']

        method = getattr( self, buttonId )

        try:
            actionList = method(json_body, client_state)
            actions = {'actions': actionList}
            return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
        except Exception as e:
            raise e
        finally:
            self.release_connection(client_state)
            
    def process_nop(self, httpMessage, sm):
        httpMessage # Fix unused warning
        sm # Fix unused warning
        return []
            
    def process_message(self, httpMessage):
        #TODO: remove?
        json_body = self.get_json_body(httpMessage)
        if 'message' in json_body:
            self.logger.info(json_body['message'])
        return self._create_http_response(HTTPStatus.OK, '{}', 'application/json')
    
    def process_validate_structured_request(self, httpMessage):
        '''
        Generate a structured request from a given document, then run it against the validation.
        '''
        json_body = intent_parser_utils.get_json_body(httpMessage)
        validation_errors = []
        validation_warnings = []
        if json_body is None:
            validation_errors.append('Unable to get information from Google document.')
        else:
            document_id = intent_parser_utils.get_document_id_from_json_body(json_body) 
            intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
            intent_parser.process()
            validation_warnings.extend(intent_parser.get_validation_warnings())
            validation_errors.extend(intent_parser.get_validation_errors())
        
        if len(validation_errors) == 0:
            dialog_action = intent_parser_view.valid_request_model_dialog(validation_warnings)
        else:
            dialog_action = intent_parser_view.invalid_request_model_dialog(validation_warnings, validation_errors)
            
        actionList = [dialog_action]
        actions = {'actions': actionList}
        return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
    
    def process_generate_structured_request(self, httpMessage):
        '''
        Validates then generates an HTML link to retrieve a structured request.
        '''
        json_body = intent_parser_utils.get_json_body(httpMessage)
        http_host = httpMessage.get_header('Host')
        validation_errors = []
        validation_warnings = []
        if json_body is None or http_host is None:
            validation_errors.append('Unable to get information from Google document.')
        else:
            document_id = intent_parser_utils.get_document_id_from_json_body(json_body) 
            intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
            intent_parser.process()
            validation_warnings.extend(intent_parser.get_validation_warnings())
            validation_errors.extend(intent_parser.get_validation_errors())
       
        if len(validation_errors) == 0:
            dialog_action = intent_parser_view.valid_request_model_dialog(validation_warnings, intent_parser_view.get_download_link(http_host, document_id))
        else:
            all_messages = []
            all_messages.extend(validation_warnings)
            all_messages.extend(validation_errors)
            dialog_action = intent_parser_view.invalid_request_model_dialog(all_messages)
        actionList = [dialog_action]
        actions = {'actions': actionList}
        return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')   

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
            link_pref_file = os.path.join(self.LINK_PREF_PATH, userId + '.json')
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

        link_pref_file = os.path.join(self.LINK_PREF_PATH, userId + '.json')
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
    
    def process_search_syn_bio_hub(self, httpMessage):
        json_body = intent_parser_utils.get_json_body(httpMessage)
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
                table_html += intent_parser_view.generate_existing_link_html(title, target, analyze)
            table_html += self.generate_results_pagination_html(offset, int(results_count))

            response = {'results':
                        {'operationSucceeded': True,
                         'search_results': search_results,
                         'table_html': table_html
                        }}


        except Exception as err:
            self.logger.error(str(err))
            return self._create_http_response(HTTPStatus.OK, json.dumps(intent_parser_view.operation_failed('Failed to search SynBioHub')), 'application/json')

        return self._create_http_response(HTTPStatus.OK, json.dumps(response), 'application/json')
        
    def process_create_table_template(self,  httpMessage):
        """
        """
        try:
            json_body = intent_parser_utils.get_json_body(httpMessage)
            data = json_body['data']
            cursor_child_index = str(data['childIndex'])
            table_type = data['tableType']

            actionList = []
            if table_type == 'measurements':
                dialog_action = intent_parser_view.create_measurement_table_template(cursor_child_index)
                actionList.append(dialog_action)
            elif table_type == 'parameters':
                protocol_options = list(intent_parser_constants.PROTOCOL_NAMES.values())
                dialog_action = intent_parser_view.create_parameter_table_template(cursor_child_index, protocol_options)
                actionList.append(dialog_action)
            else :
                self.logger.warning('WARNING: unsupported table type: %s' % table_type)

            actions = {'actions': actionList}
            return self._create_http_response(HTTPStatus.OK, json.dumps(actions), 'application/json')
        except Exception as e:
            raise e

    def process_add_to_syn_bio_hub(self, httpMessage):
        try:
            json_body = intent_parser_utils.get_json_body(httpMessage)

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
                dict_path = os.path.join(self.DICT_PATH, userId + '.json')
                if os.path.exists(dict_path):
                    self.logger.info('Loaded dictionary for userId, path: %s' % dict_path)
                    self.spellCheckers[userId].word_frequency.load_dictionary(dict_path)

            lab_experiment = self.intent_parser_factory.create_lab_experiment() 
            doc = lab_experiment.load_from_google_doc(document_id)
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
                    endIdx = len(content);
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
            if not client_state is None:
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

        header.append(intent_parser_constants.COL_HEADER_MEASUREMENT_TYPE)
        header.append(intent_parser_constants.COL_HEADER_FILE_TYPE)
        header.append(intent_parser_constants.COL_HEADER_REPLICATE)
        header.append(intent_parser_constants.COL_HEADER_STRAIN)

        col_sizes.append(len(intent_parser_constants.COL_HEADER_MEASUREMENT_TYPE) + 1)
        col_sizes.append(len(intent_parser_constants.COL_HEADER_FILE_TYPE) + 1)
        col_sizes.append(len(intent_parser_constants.COL_HEADER_REPLICATE) + 1)
        col_sizes.append(len(intent_parser_constants.COL_HEADER_STRAIN) + 1)
        if has_ods:
            header.append(intent_parser_constants.COL_HEADER_ODS)
            col_sizes.append(len(intent_parser_constants.COL_HEADER_ODS) + 1)
        if has_time:
            header.append(intent_parser_constants.COL_HEADER_TIMEPOINT)
            col_sizes.append(len(intent_parser_constants.COL_HEADER_TIMEPOINT) + 1)
        if has_temp:
            header.append(intent_parser_constants.COL_HEADER_TEMPERATURE)
            col_sizes.append(len(intent_parser_constants.COL_HEADER_TEMPERATURE) + 1)

        if has_notes:
            header.append(intent_parser_constants.COL_HEADER_NOTES)
            col_sizes.append(len(intent_parser_constants.COL_HEADER_NOTES) + 1)

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
        selected_protocol = data['protocol']
        table_data = []
        col_sizes = []
        
        header = []
        header.append(intent_parser_constants.COL_HEADER_PARAMETER)
        header.append(intent_parser_constants.COL_HEADER_PARAMETER_VALUE)
        table_data.append(header)
        
        col_sizes.append(len(intent_parser_constants.COL_HEADER_PARAMETER) + 1)
        col_sizes.append(len(intent_parser_constants.COL_HEADER_PARAMETER_VALUE) + 1)
        
        protocol = [key for key, value in intent_parser_constants.PROTOCOL_NAMES.items() if value == selected_protocol]
        
        if protocol[0] not in intent_parser_constants.PROTOCOL_NAMES.keys():
            raise ConnectionException(HTTPStatus.BAD_REQUEST, 'Invalid protocol specified.')
        
        protocol_default_value = self.strateos_accessor.get_protocol(protocol[0])
            
        strateos_dictionary_mapping = self.sbol_dictionary.get_strateos_mappings()
        for protocol_key,protocol_value in protocol_default_value.items():
            parameter_row = []
            for common_name, strateos_id in strateos_dictionary_mapping.items():
                if protocol_key == strateos_id:
                    parameter_row.append(common_name)
                    parameter_row.append(protocol_value)
                    col_sizes.append(len(common_name) + 1)
                    col_sizes.append(len(str(protocol_value)) + 1)
                    break
            if not parameter_row:
                raise Exception('Unable to include %s to the Parameter table because there is no parameter name in the SBOL Dictionary for this Strateos UID' % protocol_key)
            else:
                table_data.append(parameter_row)
                    
        create_table = {}
        create_table['action'] = 'addTable'
        create_table['cursorChildIndex'] = data['cursorChildIndex']
        create_table['tableData'] = table_data
        create_table['tableType'] = 'parameters'
        create_table['tableProtocol'] = [["Protocol: %s" % selected_protocol]]
        create_table['colSizes'] = col_sizes
        return [create_table]
    
    def get_client_state(self, httpMessage):
        json_body = intent_parser_utils.get_json_body(httpMessage)
                
        if 'documentId' not in json_body:
            raise ConnectionException(HTTPStatus.BAD_REQUEST,
                                      'Missing documentId')
        document_id = json_body['documentId']

        try:
            client_state = self.get_connection(document_id)
        except:
            client_state = None

        return (json_body, client_state)
    
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

        action = intent_parser_view.link_text(paragraph_index, offset,
                                end_offset, link)

        return [action]
    
    def _initiate_document_analysis(self, httpMessage):
        """
        This function does the actual work of analyzing the document, and is designed to be run in a separate thread.
        This will process the document and update a status container.  The client will keep pinging the server for status
        while the document is being analyzed and the server will either return the progress percentage, or indicate that the
        results are ready.
        """
        json_body = intent_parser_utils.get_json_body(httpMessage)
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body) 
        
        lab_experiment = self.intent_parser_factory.create_lab_experiment()
        doc = lab_experiment.load_from_google_doc(document_id)
         
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
        lab_experiment = self.intent_parser_factory.create_lab_experiment()
        lab_experiment.load_from_google_doc(doc_id)
        paragraphs = lab_experiment.paragraphs() 

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
                self.logger.error('Error: releasing client_state, but it is not locked! doc_id: %s, called by %s' % (document_id, inspect.currentframe().f_back.f_code.co_name))
            client_state['locked'] = False

        self.client_state_lock.release()

    def stop(self):
        """
        Stop all jobs running on intent parser server
        """
        self.initialized = False
        self.logger.info('Signaling shutdown...')
        self.shutdownThread = True
        self.event.set()
        if self.sbh is not None:
            self.sbh.stop()
            self.logger.info('Stopped SynBioHub') 
        if self.strateos_accessor is not None:
            self.strateos_accessor.stop_synchronizing_protocols()
            self.logger.info('Stopped caching Strateos protocols.')
        if self.socket is not None:
            self.logger.info('Closing server...')
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except OSError:
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
                item_map = self.sbol_dictionary.generate_item_map(use_cache=False)
            except Exception as ex:
                self.logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))

            self.item_map_lock.acquire()
            self.item_map = item_map
            self.item_map_lock.release()

    

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

        if offset == 0 or not term in self.sparql_similar_count_cache:
            sparql_count = self.sparql_similar_count.replace('${TERM}', term).replace('${EXTRA_FILTER}', extra_filter)
            query_results = self.sbh.sparqlQuery(sparql_count)
            bindings = query_results['results']['bindings']
            self.sparql_similar_count_cache[term] = bindings[0]['count']['value']

        sparql_query = self.sparql_similar_query.replace('${TERM}', term).replace('${LIMIT}', str(intent_parser_constants.SPARQL_LIMIT)).replace('${OFFSET}', str(offset)).replace('${EXTRA_FILTER}', extra_filter)
        query_results = self.sbh.sparqlQuery(sparql_query)
        bindings = query_results['results']['bindings']
        search_results = []
        for binding in bindings:
            title = binding['title']['value']
            target = binding['member']['value']
            if self.sbh_spoofing_prefix is not None:
                target = target.replace(self.sbh_spoofing_prefix, self.sbh_url)
            search_results.append({'title': title, 'target': target})

        return search_results, self.sparql_similar_count_cache[term]




def setup_logging(
    default_path='logging.json',
    default_level=logging.INFO,
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
    
    logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.CRITICAL)
    logging.getLogger("googleapiclient.discovery").setLevel(logging.CRITICAL)

def signal_int_handler(sig, frame, intent_parser_server):
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
        intent_parser_server.stop()
    # If we receive enough SIGINTs, die
    if sigIntCount > 3:
        sys.exit(0)

signal.signal(signal.SIGINT, signal_int_handler)
sigIntCount = 0

def main():
    parser = argparse.ArgumentParser(description='Processes an experimental design.')
    parser.add_argument('-a', '--authn', nargs='?',
                            required=True, help='Authorization token for data catalog.')
    
    parser.add_argument('-b', '--bind-host', nargs='?', default='0.0.0.0',
                            required=False, help='IP address to bind to.')
    
    parser.add_argument('-c', '--collection', nargs='?', default=intent_parser_constants.SBH_HUB_STAGING_URL,
                            required=False, help='Collection url.')
    
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
        datacatalog_config = { "mongodb" : { "database" : "catalog_staging", "authn" : input_args.authn } }
        strateos_accessor = StrateosAccessor(input_args.transcriptic)
        intent_parser_factory = IntentParserFactory(datacatalog_config, sbh, sbol_dictionary)
        intent_parser_server = IntentParserServer(sbh, sbol_dictionary, strateos_accessor, intent_parser_factory,
                                       bind_ip=input_args.bind_host,
                                       bind_port=input_args.bind_port)
        intent_parser_server.initialize_server()
        intent_parser_server.start() 
    except Exception:
        if intent_parser_server is not None:
            intent_parser_server.stop()

if __name__ == "__main__":
    main()
