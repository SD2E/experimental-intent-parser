from flask import Flask, request, redirect, jsonify
from flask_restful import Api, Resource
from flasgger import Swagger
from http import HTTPStatus
from intent_parser.accessor.strateos_accessor import StrateosAccessor
from intent_parser.accessor.sbol_dictionary_accessor import SBOLDictionaryAccessor
from intent_parser.intent_parser_exceptions import IntentParserException, RequestErrorException
from intent_parser.intent_parser_factory import IntentParserFactory
from intent_parser.accessor.intent_parser_sbh import IntentParserSBH
from intent_parser.server.intent_parser_processor import IntentParserProcessor
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import json
import logging.config
import os
import traceback

logger = logging.getLogger(__name__)
app = Flask(__name__)
api = Api(app)

# Create an APISpec
template = {
    'swagger': '2.0',
    'info': {
        'title': 'Intent Parser API',
        'description': 'API for calling Intent Parser.',
        'version': '3.0'
    }
}
app.config['DEBUG'] = True
app.config['SWAGGER'] = {
    'title': 'Intent Parser API',
    'uiversion': 3,
    'specs_route': '/api/'
}
Swagger(app, template=template)

class GetIntentParserHome(Resource):
    def __init__(self):
        pass

    def get(self):
        return redirect("https://github.com/SD2E/experimental-intent-parser", code=302)

class GetStatus(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self):
        """
        Reports the status of intent parser server.
        ---
        responses:
            200:
                description: A message indicating the server is properly setup and running.
            503:
                description: A message indicating the server not properly setup and will not run correctly.
        """
        try:
            ip_status = self._ip_processor.get_status()
            return ip_status, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class GetDocumentReport(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self, doc_id):
        """
        Generates a document report for a given experiment.
        ---
        parameters:
            - in: path
              name: doc_id
              type: string
              required: true
              description: ID of document
        """
        try:
            report = self._ip_processor.process_document_report(doc_id)
            return report, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR


class GetExperimentRequestDocuments(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self):
        """
        Retrieves a list of experiment request document ID.
        ---
        responses:
            200:
                schema:
                    properties:
                    doc_id:
                        type: object
        """
        try:
            er_documents = self._ip_processor.process_experiment_request_documents()
            return er_documents, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class GetExperimentStatus(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self, doc_id):
        """
        Reports the status of a given experiment in the TA4 pipeline.
        ---
        parameters:
            - in: path
              name: doc_id
              type: string
              required: true
              description: ID of document
        """
        try:
            experiment_status = self._ip_processor.process_experiment_status_get(doc_id)
            return experiment_status, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class GetGenerateStructuredRequest(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self, doc_id):
        """
        Generates a structured request for a given experiment.
        ---
        parameters:
            - in: path
              name: doc_id
              type: string
              required: true
              description: ID of document
        """
        # previously called document_request
        try:
            structure_request = self._ip_processor.process_document_request(doc_id)
            return structure_request, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class GetOpilRequest(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self, doc_id):
        """
        Generates OPIL data for a given experiment.
        ---
        parameters:
            - in: path
              name: doc_id
              type: string
              required: true
              description: ID of document
        """
        try:
            opil_output = self._ip_processor.process_opil_get_request(doc_id)
            return opil_output, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class GetRunExperiment(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self, doc_id):
        """
        Executes a given experiment.
        ---
        parameters:
            - in: path
              name: doc_id
              type: string
              required: true
              description: ID of document
        """
        try:
            experiment_data = self._ip_processor.process_run_experiment_get(doc_id)
            return experiment_data, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class GetUpdateExperimentStatus(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self, doc_id):
        """
        Updates the status of an experiment.
        ---
        parameters:
            - in: path
              name: doc_id
              type: string
              required: true
              description: ID of document
        """
        try:
            status_data = self._ip_processor.process_update_experiment_status(doc_id)
            return status_data, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class PostAddBySpelling(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        """
        Checks spelling in a given document.
        ---
        parameters:
            - in: body
              name: body
              schema:
                properties:
                    doc_id:
                        type: string
                    userEmail:
                        type: string
        """
        try:
            spelling_data = self._ip_processor.process_add_by_spelling(request.get_json())
            return spelling_data, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class PostAddToSynbiohub(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        """
        Adds terms in a given document to SynbioHub.
        ---
        parameters:
            - in: body
              name: body
              schema:
                properties:
                    doc_id:
                        type: string
                    data:
                        properties:
                            start:
                                properties:
                                    paragraphIndex:
                                        type: number
                                    offset:
                                        type: number
                            end:
                                properties:
                                    paragraphIndex:
                                        type: number
                                    offset:
                                        type: number
        """
        try:
            sbh_data = self._ip_processor.process_add_to_syn_bio_hub(request.get_json())
            return sbh_data, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class PostAnalyzeDocument(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        """
        Links terms in a given document to SynbioHub.
        ---
        parameters:
            - in: body
              name: body
              schema:
                properties:
                    doc_id:
                        type: string
                    userEmail:
                        type: string
        """
        try:
            analyze_data = self._ip_processor.process_analyze_document(request.get_json())
            return analyze_data, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR


class PostButtonClick(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        try:
            button_response = self._ip_processor.process_button_click(request.get_json())
            return button_response, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class PostCalculateSamples(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        """
        Updates measurement samples in a given experiment.
        ---
        parameters:
            - in: body
              name: body
              schema:
                properties:
                    doc_id:
                        type: string
        """
        try:
            table_template = self._ip_processor.process_calculate_samples(request.get_json())
            return table_template, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class PostCreateTableTemplate(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        """
        Show options to create a table template in a given document.
        ---
        parameters:
            - in: body
              name: body
              schema:
                properties:
                    doc_id:
                        type: string
                    data:
                        properties:
                            childIndex:
                                type: number
                            tableType:
                                type: string
        """
        try:
            table_template = self._ip_processor.process_create_table_template(request.get_json())
            return table_template, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class PostExperimentExecutionStatus(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        # TODO: Implement when addressing Issue #257
        experiment_data = self._ip_processor.process_experiment_execution_status(request.get_json())
        return experiment_data, HTTPStatus.OK

class PostExperimentStatus(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        """
        Reports the status of a given experiment in the TA4 pipeline.
        ---
        parameters:
            - in: body
              name: body
              schema:
                properties:
                    doc_id:
                        type: string
        """
        # previously called reportExperimentStatus
        try:
            experiment_status = self._ip_processor.process_experiment_status_post(request.get_json())
            return experiment_status, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class PostGenerateStructuredRequest(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        """
        Generates a structured request for a given experiment.
        ---
        parameters:
            - in: body
              name: body
              schema:
                properties:
                    doc_id:
                        type: string
        """
        try:
            structure_request = self._ip_processor.process_generate_structured_request(request.host_url, request.get_json())
            return structure_request, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class PostMessage(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        message = self._ip_processor.process_message(request.get_json())
        return message, HTTPStatus.OK

class PostOpilRequest(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        """
        Generates OPIL data for a given experiment.
        ---
        parameters:
            - in: body
              name: body
              schema:
                properties:
                    doc_id:
                        type: string
        """
        # previously called generateOpilRequest
        try:
            opil_output = self._ip_processor.process_opil_post_request(request.host_url, request.get_json())
            return opil_output, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class PostRunExperiment(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        """
        Executes a given experiment.
        ---
        parameters:
            - in: body
              name: body
              schema:
                properties:
                    doc_id:
                        type: string
        """
        # previously called executeExperiment
        try:
            experiment_data = self._ip_processor.process_run_experiment_post(request.get_json())
            return experiment_data, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class PostSearchSynBioHub(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        """
        Queries SynBioHub for a term in a given document.
        ---
        parameters:
            - in: body
              name: body
              schema:
                properties:
                    data:
                        properties:
                            term:
                                type: string
                            offset:
                                type: number
        """
        try:
            sbh_data = self._ip_processor.process_search_syn_bio_hub(request.get_json())
            return sbh_data, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class PostSubmitForm(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        try:
            submit_form_data = self._ip_processor.process_submit_form(request.get_json())
            return submit_form_data, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class PostUpdateExperimentResult(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        """
        Scans SynBioHub for experiments related to the given document and reports information about completed experiments.
        ---
        parameters:
            - in: body
              name: body
              schema:
                properties:
                    doc_id:
                        type: string
        """
        try:
            experiment_result = self._ip_processor.process_update_exp_results(request.get_json())
            return experiment_result, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

class PostValidateStructuredRequest(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        """
        Validates information about an experiment for a given document.
        ---
        parameters:
            - in: body
              name: body
              schema:
                properties:
                    doc_id:
                        type: string
        """
        try:
            sr_result = self._ip_processor.process_validate_structured_request(request.get_json())
            return sr_result, HTTPStatus.OK
        except RequestErrorException as err:
            status_code = err.get_http_status()
            res = {"errors": err.get_errors(),
                   "warnings": err.get_warnings()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR


class IntentParserServer(object):
    def __init__(self, sbh_username, sbh_password, datacatalog_authn, transcriptic_credential):
        self.ip_processor = None
        self._sbh_username = sbh_username
        self._sbh_password = sbh_password
        self._datacatalog_authn = datacatalog_authn
        self._transcriptic_credential = transcriptic_credential

    def initialize(self):
        if self.ip_processor:
            return
        sbh = IntentParserSBH(self._sbh_username, self._sbh_password)
        sbol_dictionary = SBOLDictionaryAccessor(intent_parser_constants.SD2_SPREADSHEET_ID, sbh)
        datacatalog_config = {"mongodb": {"database": "catalog_staging", "authn": self._datacatalog_authn}}
        strateos_accessor = StrateosAccessor(self._transcriptic_credential)
        intent_parser_factory = IntentParserFactory(datacatalog_config, sbh, sbol_dictionary)
        self.ip_processor = IntentParserProcessor(sbh, sbol_dictionary, strateos_accessor, intent_parser_factory)
        self.ip_processor.initialize_intent_parser_processor()
        self._setup_api_resources()

    def run_server(self, host, port):
        if not self.ip_processor:
            logger.info('IntentParserServer needs to be initialized.')
            return

        try:
            app.run(host, port)
        except (KeyboardInterrupt, SystemExit):
            logger.info('Shutting down Intent Parser Server.')
            return
        except Exception as ex:
            logger.warning(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
        finally:
            if self.ip_processor:
                self.ip_processor.stop()
                self.ip_processor = None

    def _setup_api_resources(self):
        api.add_resource(GetIntentParserHome,
                         '/home')
        api.add_resource(GetStatus,
                         '/status',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(GetDocumentReport,
                         '/document_report/d/<string:doc_id>',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(GetGenerateStructuredRequest,
                         '/generateStructuredRequest/d/<string:doc_id>',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(GetExperimentRequestDocuments,
                         '/experiment_request_documents',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(GetExperimentStatus,
                         '/experiment_status/d/<string:doc_id>',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(GetOpilRequest,
                         '/generateOpilRequest/d/<string:doc_id>',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(GetRunExperiment,
                         '/run_experiment/d/<string:doc_id>',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(GetUpdateExperimentStatus,
                         '/update_experiment_status/d/<string:doc_id>',
                         resource_class_kwargs={'ip_processor': self.ip_processor})

        api.add_resource(PostAddBySpelling,
                         '/addBySpelling',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(PostAddToSynbiohub,
                         '/addToSynBioHub',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(PostAnalyzeDocument,
                         '/analyzeDocument',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(PostButtonClick,
                         '/buttonClick',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(PostCalculateSamples,
                         '/calculateSamples',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(PostCreateTableTemplate,
                         '/createTableTemplate',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(PostExperimentExecutionStatus,
                         '/experimentExecutionStatus',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(PostExperimentStatus,
                         '/experiment_status',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(PostGenerateStructuredRequest,
                         '/generateStructuredRequest',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(PostMessage,
                         '/message',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(PostOpilRequest,
                         '/generateOpilRequest',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(PostRunExperiment,
                         '/run_experiment',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(PostSearchSynBioHub,
                         '/searchSynBioHub',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(PostSubmitForm,
                         '/submitForm',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(PostUpdateExperimentResult,
                         '/updateExperimentalResults',
                         resource_class_kwargs={'ip_processor': self.ip_processor})
        api.add_resource(PostValidateStructuredRequest,
                         '/validateStructuredRequest',
                         resource_class_kwargs={'ip_processor': self.ip_processor})



