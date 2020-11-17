from http import HTTPStatus
from intent_parser.accessor.google_accessor import GoogleAccessor
from intent_parser.accessor.mongo_db_accessor import TA4DBAccessor
from intent_parser.accessor.tacc_go_accessor import TACCGoAccessor
from intent_parser.document.analyze_document_controller import AnalyzeDocumentController
from intent_parser.document.document_location import DocumentLocation
from intent_parser.document.intent_parser_document_factory import IntentParserDocumentFactory
from intent_parser.intent_parser_factory import LabExperiment
from intent_parser.intent_parser_exceptions import RequestErrorException
from intent_parser.intent_parser_exceptions import DictionaryMaintainerException, IntentParserException, TableException
from intent_parser.protocols.protocol_factory import ProtocolFactory
from intent_parser.table.intent_parser_table_type import TableType
from intent_parser.table.table_creator import TableCreator
from spellchecker import SpellChecker
import inspect
import intent_parser.constants.google_api_constants as google_constants
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.constants.ip_app_script_constants as ip_addon_constants
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.protocols.opil_parameter_utils as opil_util
import intent_parser.utils.intent_parser_utils as intent_parser_utils
import intent_parser.utils.intent_parser_view as intent_parser_view
import logging.config
import os
import threading
import traceback

class IntentParserProcessor(object):

    logger = logging.getLogger('intent_parser_processor')
    dict_path = 'dictionaries'
    link_pref_path = 'link_pref'

    _curr_path = os.path.dirname(os.path.realpath(__file__))

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
                 intent_parser_factory
                 ):
        self.sbh = sbh
        self.sbol_dictionary = sbol_dictionary
        self.strateos_accessor = strateos_accessor
        self.intent_parser_factory = intent_parser_factory

        if not os.path.exists(self.dict_path):
            os.makedirs(self.dict_path)
        if not os.path.exists(self.link_pref_path):
            os.makedirs(self.link_pref_path)

        self.sparql_similar_query = intent_parser_utils.load_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'findSimilar.sparql'))
        self.sparql_similar_count = intent_parser_utils.load_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'findSimilarCount.sparql'))
        self.sparql_similar_count_cache = {}

        self.spellCheckers = {}
        # Dictionary per-user that stores analyze associations to ignore
        self.analyze_controller = AnalyzeDocumentController()
        self.client_state_map = {}
        self.client_state_lock = threading.Lock()
        self.initialized = False

    def initialize_intent_parser_processor(self, init_sbh=True):
        """
        Initialize the server.
        """
        self.sbol_dictionary.start_synchronizing_spreadsheet()
        self.analyze_controller.start_analyze_controller()
        self.strateos_accessor.start_synchronize_protocols()

        if init_sbh:
            self.sbh.initialize_sbh()
        self.initialized = True

    def process_opil_GET_request(self, document_id):
        lab_accessors = {dc_constants.LAB_TRANSCRIPTIC: self.strateos_accessor}
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        intent_parser.process_opil_request(lab_accessors)
        sbol_doc = intent_parser.get_opil_request()
        if not sbol_doc:
            errors = ['No opil output generated.']
            errors.extend(intent_parser.get_validation_errors())
            warnings = [intent_parser.get_validation_warnings()]
            return {'errors': errors, 'warnings': warnings}

        xml_string = sbol_doc.write_string('xml')
        return xml_string

    def process_opil_POST_request(self, http_host, json_body):
        validation_errors = []
        validation_warnings = []
        if json_body is None or http_host is None:
            validation_errors.append('Unable to get information from Google document.')
        else:
            document_id = intent_parser_utils.get_document_id_from_json_body(json_body)
            lab_accessors = {dc_constants.LAB_TRANSCRIPTIC: self.strateos_accessor}
            intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
            intent_parser.process_opil_request(lab_accessors)
            validation_warnings.extend(intent_parser.get_validation_warnings())
            validation_errors.extend(intent_parser.get_validation_errors())

        if len(validation_errors) == 0:
            link = intent_parser_view.get_download_opil_link(http_host, document_id)
            dialog_action = intent_parser_view.valid_request_model_dialog('OPIL Validation: Passed!',
                                                                          'Download OPIL File',
                                                                          validation_warnings,
                                                                          link)
        else:
            all_messages = []
            all_messages.extend(validation_warnings)
            all_messages.extend(validation_errors)
            dialog_action = intent_parser_view.invalid_request_model_dialog('OPIL request validation: Failed!', all_messages)

        action_list = [dialog_action]
        actions = {'actions': action_list}
        return actions

    def process_document_report(self, document_id):
        """
        Handles a request to generate a report
        """
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        report = intent_parser.generate_report()
        return report

    def process_document_request(self, document_id):
        """
        Handles a request to generate a structured request
        """
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        intent_parser.process_structure_request()
        if len(intent_parser.get_validation_errors()) > 0:
            raise RequestErrorException(HTTPStatus.BAD_REQUEST,
                                        errors=intent_parser.get_validation_errors(),
                                        warnings=intent_parser.get_validation_warnings())

        return intent_parser.get_structured_request()

    def process_experiment_request_documents(self):
        """
        Retrieve experiment request documents.
        """
        drive_accessor = GoogleAccessor().get_google_drive_accessor(version=3)
        er_docs = drive_accessor.get_all_docs(intent_parser_constants.GOOGLE_DRIVE_EXPERIMENT_REQUEST_FOLDER)
        return {'docId': er_docs}

    def process_experiment_status_GET(self, document_id):
        """
        Retrieve the statuses of an experiment from a google document.
        """
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        intent_parser.process_experiment_status_request()
        if len(intent_parser.get_validation_errors()) > 0:
            raise RequestErrorException(HTTPStatus.BAD_REQUEST,
                                        errors=intent_parser.get_validation_errors(),
                                        warnings=intent_parser.get_validation_warnings())

        experiment_status = intent_parser.get_experiment_status_request()
        result = {dc_constants.LAB: experiment_status[dc_constants.LAB],
                  dc_constants.EXPERIMENT_ID: experiment_status[dc_constants.EXPERIMENT_ID]}
        for table_id, status_table in experiment_status[dc_constants.STATUS_ELEMENT].items():
            result[table_id] = status_table.to_dict()

        return result

    def get_status(self):
        if not self.initialized:
            raise RequestErrorException(HTTPStatus.SERVICE_UNAVAILABLE,
                                        errors=['Intent Parser not initialized to properly accept incoming requests.'])
        return 'Intent Parser Server is Up and Running'

    def process_experiment_execution_status(self, json_body):
        execution_id = 'ZzL5p65NgyXw' # TODO: placeholder to assume authentication was successful. Will need to update to correct execution_id
        tacc_accessor = TACCGoAccessor()
        status = tacc_accessor.get_status_of_experiment(execution_id)
        action_list = [intent_parser_view.message_dialog('Submission Status', status)]

        actions = {'actions': action_list}
        return actions

    def process_run_experiment_GET(self, document_id):
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        intent_parser.process_experiment_run_request()

        validation_warnings = []
        validation_errors = []
        validation_warnings.extend(intent_parser.get_validation_warnings())
        validation_errors.extend(intent_parser.get_validation_errors())

        request_data = intent_parser.get_experiment_request()
        response_json = TACCGoAccessor().execute_experiment(request_data)
        if '_links' not in response_json and 'self' not in response_json['_links']:
            validation_errors.append('Intent Parser unable to get redirect link to TACC authentication webpage.')

        if len(validation_errors) > 0:
            raise RequestErrorException(HTTPStatus.BAD_REQUEST, errors=validation_errors, warnings=validation_warnings)

        link = response_json['_links']['self']
        return {'authenticationLink': link}

    def process_run_experiment_POST(self, json_body):
        validation_errors = []
        validation_warnings = []
        response_json = {}
        if json_body is None:
            validation_errors.append('Unable to get information from Google document.')
        else:
            document_id = intent_parser_utils.get_document_id_from_json_body(json_body)
            intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
            intent_parser.process_experiment_run_request()
            validation_warnings.extend(intent_parser.get_validation_warnings())
            validation_errors.extend(intent_parser.get_validation_errors())
            request_data = intent_parser.get_experiment_request()
            response_json = TACCGoAccessor().execute_experiment(request_data)

        action_list = []
        if not response_json or ('_links' not in response_json and 'self' not in response_json['_links']):
            validation_errors.append('Intent Parser unable to get redirect link to TACC authentication webpage.')

        if len(validation_errors) == 0:
            link = response_json['_links']['self']
            action_list.append(intent_parser_view.create_execute_experiment_dialog(link))
        else:
            all_messages = []
            all_messages.extend(validation_warnings)
            all_messages.extend(validation_errors)
            dialog_action = intent_parser_view.invalid_request_model_dialog('Failed to execute experiment',
                                                                            all_messages)
            action_list.append(dialog_action)
        actions = {'actions': action_list}
        return actions

    def _get_user_id(self, json_body):
        if ip_addon_constants.USER_EMAIL in json_body and json_body[ip_addon_constants.USER_EMAIL]:
            return json_body[ip_addon_constants.USER_EMAIL]
        if ip_addon_constants.USER in json_body and json_body[ip_addon_constants.USER]:
            return json_body[ip_addon_constants.USER]
        raise RequestErrorException(HTTPStatus.BAD_REQUEST, errors=['No user credential provided from request.'])

    def _get_or_create_cursor_location(self, json_body):
        doc_location = DocumentLocation()
        if 'data' in json_body and 'paragraphIndex' in json_body['data'] and 'offset' in json_body['data']:
            paragraph_index = json_body['data']['paragraphIndex']
            start_offset = json_body['data']['offset']
            doc_location.set_paragraph_index(paragraph_index)
            doc_location.set_start_offset(start_offset)

        return doc_location

    def process_analyze_document(self, json_body):
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body)
        intent_parser = LabExperiment(document_id)
        doc_factory = IntentParserDocumentFactory()
        ip_document = doc_factory.from_google_doc(intent_parser.load_from_google_doc())
        self.analyze_controller.process_dictionary_terms(document_id,
                                                         ip_document,
                                                         self._get_user_id(json_body),
                                                         self._get_or_create_cursor_location(json_body),
                                                         self.sbol_dictionary.get_analyzed_terms())

        actions = [intent_parser_view.progress_sidebar_dialog()]
        search_result_action = self._report_current_term(document_id)
        actions.extend(search_result_action)
        actions = {'actions': search_result_action}
        return actions

    def _report_current_term(self, document_id):
        actions = []
        current_result = self.analyze_controller.get_first_analyze_result(document_id)
        if not current_result:
            final_result_action = intent_parser_view.simple_sidebar_dialog('Finished Analyzing Document.', [])
            actions.append(final_result_action)
        else:
            search_result_actions = intent_parser_view.create_search_result_dialog(current_result.get_matching_term(),
                                                                                   current_result.get_sbh_uri(),
                                                                                   current_result.get_matching_term(),
                                                                                   document_id,
                                                                                   current_result.get_paragraph_index(),
                                                                                   current_result.get_start_offset(),
                                                                                   current_result.get_end_offset())
            actions.extend(search_result_actions)

        return actions


    def process_update_exp_results(self, json_body):
        """
        This function will scan SynbioHub for experiments related to this document, and updated an
        "Experiment Results" section with information about completed experiments.
        """
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body)
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        experimental_results = intent_parser.update_experimental_results()
        actions = {'actions': [experimental_results]}
        return actions

    def process_calculate_samples(self, json_body):
        """
        Find all measurements tables and update the samples columns, or add the samples column if it doesn't exist.
        """
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body)
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        samples = intent_parser.calculate_samples()
        actions = {'actions': [samples]}
        return actions

    def process_submit_form(self, json_body):
        if 'data' not in json_body:
            error_message = ['No data provided from button click.']
            raise RequestErrorException(HTTPStatus.BAD_REQUEST, errors=error_message)

        document_id = intent_parser_utils.get_document_id_from_json_body(json_body)
        data = json_body['data']
        action = data['extra']['action']

        result = {}

        if action == 'submit':
            result = self.sbh.create_sbh_stub(data)
            if result['results']['operationSucceeded'] and data['isSpellcheck'] == 'True':
                # store the link for any other matching results
                # curr_term = client_state['spelling_results'][client_state["spelling_index"]]['term']
                # for r in client_state['spelling_results']:
                #     if r['term'] == curr_term:
                #         r['prev_link'] = result['actions'][0]['url']
                #
                # client_state["spelling_index"] += 1
                # if client_state['spelling_index'] < client_state['spelling_size']:
                for action in intent_parser_view.report_spelling_results(data):
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
            actions = self.process_create_parameter_table(data, json_body['documentId'])
            result = {'actions': actions,
                      'results': {'operationSucceeded': True}
                      }
        return result

    def process_submit_form_old(self, json_body):
        client_state = self.get_client_state(json_body)
        try:
            data = json_body['data']
            action = data['extra']['action']

            result = {}

            if action == 'submit':
                result = self.sbh.create_sbh_stub(data)
                if result['results']['operationSucceeded'] and data['isSpellcheck'] == 'True':
                    # store the link for any other matching results
                    curr_term = client_state['spelling_results'][client_state["spelling_index"]]['term']
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
                    {'paragraph_index': data['selectionStartParagraph'],
                     'offset': int(data['selectionStartOffset']),
                     'end_offset': int(data['selectionEndOffset']),
                     'uri': data['extra']['link']
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
                actions = self.process_create_parameter_table(data, json_body['documentId'])
                result = {'actions': actions,
                          'results': {'operationSucceeded': True}
                }
            else:
                self.logger.error('Unsupported form action: {}'.format(action))
            self.logger.info('Action: %s' % result)
            return result
        except DictionaryMaintainerException as err:
            self.logger.info('Action: %s resulted in exception %s' % (action, err))
            raise RequestErrorException(HTTPStatus.INTERNAL_SERVER_ERROR, errors=[err.get_message()])
        finally:
            self.release_connection(client_state)

    def spellcheck_add_ignore(self, json_body, client_state):
        """ Ignore button action for additions by spelling
        """
        client_state['spelling_index'] += 1
        if client_state['spelling_index'] >= client_state['spelling_size']:
            # We are at the end, nothing else to do
            return []
        else:
            return intent_parser_view.report_spelling_results(client_state)

    def spellcheck_add_ignore_all(self, json_body, client_state):
        """ Ignore All button action for additions by spelling
        """
        if self.spellcheck_remove_term(client_state):
            return intent_parser_view.report_spelling_results(client_state)

    def spellcheck_add_dictionary(self, json_body, client_state):
        """ Add to spelling dictionary button action for additions by spelling
        """
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
                raise RequestErrorException(HTTPStatus.NOT_FOUND, errors=[errorMessage])

            body = doc.get('body')
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
        body = doc.get('body')
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
        return self.spellcheck_select_word_from_text(client_state, True, True)

    def spellcheck_add_select_next(self, json_body, client_state):
        """ Select next word button action for additions by spelling
        """
        return self.spellcheck_select_word_from_text(client_state, False, True)

    def spellcheck_add_drop_first(self, json_body, client_state):
        """ Remove selection previous word button action for additions by spelling
        """
        return self.spellcheck_select_word_from_text(client_state, True, False)

    def spellcheck_add_drop_last(self, json_body, client_state):
        """ Remove selection next word button action for additions by spelling
        """
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

            search_result = { 'paragraph_index': result[0],
                              'offset': result[1],
                              'end_offset': result[1] + len(selected_term) - 1,
                              'term': selected_term,
                              'uri': uri,
                              'link': result[3],
                              'text': result[4]}
            # Only link terms that don't already have links
            if  search_result['link'] is None:
                actions += self.add_link(search_result)

            pos = result[2] + len(selected_term)

        return actions

    def _get_button_id(self, data):
        if ip_addon_constants.BUTTON_ID not in data:
            error_message = ['Expected to get %s assigned to this HTTP data: %s but none was found.' % (ip_addon_constants.BUTTON_ID, data)]
            raise RequestErrorException(HTTPStatus.BAD_REQUEST, errors=error_message)

        if type(data[ip_addon_constants.BUTTON_ID]) is dict:
            buttonDat = data[ip_addon_constants.BUTTON_ID]
            button_id = buttonDat[ip_addon_constants.BUTTON_ID]
            return button_id
        return data[ip_addon_constants.BUTTON_ID]

    def process_button_click(self, json_body):
        if 'data' not in json_body:
            error_message = ['No data provided from button click.']
            raise RequestErrorException(HTTPStatus.BAD_REQUEST, errors=error_message)

        data = json_body['data']
        if ip_addon_constants.BUTTON_ID not in data:
            error_message = ['Expected to get %s assigned: %s but none was found.' % (ip_addon_constants.BUTTON_ID, data)]
            raise RequestErrorException(HTTPStatus.BAD_REQUEST, errors=error_message)

        document_id = intent_parser_utils.get_document_id_from_json_body(json_body)
        button_data = data[ip_addon_constants.BUTTON_ID]
        button_id = button_data[ip_addon_constants.BUTTON_ID]
        if button_id == intent_parser_constants.ANALYZE_YES:
            return self.process_analyze_yes(document_id, button_data)
        elif button_id == intent_parser_constants.ANALYZE_YES_TO_ALL:
            return self.process_analyze_yes_to_all(document_id, button_data)
        elif button_id == intent_parser_constants.ANALYZE_NO:
            return self.process_analyze_no(document_id, button_data)
        elif button_id == intent_parser_constants.ANALYZE_NO_TO_ALL:
            return self.process_analyze_no_to_all(document_id, button_data)
        elif button_id == intent_parser_constants.ANALYZE_NEVER_LINK:
            return self.process_analyze_never_link(document_id,
                                                   self._get_user_id(json_body),
                                                   button_data)


    def process_nop(self, http_message, sm):
        return []

    def process_message(self, json_body):
        if 'message' in json_body:
            self.logger.info(json_body['message'])
        return '{}'

    def process_validate_structured_request(self, json_body):
        """
        Generate a structured request from a given document, then run it against the validation.
        """
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
            if len(validation_warnings) == 0:
                validation_warnings.append('No warnings found.')
            dialog_action = intent_parser_view.valid_request_model_dialog(validation_warnings, width=600)
        else:
            all_errors = validation_warnings + validation_errors
            dialog_action = intent_parser_view.invalid_request_model_dialog('Structured request validation: Failed!',
                                                                            all_errors)

        actionList = [dialog_action]
        actions = {'actions': actionList}
        return actions

    def process_generate_structured_request(self, http_host, json_body):
        """
        Validates then generates an HTML link to retrieve a structured request.
        """
        validation_errors = []
        validation_warnings = []
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body)
        if http_host is None:
            validation_errors.append('Missing an intent parser URL to generate a structured request on.')

        if 'data' in json_body and 'bookmarks' in json_body['data']:
            intent_parser = self.intent_parser_factory.create_intent_parser(document_id,
                                                                            bookmarks=json_body['data']['bookmarks'])
        else:
            intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        intent_parser.process_structure_request()
        validation_warnings.extend(intent_parser.get_validation_warnings())
        validation_errors.extend(intent_parser.get_validation_errors())

        if len(validation_errors) == 0:
            if len(validation_warnings) == 0:
                validation_warnings.append('No warnings found.')
            dialog_action = intent_parser_view.valid_request_model_dialog('Structured request validation: Passed!',
                                                                          'Download Structured Request ',
                                                                          validation_warnings,
                                                                          intent_parser_view.get_download_structured_request_link(http_host, document_id),
                                                                          width=600)
        else:
            all_messages = []
            all_messages.extend(validation_warnings)
            all_messages.extend(validation_errors)
            dialog_action = intent_parser_view.invalid_request_model_dialog('Structured request validation: Failed!', all_messages)
        actionList = [dialog_action]
        actions = {'actions': actionList}
        return actions

    def process_analyze_yes(self, document_id, data):
        self.analyze_controller.remove_analyze_result(document_id,
                                                      data[intent_parser_constants.ANALYZE_PARAGRAPH_INDEX],
                                                      data[intent_parser_constants.ANALYZE_CONTENT_TERM],
                                                      data[intent_parser_constants.ANALYZE_LINK],
                                                      data[intent_parser_constants.ANALYZE_OFFSET],
                                                      data[intent_parser_constants.ANALYZE_END_OFFSET])
        actions = [intent_parser_view.link_text(data[intent_parser_constants.ANALYZE_PARAGRAPH_INDEX],
                                                data[intent_parser_constants.ANALYZE_OFFSET],
                                                data[intent_parser_constants.ANALYZE_END_OFFSET],
                                                data[intent_parser_constants.ANALYZE_LINK])]
        actions.extend(self._report_current_term(document_id))
        return {'actions': actions}

    def process_analyze_yes_to_all(self, document_id, data):
        matching_terms = self.analyze_controller.remove_analyze_result_with_term(document_id,
                                                                                 data[intent_parser_constants.ANALYZE_CONTENT_TERM])
        actions = []
        for term in matching_terms:
            actions.append(intent_parser_view.link_text(term.get_paragraph_index(),
                                                        term.get_start_offset(),
                                                        term.get_end_offset(),
                                                        term.get_sbh_uri()))
        actions.extend(self._report_current_term(document_id))
        return {'actions': actions}

    def process_analyze_no(self, document_id, data):
        self.analyze_controller.remove_analyze_result(document_id,
                                                      data[intent_parser_constants.ANALYZE_PARAGRAPH_INDEX],
                                                      data[intent_parser_constants.ANALYZE_CONTENT_TERM],
                                                      data[intent_parser_constants.ANALYZE_LINK],
                                                      data[intent_parser_constants.ANALYZE_OFFSET],
                                                      data[intent_parser_constants.ANALYZE_END_OFFSET])
        actions = []
        actions.extend(self._report_current_term(document_id))
        return {'actions': actions}

    def process_analyze_no_to_all(self, document_id, data):
        self.analyze_controller.remove_analyze_result_with_term(document_id,
                                                                data[intent_parser_constants.ANALYZE_CONTENT_TERM])
        actions = []
        actions.extend(self._report_current_term(document_id))
        return {'actions': actions}

    def process_analyze_never_link(self, document_id: str, user_id: str, data: dict):
        self.analyze_controller.remove_analyze_result_with_term(document_id,
                                                                data[intent_parser_constants.ANALYZE_CONTENT_TERM])
        self.analyze_controller.add_to_ignore_terms(user_id, data[intent_parser_constants.ANALYZE_CONTENT_TERM])

        actions = []
        actions.extend(self._report_current_term(document_id))
        return {'actions': actions}

    def process_search_syn_bio_hub(self, json_body):
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

            response = {'results': {'operationSucceeded': True,
                                    'search_results': search_results,
                                    'table_html': table_html
                                    }
                        }
        except Exception as err:
            self.logger.error(str(err))
            return intent_parser_view.operation_failed('Failed to search SynBioHub')

        return response

    def process_create_table_template(self, json_body):
        """
        Process create table templates.
        """
        data = json_body['data']
        cursor_child_index = str(data['childIndex'])
        table_type = data[ip_addon_constants.TABLE_TYPE]
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body)

        action_list = []
        if table_type == ip_addon_constants.TABLE_TYPE_CONTROLS:
            dialog_action = intent_parser_view.create_controls_table_dialog(cursor_child_index)
            action_list.append(dialog_action)
        elif table_type == ip_addon_constants.TABLE_TYPE_MEASUREMENTS:
            dialog_action = intent_parser_view.create_measurement_table_dialog(cursor_child_index)
            action_list.append(dialog_action)
        elif table_type == ip_addon_constants.TABLE_TYPE_PARAMETERS:
            intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
            intent_parser.process_lab_name()
            lab_name = intent_parser.get_lab_name()
            protocol_factory = ProtocolFactory(lab_name=lab_name, transcriptic_accessor=self.strateos_accessor)
            protocols = protocol_factory.load_protocols_from_lab()
            protocol_names = [intent_parser_constants.PROTOCOL_PLACEHOLDER]
            cell_free_riboswitch_parameters = []
            growth_curve_parameters = []
            obstacle_course_parameters = []
            time_series_parameters = []
            for protocol in protocols:
                parameters = protocol_factory.get_optional_parameter_fields(protocol)
                parameter_names = [parameter.name for parameter in parameters]
                if protocol.name == intent_parser_constants.CELL_FREE_RIBO_SWITCH_PROTOCOL:
                    cell_free_riboswitch_parameters.extend(parameter_names)
                    protocol_names.append(protocol.name)
                elif protocol.name == intent_parser_constants.GROWTH_CURVE_PROTOCOL:
                    growth_curve_parameters.extend(parameter_names)
                    protocol_names.append(protocol.name)
                elif protocol.name == intent_parser_constants.OBSTACLE_COURSE_PROTOCOL:
                    obstacle_course_parameters.extend(parameter_names)
                    protocol_names.append(protocol.name)
                elif protocol.name == intent_parser_constants.TIME_SERIES_HTP_PROTOCOL:
                    time_series_parameters.extend(parameter_names)
                    protocol_names.append(protocol.name)

            dialog_action = intent_parser_view.create_parameter_table_dialog(cursor_child_index,
                                                                             protocol_names,
                                                                             timeseries_optional_fields=time_series_parameters,
                                                                             growthcurve_optional_fields=growth_curve_parameters,
                                                                             obstaclecourse_optional_fields=obstacle_course_parameters,
                                                                             cellfreeriboswitch_options=cell_free_riboswitch_parameters)
            action_list.append(dialog_action)
        else:
            self.logger.warning('WARNING: unsupported table type: %s' % table_type)

        actions = {'actions': action_list}
        return actions

    def get_common_names_for_optional_parameter_fields(self, parameters: dict):
        common_names = []
        for field_id, parameter in parameters.items():
            if not parameter.is_required():
                field_name = self.sbol_dictionary.get_common_name_from_transcriptic_id(field_id)
                if field_name:
                    common_names.append(field_name)
        return common_names

    def process_add_to_syn_bio_hub(self, json_body):
        data = json_body['data']
        start = data['start']
        end = data['end']
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body)

        start_paragraph = start['paragraphIndex']
        end_paragraph = end['paragraphIndex']

        start_offset = start['offset']
        end_offset = end['offset']

        dialog_action = self._add_to_syn_bio_hub(document_id,
                                                 start_paragraph,
                                                 end_paragraph,
                                                 start_offset,
                                                 end_offset)
        action_list = [dialog_action]
        actions = {'actions': action_list}
        return actions

    def _add_to_syn_bio_hub(self, document_id, start_paragraph, end_paragraph, start_offset, end_offset, is_spellcheck=False):
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
                                                                 is_spellcheck)

    def process_add_by_spelling(self, json_body):
        """
        Function that sets up the results for additions by spelling
        This will start from a given offset (generally 0) and searches the rest of the
        document, looking for words that are not in the dictionary.  Any words that
        don't match are then used as suggestions for additions to SynBioHub.

        Users can add words to the dictionary, and added words are saved by a user id.
        This comes from the email address, but if that's not available the document id
        is used instead.
        """
        client_state = None
        try:
            document_id = intent_parser_utils.get_document_id_from_json_body(json_body)
            user = json_body['user']
            userEmail = json_body['userEmail']

            if not userEmail:
                userId = userEmail
            elif user:
                userId = user
            else:
                userId = document_id

            if userId not in self.spellCheckers:
                self.spellCheckers[userId] = SpellChecker()
                dict_path = os.path.join(self.dict_path, userId + '.json')
                if os.path.exists(dict_path):
                    self.logger.info('Loaded dictionary for userId, path: %s' % dict_path)
                    self.spellCheckers[userId].word_frequency.load_dictionary(dict_path)

            lab_experiment = self.intent_parser_factory.create_lab_experiment(document_id)
            doc = lab_experiment.load_from_google_doc()
            paragraphs = lab_experiment.paragraphs()
            if 'data' in json_body:
                data = json_body['data']
                paragraph_index = data['paragraphIndex']
                offset = data['offset']
                paragraph = paragraphs[paragraph_index]
                first_element = paragraph['elements'][0]
                paragraph_offset = first_element['startIndex']
                starting_pos = paragraph_offset + offset
            else:
                starting_pos = 0

            # Used to store session information
            client_state = self.new_connection(document_id)
            client_state['doc'] = doc
            client_state['user_id'] = userId

            spellCheckResults = []  # Store results metadata
            missedTerms = []  # keep track of lists of misspelt words
            # Second list can help us remove results by word

            for pIdx in range(0, len(paragraphs)):
                paragraph = paragraphs[pIdx]
                elements = paragraph['elements']
                firstIdx = elements[0]['startIndex']
                for element_index in range(len(elements)):
                    element = elements[element_index]
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
                            if word not in self.spellCheckers[userId] and not intent_parser_utils.should_ignore_token(word):
                                # Convert from an index into the content string,
                                # to an offset into the paragraph string
                                absolute_idx = wordStart + (start_index - firstIdx)
                                result = {
                                   'term': word,
                                   'select_start': {'paragraph_index': pIdx,
                                                    'cursor_index': absolute_idx,
                                                    'element_index': element_index},
                                   'select_end': {'paragraph_index': pIdx,
                                                  'cursor_index': absolute_idx + len(word) - 1,
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
                        else:  # continue until we find word end
                            currIdx += 1

                    # Check for tailing word that wasn't processed
                    if currIdx - wordStart > 1:
                        word = content[wordStart:currIdx]
                        word = intent_parser_utils.strip_leading_trailing_punctuation(word)
                        word = word.lower()
                        if word not in self.spellCheckers[userId]:
                            absolute_idx = wordStart + (start_index - firstIdx)
                            result = {
                               'term': word,
                               'select_start': {'paragraph_index': pIdx,
                                                'cursor_index': absolute_idx,
                                                'element_index': element_index},
                               'select_end': {'paragraph_index': pIdx,
                                              'cursor_index': absolute_idx + len(word) - 1,
                                              'element_index': element_index}
                               }
                            spellCheckResults.append(result)
                            missedTerms.append(word)

            # If we have a spelling mistake, highlight text and update user
            if len(spellCheckResults) > 0:
                client_state['spelling_results'] = spellCheckResults
                client_state['spelling_index'] = 0
                client_state['spelling_size'] = len(spellCheckResults)
                action_list = intent_parser_view.report_spelling_results(client_state)
                actions = {'actions': action_list}
                return actions
            else:  # No spelling mistakes!
                buttons = [('Ok', 'process_nop')]
                dialog_action = intent_parser_view.simple_modal_dialog('Found no words not in spelling dictionary!',
                                                                       buttons,
                                                                       'No misspellings!',
                                                                       400,
                                                                       450)
                action_list = [dialog_action]
                actions = {'actions': action_list}
                return actions
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
        if data[ip_addon_constants.HTML_NUM_NEG_CONTROLS]:
            header_row.append(intent_parser_constants.HEADER_NUMBER_OF_NEGATIVE_CONTROLS_VALUE)
        if data[ip_addon_constants.HTML_RNA_INHIBITOR_REACTION]:
            header_row.append(intent_parser_constants.HEADER_USE_RNA_INHIBITOR_IN_REACTION_VALUE)
        if data[ip_addon_constants.HTML_DNA_REACTION_CONCENTRATION]:
            header_row.append(intent_parser_constants.HEADER_DNA_REACTION_CONCENTRATION_VALUE)
        if data[ip_addon_constants.HTML_TEMPLATE_DNA]:
            header_row.append(intent_parser_constants.HEADER_TEMPLATE_DNA_VALUE)
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

    def process_update_experiment_status(self, document_id):
        try:
            self._report_experiment_status(document_id)
        except (IntentParserException, TableException) as err:
            all_errors = [err.get_message()]
            return {'status': 'updated', 'messages': all_errors}

        return {'status': 'updated', 'messages': []}

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
            experiment_ref = google_constants.GOOGLE_DOC_URL_PREFIX + document_id
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

    def process_experiment_status_POST(self, json_body):
        """Report the status of an experiment by inserting experiment specification and status tables."""
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body)
        self.logger.warning('Processing document id: %s' % document_id)

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
        return actions

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

    def process_create_parameter_table(self, data, document_id):
        table_template = []
        header_row = [intent_parser_constants.HEADER_PARAMETER_VALUE,
                      intent_parser_constants.HEADER_PARAMETER_VALUE_VALUE]
        table_template.append(header_row)

        selected_protocol = data[ip_addon_constants.HTML_PROTOCOL]
        lab_name = data[ip_addon_constants.HTML_LAB]
        table_template.append([intent_parser_constants.PARAMETER_PROTOCOL_NAME, selected_protocol])

        protocol_factory = ProtocolFactory(lab_name, self.strateos_accessor)
        protocol = protocol_factory.get_protocol_interface(selected_protocol)
        ref_required_id_to_name = {}
        ref_optional_name_to_id = {}
        for parameter in protocol.has_parameter:
            if not parameter.default_value:
                self.logger.warning('parameter %s does not have default value' % parameter.name)
                continue

            ref_id = str(parameter.default_value[0])
            if parameter.required:
                ref_required_id_to_name[ref_id] = parameter.name
            else:
                ref_optional_name_to_id[parameter.name] = ref_id

        parameter_values = protocol_factory.load_parameter_values_from_protocol(selected_protocol)
        param_value_mapping = {}
        for param_val in parameter_values:
            param_value_mapping[param_val.identity] = param_val

        protocol_id = opil_util.get_protocol_id_from_annotaton(protocol)
        required_fields = self._add_required_parameters(ref_required_id_to_name,
                                                        param_value_mapping,
                                                        google_constants.GOOGLE_DOC_URL_PREFIX + document_id,
                                                        protocol_id)
        table_template.extend(required_fields)

        selected_optional_parameters = data[ip_addon_constants.HTML_OPTIONALPARAMETERS]
        optional_fields = self._add_optional_parameters(ref_optional_name_to_id, param_value_mapping, selected_optional_parameters)
        table_template.extend(optional_fields)

        column_width = [len(header) for header in header_row]
        return intent_parser_view.create_table_template(data[ip_addon_constants.CURSOR_CHILD_INDEX],
                                                        table_template,
                                                        ip_addon_constants.TABLE_TYPE_PARAMETERS,
                                                        column_width)

    def _add_required_parameters(self, ref_required_values, param_value_mapping, experiment_ref_url, protocol_id):
        required_parameters = [[intent_parser_constants.PROTOCOL_FIELD_XPLAN_BASE_DIRECTORY, ''],
                               [intent_parser_constants.PROTOCOL_FIELD_XPLAN_REACTOR, 'xplan'],
                               [intent_parser_constants.PROTOCOL_FIELD_PLATE_SIZE, ''],
                               [intent_parser_constants.PARAMETER_PLATE_NUMBER, ' '],
                               [intent_parser_constants.PROTOCOL_FIELD_CONTAINER_SEARCH_STRING, ' '],
                               [intent_parser_constants.PARAMETER_STRAIN_PROPERTY, ' '],
                               [intent_parser_constants.PARAMETER_XPLAN_PATH, ''],
                               [intent_parser_constants.PARAMETER_SUBMIT, 'False'],
                               [intent_parser_constants.PARAMETER_PROTOCOL_ID, protocol_id],
                               [intent_parser_constants.PARAMETER_TEST_MODE, 'True'],
                               [intent_parser_constants.PARAMETER_EXPERIMENT_REFERENCE_URL_FOR_XPLAN, experiment_ref_url]]

        for value_id, param_name in ref_required_values.items():
            if value_id in param_value_mapping:
                param_value = opil_util.get_param_value_as_string(param_value_mapping[value_id])
                required_parameters.append([param_name, param_value])
            else:
                required_parameters.append([param_name, ' '])

        return required_parameters

    def _add_optional_parameters(self, ref_optional_name_to_id, param_value_mapping, selected_options):
        ref_uris = {}
        optional_parameters = []
        for param_name in selected_options:
            if param_name in ref_optional_name_to_id:
                ref_uris[ref_optional_name_to_id[param_name]] = param_name
            else:
                optional_parameters.append([param_name, ' '])

        for uri, param_name in ref_uris.items():
            if uri in param_value_mapping:
                param_value = opil_util.get_param_value_as_string(param_value_mapping[uri])
                optional_parameters.append([param_name, param_value])

        return optional_parameters

    def get_client_state(self, json_body):
        if ip_addon_constants.DOCUMENT_ID not in json_body:
            errors = ['Expecting to get a %s from this http_message: but none was given' % (ip_addon_constants.DOCUMENT_ID)]
            raise RequestErrorException(HTTPStatus.BAD_REQUEST, errors=errors)
        document_id = json_body[ip_addon_constants.DOCUMENT_ID]
        client_state = self.get_connection(document_id)
        return client_state

    def add_link(self, search_result, new_link=None):
        """ Add a hyperlink to the desired search_result
        """
        paragraph_index = search_result[intent_parser_constants.ANALYZE_PARAGRAPH_INDEX]
        offset = search_result[intent_parser_constants.ANALYZE_OFFSET]
        end_offset = search_result[intent_parser_constants.ANALYZE_END_OFFSET]
        if new_link is None:
            link = search_result['uri']
        else:
            link = new_link
        search_result[intent_parser_constants.ANALYZE_LINK] = link

        action = intent_parser_view.link_text(paragraph_index, offset, end_offset, link)

        return [action]

    def new_connection(self, document_id):
        self.client_state_lock.acquire()
        if document_id in self.client_state_map:
            if self.client_state_map[document_id]['locked']:
                self.client_state_lock.release()
                raise RequestErrorException(HTTPStatus.SERVICE_UNAVAILABLE, errors=['This document is busy'])

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
            raise RequestErrorException(HTTPStatus.BAD_REQUEST, errors=['Invalid session'])

        client_state = self.client_state_map[document_id]

        if client_state['locked']:
            self.client_state_lock.release()
            raise RequestErrorException(HTTPStatus.SERVICE_UNAVAILABLE, errors=['This document is busy'])
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
        """Stop all jobs running on intent table server
        """
        self.initialized = False
        self.logger.info('Signaling shutdown...')

        if self.sbh is not None:
            self.sbh.stop()
            self.logger.info('Stopped SynBioHub')
        if self.analyze_controller is not None:
            self.analyze_controller.stop_synchronizing_ignored_terms()
            self.logger.info('Stopped caching Analyze controller ignored terms.')
        if self.sbol_dictionary is not None:
            self.sbol_dictionary.stop_synchronizing_spreadsheet()
            self.logger.info('Stopped caching SBOL Dictionary.')
        if self.strateos_accessor is not None:
            self.strateos_accessor.stop_synchronizing_protocols()
            self.logger.info('Stopped caching Strateos protocols.')

        self.logger.info('Shutdown complete')

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
