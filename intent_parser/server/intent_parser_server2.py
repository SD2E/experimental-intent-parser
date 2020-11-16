from flask import Flask, jsonify, request
from flask_restful import Api, Resource, reqparse
from http import HTTPStatus
from intent_parser.server.intent_parser_processor import IntentParserProcessor
from intent_parser.accessor.strateos_accessor import StrateosAccessor
from intent_parser.accessor.sbol_dictionary_accessor import SBOLDictionaryAccessor
from intent_parser.intent_parser_factory import IntentParserFactory
from intent_parser.intent_parser_sbh import IntentParserSBH
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import argparse
import json
import logging.config
import os
import traceback

logger = logging.getLogger(__name__)
app = Flask(__name__)
api = Api(app)
parser = reqparse.RequestParser()

class Status(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self):
        ip_status = self._ip_processor.get_status()
        return ip_status, HTTPStatus.OK

class DocumentReport(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self, doc_id):
        report = self._ip_processor.process_document_report(doc_id)
        return jsonify(report), HTTPStatus.OK

class DocumentRequest(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self, doc_id):
        structure_request = self._ip_processor.process_document_request(doc_id)
        return jsonify(structure_request), HTTPStatus.OK

    def post(self):
        # previously called generateStructuredRequest
        structure_request = self._ip_processor.process_generate_structured_request(request.get_json())
        return structure_request, HTTPStatus.OK # TODO

class ExperimentRequestDocuments(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self):
        er_documents = self._ip_processor.process_experiment_request_documents()
        return jsonify(er_documents), HTTPStatus.OK

class ExperimentStatus(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self, doc_id):
        experiment_status = self._ip_processor.process_experiment_status_GET(doc_id)
        return experiment_status, HTTPStatus.OK

    def post(self):
        # previously called reportExperimentStatus
        experiment_status = self._ip_processor.process_experiment_status_POST(request.get_json())
        return experiment_status, HTTPStatus.OK # TODO

class OpilRequest(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self, doc_id):
        opil_output = self._ip_processor.process_opil_GET_request(doc_id)
        return opil_output, HTTPStatus.OK

    def post(self):
        # previously called generateOpilRequest
        opil_output = self._ip_processor.process_opil_POST_request(request.get_json())
        return opil_output, HTTPStatus.OK # TODO

class RunExperiment(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self, doc_id):
        experiment_data = self._ip_processor.process_run_experiment_GET(doc_id)
        return jsonify(experiment_data), HTTPStatus.OK

    def post(self):
        # previously called executeExperiment
        experiment_data = self._ip_processor.process_run_experiment_POST(request.get_json())
        return experiment_data, HTTPStatus.OK # TODO

class UpdateExperimentStatus(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def get(self, doc_id):
        status_data = self._ip_processor.process_update_experiment_status(doc_id)
        return jsonify(status_data), HTTPStatus.OK

class AddBySpelling(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        spelling_data = self._ip_processor.process_add_by_spelling(request.get_json())
        return jsonify(spelling_data), HTTPStatus.OK # TODO

class AddToSynbiohub(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        sbh_data = self._ip_processor.process_add_to_syn_bio_hub(request.get_json())
        return sbh_data, HTTPStatus.OK # TODO

class AnalyzeDocument(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        analyze_data = self._ip_processor.process_analyze_document(request.get_json())
        return analyze_data, HTTPStatus.OK

class ButtonClick(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        button_response = self._ip_processor.process_button_click(request.get_json())
        return button_response, HTTPStatus.OK # TODO

class CalculateSamples(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        table_template = self._ip_processor.process_calculate_samples(request.get_json())
        return table_template, HTTPStatus.OK

class CreateTableTemplate(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        table_template = self._ip_processor.process_create_table_template(request.get_json())
        return table_template, HTTPStatus.OK

class ExperimentExecutionStatus(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        experiment_data = self._ip_processor.process_experiment_execution_status(request.get_json())
        return experiment_data, HTTPStatus.OK  # TODO

class ExperimentStatus(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        experiment_data = self._ip_processor.process_experiment_status_POST(request.get_json())
        return experiment_data, HTTPStatus.OK  # TODO

class Message(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        message = self._ip_processor.process_message(request.get_json())
        return message, HTTPStatus.OK  # TODO

class SearchSynBioHub(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        sbh_data = self._ip_processor.process_search_syn_bio_hub(request.get_json())
        return sbh_data, HTTPStatus.OK # TODO

class SubmitForm(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        submit_form_data = self._ip_processor.process_submit_form(request.get_json())
        return submit_form_data, HTTPStatus.OK # TODO

class UpdateExperimentResult(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        experiment_result = self._ip_processor.process_update_exp_results(request.get_json())
        return experiment_result, HTTPStatus.OK

class ValidateStructuredRequest(Resource):
    def __init__(self, ip_processor):
        self._ip_processor = ip_processor

    def post(self):
        sr_result = self._ip_processor.process_validate_structured_request(request.get_json())
        return sr_result, HTTPStatus.OK

def setup_api_resources(ip_processor):
    api.add_resource(Status,
                     '/status',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(DocumentReport,
                     '/document_report/d/<string:doc_id>',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(DocumentRequest,
                     '/document_request/d/<string:doc_id>',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(ExperimentRequestDocuments,
                     '/experiment_request_documents',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(ExperimentStatus,
                     '/experiment_status/d/<string:doc_id>',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(OpilRequest,
                     '/opil_request/d/<string:doc_id>',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(RunExperiment,
                     '/run_experiment/d/<string:doc_id>',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(UpdateExperimentStatus,
                     '/update_experiment_status/d/<string:doc_id>',
                     resource_class_kwargs={'ip_processor': ip_processor})

    api.add_resource(AddBySpelling,
                     '/addBySpelling',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(AddToSynbiohub,
                     '/addToSynBioHub',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(AnalyzeDocument,
                     '/analyzeDocument',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(ButtonClick,
                     '/buttonClick',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(CalculateSamples,
                     '/calculateSamples',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(CreateTableTemplate,
                     '/createTableTemplate',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(ExperimentExecutionStatus,
                     '/experimentExecutionStatus',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(Message,
                     '/message',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(SearchSynBioHub,
                     '/searchSynBioHub',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(SubmitForm,
                     '/submitForm',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(UpdateExperimentResult,
                     '/updateExperimentalResults',
                     resource_class_kwargs={'ip_processor': ip_processor})
    api.add_resource(ValidateStructuredRequest,
                     '/validateStructuredRequest',
                     resource_class_kwargs={'ip_processor': ip_processor})

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
        logging.basicConfig(level=default_level,
                            format="[%(levelname)-8s] %(asctime)-24s %(filename)-23s line:%(lineno)-4s  %(message)s")

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

    parser.add_argument('-u', '--username', nargs='?',
                        required=True, help='SynBioHub username.')

    input_args = parser.parse_args()
    setup_logging()
    ip_processor = None
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
        ip_processor = IntentParserProcessor(sbh, sbol_dictionary, strateos_accessor, intent_parser_factory)
        ip_processor.initialize_intent_parser_processor()
        setup_api_resources(ip_processor)
        app.run(host=input_args.bind_host, port=input_args.bind_port)
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
