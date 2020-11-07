from flask import Flask, jsonify, request
from http import HTTPStatus
from intent_parser.intent_parser_exceptions import RequestErrorException
from werkzeug.exceptions import HTTPException
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

"""A script in charge of listening for HTTP Requests.
"""

logger = logging.getLogger(__name__)
app = Flask(__name__)
ip_processor = None

@app.errorhandler(RequestErrorException)
def handle_request_error_exception(error):
    return (jsonify({'errors': error.get_errors(), 'warnings': error.get_warnings()}),
            error.get_http_status())

@app.errorhandler(HTTPStatus.NOT_FOUND)
def handle_page_not_found(error):
    logger.error(str(error))
    return 'Request not identified by Intent Parser', HTTPStatus.NOT_FOUND

@app.errorhandler(HTTPException)
def handle_http_exception(error):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = error.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": error.code,
        "name": error.name,
        "description": error.description,
    })
    response.content_type = "application/json"
    return response

@app.errorhandler(Exception)
def handle_exception(error):
    # pass through HTTP errors
    if isinstance(error, HTTPException):
        return error

    # now you're handling non-HTTP exceptions only
    logger.error(str(error))
    return str(error), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route('/status')
def status():
    intent_parser_processor = get_processor()
    ip_status = intent_parser_processor.get_status()
    return ip_status, HTTPStatus.OK

@app.route('/document_report/d/<doc_id>', methods=['GET'])
def document_report(doc_id):
    intent_parser_processor = get_processor()
    report = intent_parser_processor.process_document_report(doc_id)
    return jsonify(report), HTTPStatus.OK

@app.route('/document_request/<doc_id>', methods=['GET'])
def document_request(doc_id):
    intent_parser_processor = get_processor()
    structure_request = intent_parser_processor.process_document_request(doc_id)
    return jsonify(structure_request), HTTPStatus.OK

@app.route('/experiment_request_documents', methods=['GET'])
def experiment_request_documents():
    intent_parser_processor = get_processor()
    er_documents = intent_parser_processor.process_experiment_request_documents()
    return jsonify(er_documents), HTTPStatus.OK

@app.route('/experiment_status/<doc_id>', methods=['GET'])
def experiment_status(doc_id):
    intent_parser_processor = get_processor()
    experiment_status = intent_parser_processor.process_experiment_status(doc_id)
    return experiment_status, HTTPStatus.OK

@app.route('/opil_request/<doc_id>', methods=['GET'])
def opil_request(doc_id):
    intent_parser_processor = get_processor()
    opil_output = intent_parser_processor.process_opil_GET_request(doc_id)
    return opil_output, HTTPStatus.OK

@app.route('/run_experiment/<doc_id>', methods=['GET'])
def run_experiment(doc_id):
    intent_parser_processor = get_processor()
    experiment_data = intent_parser_processor.process_run_experiment(doc_id)
    return jsonify(experiment_data), HTTPStatus.OK

@app.route('/update_experiment_status/<doc_id>', methods=['GET'])
def update_experiment_status(doc_id):
    intent_parser_processor = get_processor()
    status_data = intent_parser_processor.process_update_experiment_status(doc_id)
    return jsonify(status_data), HTTPStatus.OK

@app.route('/analyzeDocument/<doc_id>', methods=['POST'])
def analyze_document(doc_id):
    intent_parser_processor = get_processor()
    analyze_data = intent_parser_processor.process_analyze_document(doc_id)
    return jsonify(analyze_data), HTTPStatus.OK

@app.route('/addBySpelling', methods=['POST'])
def add_by_spelling():
    intent_parser_processor = get_processor()
    spelling_data = intent_parser_processor.process_add_by_spelling(request.json)
    return jsonify(spelling_data), HTTPStatus.OK

@app.route('/addToSynBioHub', methods=['POST'])
def add_to_synbiohub():
    intent_parser_processor = get_processor()
    sbh_data = intent_parser_processor.process_add_to_syn_bio_hub(request.json)
    return jsonify(sbh_data), HTTPStatus.OK

@app.route('/buttonClick', methods=['POST'])
def button_click():
    intent_parser_processor = get_processor()
    button_response = intent_parser_processor.process_button_click(request.json)
    return jsonify(button_response), HTTPStatus.OK

@app.route('/calculateSamples', methods=['POST'])
def calculate_samples():
    intent_parser_processor = get_processor()
    samples = intent_parser_processor.process_calculate_samples(request.json)
    return jsonify(samples), HTTPStatus.OK

@app.route('/createTableTemplate', methods=['POST'])
def create_table_template():
    intent_parser_processor = get_processor()
    table_template = intent_parser_processor.process_create_table_template(request.json)
    return jsonify(table_template), HTTPStatus.OK

@app.route('/executeExperiment', methods=['POST'])
def execute_experiment():
    intent_parser_processor = get_processor()
    experiment_data = intent_parser_processor.process_execute_experiment(request.json)
    return jsonify(experiment_data), HTTPStatus.OK

@app.route('/experimentExecutionStatus', methods=['POST'])
def experiment_execution_status():
    intent_parser_processor = get_processor()
    experiment_data = intent_parser_processor.process_experiment_execution_status(request.json)
    return jsonify(experiment_data), HTTPStatus.OK

@app.route('/generateOpilRequest', methods=['POST'])
def generate_opil_post_request():
    intent_parser_processor = get_processor()
    opil_data = intent_parser_processor.process_opil_POST_request(request.host_url, request.json)
    return jsonify(opil_data), HTTPStatus.OK

@app.route('/generateStructuredRequest', methods=['POST'])
def generate_structured_request():
    intent_parser_processor = get_processor()
    sr_data = intent_parser_processor.process_generate_structured_request(request.host_url, request.json)
    return jsonify(sr_data), HTTPStatus.OK

@app.route('/message', methods=['POST'])
def message():
    intent_parser_processor = get_processor()
    result = intent_parser_processor.process_message(request.json)
    return result, HTTPStatus.OK

@app.route('/reportExperimentStatus', methods=['POST'])
def report_experiment_status():
    intent_parser_processor = get_processor()
    exp_status = intent_parser_processor.process_report_experiment_status(request.json)
    return jsonify(exp_status), HTTPStatus.OK

@app.route('/searchSynBioHub', methods=['POST'])
def search_SynBioHub():
    intent_parser_processor = get_processor()
    search_result = intent_parser_processor.process_search_syn_bio_hub(request.json)
    return jsonify(search_result), HTTPStatus.OK

@app.route('/submitForm', methods=['POST'])
def submit_form():
    intent_parser_processor = get_processor()
    form_result = intent_parser_processor.process_submit_form(request.json)
    return jsonify(form_result), HTTPStatus.OK

@app.route('/updateExperimentalResults', methods=['POST'])
def update_experimental_results():
    intent_parser_processor = get_processor()
    exp_result = intent_parser_processor.process_update_exp_results(request.json)
    return jsonify(exp_result), HTTPStatus.OK

@app.route('/validateStructuredRequest', methods=['POST'])
def validate_structured_request():
    intent_parser_processor = get_processor()
    sr_result = intent_parser_processor.process_validate_structured_request(request.json)
    return jsonify(sr_result), HTTPStatus.OK

def setup_ip_processor(input_args=None):
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
        ip_processor.initialize_server()
        return ip_processor
    except (KeyboardInterrupt, SystemExit):
        return
    except Exception as ex:
        logger.warning(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))

def get_processor():
    global ip_processor
    if ip_processor is None:
        raise RequestErrorException(HTTPStatus.INTERNAL_SERVER_ERROR,
                                    errors=['Intent Parser Processor unsuccessfully initialized.'])
    return ip_processor

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
    global ip_processor
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
        ip_processor.initialize_server()
        app.run(host=input_args.bind_host, port=input_args.bind_port)
    except (KeyboardInterrupt, SystemExit):
        return
    except Exception as ex:
        logger.warning(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))


if __name__ == "__main__":
    main()
