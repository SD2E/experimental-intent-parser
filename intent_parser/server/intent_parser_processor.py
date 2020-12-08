from http import HTTPStatus
from intent_parser.accessor.google_accessor import GoogleAccessor
from intent_parser.accessor.mongo_db_accessor import TA4DBAccessor
from intent_parser.accessor.tacc_go_accessor import TACCGoAccessor
from intent_parser.document.analyze_document_controller import AnalyzeDocumentController
from intent_parser.document.spellcheck_document_controller import SpellcheckDocumentController
from intent_parser.document.document_location import DocumentLocation
from intent_parser.document.intent_parser_document_factory import IntentParserDocumentFactory
from intent_parser.intent_parser_factory import LabExperiment
from intent_parser.intent_parser_exceptions import RequestErrorException
from intent_parser.intent_parser_exceptions import IntentParserException, TableException
from intent_parser.protocols.protocol_factory import ProtocolFactory
from intent_parser.table.intent_parser_table_type import TableType
from intent_parser.table.table_creator import TableCreator
import intent_parser.constants.google_api_constants as google_constants
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.constants.ip_app_script_constants as ip_addon_constants
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import intent_parser.protocols.opil_parameter_utils as opil_util
import intent_parser.utils.intent_parser_utils as intent_parser_utils
import intent_parser.utils.intent_parser_view as intent_parser_view
import logging.config
import os
import traceback

class IntentParserProcessor(object):

    logger = logging.getLogger('intent_parser_processor')

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

        self.sparql_similar_query = intent_parser_utils.load_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'findSimilar.sparql'))
        self.sparql_similar_count = intent_parser_utils.load_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'findSimilarCount.sparql'))
        self.sparql_similar_count_cache = {}

        # Dictionary per-user that stores analyze associations to ignore
        self.analyze_controller = AnalyzeDocumentController()
        self.spellcheck_controller = SpellcheckDocumentController()
        self.initialized = False

    def initialize_intent_parser_processor(self):
        """
        Initialize the server.
        """
        self.sbol_dictionary.start_synchronizing_spreadsheet()
        self.analyze_controller.start_analyze_controller()
        self.spellcheck_controller.start_spellcheck_controller()
        # self.strateos_accessor.start_synchronize_protocols()

        self.sbh.initialize_sbh()
        self.sbh.set_sbol_dictionary(self.sbol_dictionary)

        self.initialized = True

    def process_opil_GET_request(self, document_id):
        lab_accessors = {dc_constants.LAB_TRANSCRIPTIC: self.strateos_accessor}
        intent_parser = self.intent_parser_factory.create_intent_parser(document_id)
        intent_parser.process_opil_request(lab_accessors)
        sbol_doc = intent_parser.get_opil_request()
        if not sbol_doc:
            errors = ['No OPIL output generated.']
            errors.extend(intent_parser.get_validation_errors())
            warnings = [intent_parser.get_validation_warnings()]
            return {'errors': errors, 'warnings': warnings}

        xml_string = sbol_doc.write_string('xml')
        return xml_string

    def process_opil_POST_request(self, http_host, json_body):
        validation_errors = []
        validation_warnings = []

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
            dialog_action = intent_parser_view.invalid_request_model_dialog('OPIL request validation: Failed!',
                                                                            all_messages)

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
        search_result_action = self._report_current_analyze_term(document_id)
        actions.extend(search_result_action)
        actions = {'actions': search_result_action}
        return actions

    def _report_current_analyze_term(self, document_id):
        actions = []
        current_result = self.analyze_controller.get_first_analyze_result(document_id)
        if not current_result:
            final_result_action = intent_parser_view.simple_sidebar_dialog('Finished Analyzing Document.', [])
            actions.append(final_result_action)
        else:
            search_result_actions = intent_parser_view.create_analyze_result_dialog(current_result.get_matching_term(),
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

    def process_submit_to_synbiohub(self, data):
        if 'commonName' not in data:
            return intent_parser_view.operation_failed('Common Name must be specified when submitting an entry to SynBioHub')

        actions = []
        try:
            item_type = data['itemType']
            item_name = data['commonName']
            item_definition_uri = data['definitionURI']
            item_display_id = data['displayId']
            item_lab_ids = data['labId']
            item_lab_id_tag = data['labIdSelect']
            document_url = self.sbh.create_sbh_stub(item_type,
                                                    item_name,
                                                    item_definition_uri,
                                                    item_display_id,
                                                    item_lab_ids,
                                                    item_lab_id_tag)

            paragraph_index = data['selectionStartParagraph']
            offset = data['selectionStartOffset']
            end_offset = data['selectionEndOffset']
            link_text_action = intent_parser_view.link_text(paragraph_index, offset, end_offset, document_url)
            actions.append(link_text_action)
        except IntentParserException as err:
            message = err.get_message()
            result = intent_parser_view.operation_failed(message)
            return result

        return {'actions': actions,
                'results': {'operationSucceeded': True}
                }

    def process_submit_form(self, json_body):
        if 'data' not in json_body:
            error_message = ['No data provided from button click.']
            raise RequestErrorException(HTTPStatus.BAD_REQUEST, errors=error_message)

        document_id = intent_parser_utils.get_document_id_from_json_body(json_body)
        data = json_body['data']
        action_type = data['extra']['action']

        result = {}
        if action_type == intent_parser_constants.SUBMIT_FORM:
            result = self.process_submit_to_synbiohub(data)
        elif action_type == intent_parser_constants.SUBMIT_FORM_CREATE_CONTROLS_TABLE:
            actions = self.process_controls_table(data, json_body['documentId'])
            result['actions'] = actions
            result['results'] = {'operationSucceeded': True}
        elif action_type == intent_parser_constants.SUBMIT_FORM_CREATE_MEASUREMENT_TABLE:
            actions = self.process_create_measurement_table(data)
            result['actions'] = actions
            result['results'] = {'operationSucceeded': True}
        elif action_type == intent_parser_constants.SUBMIT_FORM_CREATE_PARAMETER_TABLE:
            actions = self.process_create_parameter_table(data, json_body['documentId'])
            result['actions'] = actions
            result['results'] = {'operationSucceeded': True}
        else:
            message = 'Request %s not supported in Intent Parser' % action_type
            result = intent_parser_view.operation_failed(message)

        return result

    def process_button_click(self, json_body):
        if 'data' not in json_body:
            error_message = ['No data provided from button click.']
            raise RequestErrorException(HTTPStatus.BAD_REQUEST, errors=error_message)

        data = json_body['data']
        if ip_addon_constants.BUTTON_ID not in data:
            error_message = ['Expected to get %s assigned in %s.' % (ip_addon_constants.BUTTON_ID, data)]
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
        elif button_id == intent_parser_constants.SPELLCHECK_ADD_IGNORE:
            return self.process_spellcheck_ignore(document_id, button_data)
        elif button_id == intent_parser_constants.SPELLCHECK_ADD_IGNORE_ALL:
            return self.process_spellcheck_ignore_all(document_id, button_data)
        elif button_id == intent_parser_constants.SPELLCHECK_ADD_DICTIONARY:
            return self.process_spellcheck_add_to_dictionary(document_id,
                                                             self._get_user_id(json_body),
                                                             button_data)
        elif button_id == intent_parser_constants.SPELLCHECK_ADD_SYNBIOHUB:
            return self.process_spellcheck_add_to_synbiohub(document_id, button_data)
        elif button_id == intent_parser_constants.SPELLCHECK_ADD_SELECT_PREVIOUS:
            return self.process_spellcheck_add_previous_word(document_id, button_data)
        elif button_id == intent_parser_constants.SPELLCHECK_ADD_SELECT_NEXT:
            return self.process_spellcheck_add_next_word(document_id, button_data)
        elif button_id == intent_parser_constants.SPELLCHECK_ADD_DROP_FIRST:
            return self.process_spellcheck_drop_previous_word(document_id, button_data)
        elif button_id == intent_parser_constants.SPELLCHECK_ADD_DROP_LAST:
            return self.process_spellcheck_drop_next_word(document_id, button_data)
        else:
            error_message = ['Button ID %s not recognized by Intent Parser.' % button_id]
            raise RequestErrorException(HTTPStatus.BAD_REQUEST, errors=error_message)

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
                                                                          validation_warnings, width=600)
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
                                                      data[intent_parser_constants.SELECTED_PARAGRAPH_INDEX],
                                                      data[intent_parser_constants.SELECTED_CONTENT_TERM],
                                                      data[intent_parser_constants.ANALYZE_LINK],
                                                      data[intent_parser_constants.SELECTED_START_OFFSET],
                                                      data[intent_parser_constants.SELECTED_END_OFFSET])
        actions = [intent_parser_view.link_text(data[intent_parser_constants.SELECTED_PARAGRAPH_INDEX],
                                                data[intent_parser_constants.SELECTED_START_OFFSET],
                                                data[intent_parser_constants.SELECTED_END_OFFSET],
                                                data[intent_parser_constants.ANALYZE_LINK])]
        actions.extend(self._report_current_analyze_term(document_id))
        return {'actions': actions}

    def process_analyze_yes_to_all(self, document_id, data):
        matching_terms = self.analyze_controller.remove_analyze_result_with_term(document_id,
                                                                                 data[intent_parser_constants.SELECTED_CONTENT_TERM])
        actions = []
        for term in matching_terms:
            actions.append(intent_parser_view.link_text(term.get_paragraph_index(),
                                                        term.get_start_offset(),
                                                        term.get_end_offset(),
                                                        term.get_sbh_uri()))
        actions.extend(self._report_current_analyze_term(document_id))
        return {'actions': actions}

    def process_analyze_no(self, document_id, data):
        self.analyze_controller.remove_analyze_result(document_id,
                                                      data[intent_parser_constants.SELECTED_PARAGRAPH_INDEX],
                                                      data[intent_parser_constants.SELECTED_CONTENT_TERM],
                                                      data[intent_parser_constants.ANALYZE_LINK],
                                                      data[intent_parser_constants.SELECTED_START_OFFSET],
                                                      data[intent_parser_constants.SELECTED_END_OFFSET])
        actions = []
        actions.extend(self._report_current_analyze_term(document_id))
        return {'actions': actions}

    def process_analyze_no_to_all(self, document_id, data):
        self.analyze_controller.remove_analyze_result_with_term(document_id,
                                                                data[intent_parser_constants.SELECTED_CONTENT_TERM])
        actions = []
        actions.extend(self._report_current_analyze_term(document_id))
        return {'actions': actions}

    def process_analyze_never_link(self, document_id: str, user_id: str, data: dict):
        self.analyze_controller.remove_analyze_result_with_term(document_id,
                                                                data[intent_parser_constants.SELECTED_CONTENT_TERM])
        self.analyze_controller.add_to_ignore_terms(user_id, data[intent_parser_constants.SELECTED_CONTENT_TERM])

        actions = []
        actions.extend(self._report_current_analyze_term(document_id))
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
            self.logger.error(''.join(traceback.format_exception(etype=type(e),
                                                                  value=e,
                                                                  tb=e.__traceback__)))
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

    def _report_current_spellchecker_term(self, document_id: str):
        actions = []
        current_result = self.spellcheck_controller.get_first_spellchecker_result(document_id)
        if not current_result:
            buttons = [('Ok', 'process_nop')]
            final_result_action = intent_parser_view.simple_modal_dialog('Found no words not in spelling dictionary!',
                                                                         buttons,
                                                                         'No misspellings!',
                                                                         400,
                                                                         450)
            actions.append(final_result_action)
        else:
            actions = intent_parser_view.report_spelling_results(current_result.get_paragraph_index(),
                                                                 current_result.get_paragraph_index(),
                                                                 current_result.get_start_offset(),
                                                                 current_result.get_end_offset(),
                                                                 current_result.get_matching_term())
        return actions

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
        document_id = intent_parser_utils.get_document_id_from_json_body(json_body)
        intent_parser = LabExperiment(document_id)
        doc_factory = IntentParserDocumentFactory()
        ip_document = doc_factory.from_google_doc(intent_parser.load_from_google_doc())
        self.spellcheck_controller.process_spellchecker(document_id,
                                                        ip_document,
                                                        self._get_user_id(json_body),
                                                        self._get_or_create_cursor_location(json_body))
        search_result_action = self._report_current_spellchecker_term(document_id)
        actions = {'actions': search_result_action}
        return actions

    def process_spellcheck_ignore(self, document_id, data):
        self.spellcheck_controller.remove_spellcheck_result(document_id,
                                                            data[intent_parser_constants.SELECTED_PARAGRAPH_INDEX],
                                                            data[intent_parser_constants.SELECTED_CONTENT_TERM],
                                                            data[intent_parser_constants.SELECTED_START_OFFSET],
                                                            data[intent_parser_constants.SELECTED_END_OFFSET])
        actions = []
        actions.extend(self._report_current_spellchecker_term(document_id))
        return {'actions': actions}

    def process_spellcheck_ignore_all(self, document_id, data):
        self.spellcheck_controller.remove_spellcheck_result_with_term(document_id,
                                                                      data[intent_parser_constants.SELECTED_CONTENT_TERM])
        actions = self._report_current_spellchecker_term(document_id)
        return {'actions': actions}

    def process_spellcheck_add_to_dictionary(self, document_id, user_id, data):
        self.spellcheck_controller.remove_spellcheck_result_with_term(document_id,
                                                                      data[intent_parser_constants.SELECTED_CONTENT_TERM])
        self.spellcheck_controller.add_to_spellcheck_terms(user_id,
                                                           data[intent_parser_constants.SELECTED_CONTENT_TERM])

        actions = []
        actions.extend(self._report_current_spellchecker_term(document_id))
        return {'actions': actions}

    def process_spellcheck_add_to_synbiohub(self, document_id, data):
        item_type_list = []
        for sbol_type in intent_parser_constants.ITEM_TYPES:
            item_type_list += intent_parser_constants.ITEM_TYPES[sbol_type].keys()

        item_type_list = sorted(item_type_list)
        item_types_html = intent_parser_view.generate_html_options(item_type_list)
        lab_ids_html = intent_parser_view.generate_html_options(intent_parser_constants.LAB_IDS_LIST)

        selection = data[intent_parser_constants.SELECTED_CONTENT_TERM]
        display_id = self.sbh.generate_display_id(selection)
        start_paragraph = data[intent_parser_constants.SELECTED_PARAGRAPH_INDEX]
        end_paragraph = data[intent_parser_constants.SELECTED_PARAGRAPH_INDEX]
        start_offset = data[intent_parser_constants.SELECTED_START_OFFSET]
        end_offset = data[intent_parser_constants.SELECTED_END_OFFSET]
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
        self.spellcheck_controller.remove_spellcheck_result(document_id,
                                                            start_paragraph,
                                                            selection,
                                                            start_offset,
                                                            end_offset)
        actions = self._report_current_spellchecker_term(document_id)
        actions.append(dialog_action)
        return {'actions': actions}

    def process_spellcheck_add_previous_word(self, document_id, data):
        intent_parser = LabExperiment(document_id)
        doc_factory = IntentParserDocumentFactory()
        ip_document = doc_factory.from_google_doc(intent_parser.load_from_google_doc())
        start_paragraph_index = data[intent_parser_constants.SELECTED_PARAGRAPH_INDEX]
        end_paragraph_index = data[intent_parser_constants.SELECTED_PARAGRAPH_INDEX]
        selected_paragraph = ip_document.get_paragraph(start_paragraph_index)
        paragraph_text = selected_paragraph.get_text()

        highlight_start_index = data[intent_parser_constants.SELECTED_START_OFFSET]
        highlight_end_index = data[intent_parser_constants.SELECTED_END_OFFSET]
        current_highlighted_term = paragraph_text[highlight_start_index: highlight_end_index+1]
        if highlight_start_index > len(paragraph_text):
            raise IndexError('Start index %d of selected word %s not within range of selected paragraph.' % (
                             highlight_start_index, current_highlighted_term))

        new_highlight_start_index, new_highlight_end_index, new_highlighted_term = self._extend_highlight_left_one_word(highlight_start_index,
                                                                                                                        highlight_end_index,
                                                                                                                        paragraph_text)
        actions = intent_parser_view.report_spelling_results(start_paragraph_index,
                                                             end_paragraph_index,
                                                             new_highlight_start_index,
                                                             new_highlight_end_index,
                                                             new_highlighted_term)
        return {'actions': actions}

    def process_spellcheck_add_next_word(self, document_id, data):
        intent_parser = LabExperiment(document_id)
        doc_factory = IntentParserDocumentFactory()
        ip_document = doc_factory.from_google_doc(intent_parser.load_from_google_doc())
        start_paragraph_index = data[intent_parser_constants.SELECTED_PARAGRAPH_INDEX]
        end_paragraph_index = data[intent_parser_constants.SELECTED_PARAGRAPH_INDEX]
        selected_paragraph = ip_document.get_paragraph(start_paragraph_index)
        paragraph_text = selected_paragraph.get_text()

        highlight_start_index = data[intent_parser_constants.SELECTED_START_OFFSET]
        highlight_end_index = data[intent_parser_constants.SELECTED_END_OFFSET]
        current_highlighted_term = paragraph_text[highlight_start_index: highlight_end_index + 1]
        if highlight_start_index > len(paragraph_text):
            raise IndexError('Start index %d of selected word %s not within range of selected paragraph.' % (
                             highlight_start_index, current_highlighted_term))

        new_highlight_start_index, new_highlight_end_index, new_highlighted_term = self._extend_highlight_right_one_word(highlight_start_index,
                                                                                                                         highlight_end_index,
                                                                                                                         paragraph_text)
        actions = intent_parser_view.report_spelling_results(start_paragraph_index,
                                                             end_paragraph_index,
                                                             new_highlight_start_index,
                                                             new_highlight_end_index,
                                                             new_highlighted_term)

        return {'actions': actions}

    def process_spellcheck_drop_previous_word(self, document_id, data):
        intent_parser = LabExperiment(document_id)
        doc_factory = IntentParserDocumentFactory()
        ip_document = doc_factory.from_google_doc(intent_parser.load_from_google_doc())
        start_paragraph_index = data[intent_parser_constants.SELECTED_PARAGRAPH_INDEX]
        end_paragraph_index = data[intent_parser_constants.SELECTED_PARAGRAPH_INDEX]
        selected_paragraph = ip_document.get_paragraph(start_paragraph_index)
        paragraph_text = selected_paragraph.get_text()

        highlight_start_index = data[intent_parser_constants.SELECTED_START_OFFSET]
        highlight_end_index = data[intent_parser_constants.SELECTED_END_OFFSET]
        current_highlighted_term = paragraph_text[highlight_start_index: highlight_end_index + 1]
        if highlight_start_index > len(paragraph_text):
            raise IndexError('Start index %d of selected word %s not within range of selected paragraph.' % (
                highlight_start_index, current_highlighted_term))

        new_highlight_start_index, new_highlight_end_index, new_highlighted_term = self._trim_highlight_left_one_word(highlight_start_index,highlight_end_index,paragraph_text)
        actions = intent_parser_view.report_spelling_results(start_paragraph_index,
                                                             end_paragraph_index,
                                                             new_highlight_start_index,
                                                             new_highlight_end_index,
                                                             new_highlighted_term)

        return {'actions': actions}

    def process_spellcheck_drop_next_word(self, document_id, data):
        intent_parser = LabExperiment(document_id)
        doc_factory = IntentParserDocumentFactory()
        ip_document = doc_factory.from_google_doc(intent_parser.load_from_google_doc())
        start_paragraph_index = data[intent_parser_constants.SELECTED_PARAGRAPH_INDEX]
        end_paragraph_index = data[intent_parser_constants.SELECTED_PARAGRAPH_INDEX]
        selected_paragraph = ip_document.get_paragraph(start_paragraph_index)
        paragraph_text = selected_paragraph.get_text()

        highlight_start_index = data[intent_parser_constants.SELECTED_START_OFFSET]
        highlight_end_index = data[intent_parser_constants.SELECTED_END_OFFSET]
        current_highlighted_term = paragraph_text[highlight_start_index: highlight_end_index+1]
        if highlight_start_index > len(paragraph_text):
            raise IndexError('Start index %d of selected word %s not within range of selected paragraph.' % (
                highlight_start_index, current_highlighted_term))

        new_highlight_start_index, new_highlight_end_index, new_highlighted_term = self._trim_highlight_right_one_word(highlight_start_index, highlight_end_index, paragraph_text)
        actions = intent_parser_view.report_spelling_results(start_paragraph_index,
                                                             end_paragraph_index,
                                                             new_highlight_start_index,
                                                             new_highlight_end_index,
                                                             new_highlighted_term)
        return {'actions': actions}

    def _trim_highlight_left_one_word(self, highlight_start_index, highlight_end_index, paragraph_text):
        new_highlight_start_index = highlight_start_index
        new_highlight_end_index = highlight_end_index
        new_highlighted_term = paragraph_text[highlight_start_index: highlight_end_index+1]

        cursor = highlight_start_index+1
        has_encountered_stopping_char = False
        stopping_char = [' ', '\n']
        while highlight_start_index < cursor < highlight_end_index:
            if not has_encountered_stopping_char:
                if paragraph_text[cursor] in stopping_char:
                    has_encountered_stopping_char = True
                    if cursor == highlight_end_index:
                        # cursor reached end of highlighted text but no word was found. Set original highlight as new highlight.
                        new_highlight_start_index = highlight_start_index
                        new_highlight_end_index = highlight_end_index
                        new_highlighted_term = paragraph_text[highlight_start_index: highlight_end_index+1]
                else:
                    cursor += 1
            else:
                new_highlight_start_index = cursor+1
                new_highlight_end_index = highlight_end_index
                new_highlighted_term = paragraph_text[cursor: new_highlight_end_index+1]
                break

        return new_highlight_start_index, new_highlight_end_index, new_highlighted_term

    def _trim_highlight_right_one_word(self, highlight_start_index, highlight_end_index, paragraph_text):
        new_highlight_start_index = highlight_start_index
        new_highlight_end_index = highlight_end_index
        new_highlighted_term = paragraph_text[highlight_start_index: highlight_end_index]

        cursor = highlight_end_index-1
        has_encountered_stopping_char = False
        stopping_char = [' ', '\n']
        while highlight_start_index < cursor <= highlight_end_index:
            if not has_encountered_stopping_char:
                if paragraph_text[cursor] in stopping_char:
                    has_encountered_stopping_char = True
                    if cursor == highlight_start_index:
                        # cursor reached start of highlighted text but no word was found. Set original highlight as new highlight.
                        new_highlight_start_index = highlight_start_index
                        new_highlight_end_index = highlight_end_index
                        new_highlighted_term = paragraph_text[highlight_start_index: highlight_end_index]
                else:
                    cursor -= 1
            else:
                new_highlight_start_index = highlight_start_index
                new_highlight_end_index = cursor-1
                new_highlighted_term = paragraph_text[new_highlight_start_index: cursor]
                break

        return new_highlight_start_index, new_highlight_end_index, new_highlighted_term

    def _extend_highlight_left_one_word(self, highlight_start_index, highlight_end_index, paragraph_text):
        cursor = highlight_start_index - 1
        has_encountered_first_char = False
        has_encountered_first_word = False
        stopping_char = [' ', '\n']
        while -1 < cursor < highlight_start_index:
            if not has_encountered_first_char:
                if paragraph_text[cursor] in stopping_char:
                    cursor -= 1
                else:
                    has_encountered_first_char = True
                    if cursor == 0:
                        # if cursor at start of paragraph, then consider all characters detected so far as a single word
                        has_encountered_first_word = True
                        break
            else:
                if paragraph_text[cursor] in stopping_char:
                    has_encountered_first_word = True
                    break
                elif cursor == 0:
                    # if cursor at start of paragraph, then consider all characters detected so far as a single word
                    has_encountered_first_word = True
                    break
                else:
                    cursor -= 1

        current_highlighted_term = paragraph_text[highlight_start_index: highlight_end_index + 1]
        if not has_encountered_first_char or not has_encountered_first_word:
            self.logger.info('No word found before %s' % current_highlighted_term)
            return highlight_start_index, highlight_end_index, current_highlighted_term

        new_highlighted_term = paragraph_text[cursor: highlight_end_index + 1]
        new_highlight_start_index = cursor if cursor == 0 else cursor+1
        new_highlight_end_index = highlight_end_index
        return new_highlight_start_index, new_highlight_end_index, new_highlighted_term

    def _extend_highlight_right_one_word(self, highlight_start_index, highlight_end_index, paragraph_text):
        cursor = highlight_end_index + 1
        has_encountered_first_char = False
        has_encountered_first_word = False
        stopping_char = [' ', '\n']
        paragraph_last_char_index = len(paragraph_text)-1
        while highlight_end_index < cursor < len(paragraph_text):
            if not has_encountered_first_char:
                if paragraph_text[cursor] in stopping_char:
                    cursor += 1
                else:
                    has_encountered_first_char = True
                    if cursor == paragraph_last_char_index:
                        # if cursor at end of paragraph, then consider all characters detected so far as a single word
                        has_encountered_first_word = True
                        break
            else:
                if paragraph_text[cursor] in stopping_char:
                    has_encountered_first_word = True
                    break
                elif cursor == paragraph_last_char_index:
                    # if cursor at end of paragraph, then consider all characters detected so far as a single word
                    has_encountered_first_word = True
                    break
                else:
                    cursor += 1

        current_highlighted_term = paragraph_text[highlight_start_index: highlight_end_index + 1]
        if not has_encountered_first_char or not has_encountered_first_word:
            self.logger.info('No word found after %s' % current_highlighted_term)
            return highlight_start_index, highlight_end_index, current_highlighted_term

        new_highlighted_term = paragraph_text[highlight_start_index: cursor]
        new_highlight_start_index = highlight_start_index
        new_highlight_end_index = cursor - 1
        return new_highlight_start_index, new_highlight_end_index, new_highlighted_term

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
        optional_fields = self._add_optional_parameters(ref_optional_name_to_id,
                                                        param_value_mapping,
                                                        selected_optional_parameters)
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
            self.logger.info('Stopped caching Analyze ignored terms.')
        if self.spellcheck_controller is not None:
            self.spellcheck_controller.stop_synchronizing_spellcheck_terms()
            self.logger.info('Stopped caching Spellcheck terms.')
        if self.sbol_dictionary is not None:
            self.sbol_dictionary.stop_synchronizing_spreadsheet()
            self.logger.info('Stopped caching SBOL Dictionary.')
        if self.strateos_accessor is not None:
            self.strateos_accessor.stop_synchronizing_protocols()
            self.logger.info('Stopped caching Strateos protocols.')

        self.logger.info('Shutdown complete')

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
            search_results.append({'title': title, 'target': target})

        return search_results, self.sparql_similar_count_cache[term]
