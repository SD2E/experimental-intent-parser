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
from intent_parser.server.config import env_config
import argparse
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import json
import logging.config
import os
import traceback

curr_path = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(__name__)
app = Flask(__name__)
api = Api(app)

# Create an APISpec
template = {
    'swagger': '2.0',
    'info': {
        'title': 'Intent Parser API',
        'description': 'API for access features supported in Intent Parser.',
        'version': '3.0'
    }
}
app.config.from_object(env_config[os.getenv("IP_FLASK_ENV")])
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
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
                   "warnings": err.get_errors()}
            return res, status_code
        except IntentParserException as err:
            return err.get_message(), HTTPStatus.INTERNAL_SERVER_ERROR

def _setup_api_resources(ip_processor):
    api.add_resource(GetIntentParserHome,
                     '/home')
    api.add_resource(GetStatus,
                     '/status',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(GetDocumentReport,
                     '/document_report/d/<string:doc_id>',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(GetGenerateStructuredRequest,
                     '/generateStructuredRequest/d/<string:doc_id>',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(GetExperimentRequestDocuments,
                     '/experiment_request_documents',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(GetExperimentStatus,
                     '/experiment_status/d/<string:doc_id>',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(GetOpilRequest,
                     '/generateOpilRequest/d/<string:doc_id>',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(GetRunExperiment,
                     '/run_experiment/d/<string:doc_id>',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(GetUpdateExperimentStatus,
                     '/update_experiment_status/d/<string:doc_id>',
                     resource_class_kwargs={'ip_processor': ip_processor})

    api.add_resource(PostAddBySpelling,
                     '/addBySpelling',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(PostAddToSynbiohub,
                     '/addToSynBioHub',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(PostAnalyzeDocument,
                     '/analyzeDocument',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(PostButtonClick,
                     '/buttonClick',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(PostCalculateSamples,
                     '/calculateSamples',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(PostCreateTableTemplate,
                     '/createTableTemplate',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(PostExperimentExecutionStatus,
                     '/experimentExecutionStatus',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(PostExperimentStatus,
                     '/experiment_status',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(PostGenerateStructuredRequest,
                     '/generateStructuredRequest',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(PostMessage,
                     '/message',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(PostOpilRequest,
                     '/generateOpilRequest',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(PostRunExperiment,
                     '/run_experiment',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(PostSearchSynBioHub,
                     '/searchSynBioHub',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(PostSubmitForm,
                     '/submitForm',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(PostUpdateExperimentResult,
                     '/updateExperimentalResults',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(PostValidateStructuredRequest,
                     '/validateStructuredRequest',
                     resource_class_kwargs={'ip_processor': ip_processor})

def _setup_logging(
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
        logging.basicConfig(level=default_level,
                            format="[%(levelname)-8s] %(asctime)-24s %(filename)-23s line:%(lineno)-4s  %(message)s")

    logger.addHandler(logging.FileHandler('intent_parser_server.log'))
    logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.CRITICAL)
    logging.getLogger("googleapiclient.discovery").setLevel(logging.CRITICAL)

def start_server(ip_processor, host, port):
    _setup_api_resources(ip_processor)
    app.run(host, port)

def main():
    cmd_parser = argparse.ArgumentParser(description='Processes an experimental design.')
    cmd_parser.add_argument('-a', '--authn', nargs='?',
                            required=True, help='Authorization token for data catalog.')

    cmd_parser.add_argument('-b', '--bind-host', nargs='?', default='0.0.0.0',
                            required=False, help='IP address to bind to.')

    cmd_parser.add_argument('-c', '--collection', nargs='?',
                            required=True, help='Collection url.')

    cmd_parser.add_argument('-i', '--spreadsheet-id', nargs='?', default=intent_parser_constants.SD2_SPREADSHEET_ID,
                            required=False, help='Dictionary spreadsheet id.')

    cmd_parser.add_argument('-l', '--bind-port', nargs='?', type=int, default=8081,
                            required=False, help='TCP Port to listen on.')

    cmd_parser.add_argument('-p', '--password', nargs='?',
                            required=True, help='SynBioHub password.')

    cmd_parser.add_argument('-s', '--spoofing-prefix', nargs='?',
                            required=False, help='SBH spoofing prefix.')

    cmd_parser.add_argument('-t', '--transcriptic', nargs='?',
                            required=False, help='Path to transcriptic configuration file.')

    cmd_parser.add_argument('-u', '--username', nargs='?',
                            required=True, help='SynBioHub username.')

    input_args = cmd_parser.parse_args()
    _setup_logging()
    ip_processor = None
    try:
        sbh = IntentParserSBH()
        sbol_dictionary = SBOLDictionaryAccessor(intent_parser_constants.SD2_SPREADSHEET_ID, sbh)
        datacatalog_config = {"mongodb": {"database": "catalog_staging", "authn": input_args.authn}}
        strateos_accessor = StrateosAccessor(input_args.transcriptic)
        intent_parser_factory = IntentParserFactory(datacatalog_config, sbh, sbol_dictionary)
        ip_processor = IntentParserProcessor(sbh, sbol_dictionary, strateos_accessor, intent_parser_factory)
        ip_processor.initialize_intent_parser_processor()
        start_server(ip_processor, input_args.bind_host, input_args.bind_port)

    except (KeyboardInterrupt, SystemExit):
        logger.info('Shutting down Intent Parser Server.')
        return
    except Exception as ex:
        logger.warning(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
    finally:
        if ip_processor:
            ip_processor.stop()

if __name__ == "__main__":
    main()
