from flask import Flask, g, jsonify
from http import HTTPStatus
from intent_parser.server.intent_parser_processor import IntentParserProcessor
from intent_parser.accessor.strateos_accessor import StrateosAccessor
from intent_parser.accessor.sbol_dictionary_accessor import SBOLDictionaryAccessor
from intent_parser.intent_parser_exceptions import RequestErrorException
from intent_parser.intent_parser_factory import IntentParserFactory
from intent_parser.intent_parser_sbh import IntentParserSBH
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import argparse
import json
import logging.config
import os
import traceback

"""A script in charge of listening into HTTP Requests.
"""
logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.errorhandler(RequestErrorException)
def request_error_exception_handler(error):
    return (jsonify({'errors': error.get_errors(), 'warnings': error.get_warnings()}),
            error.get_http_status())

@app.errorhandler(HTTPStatus.NOT_FOUND)
def page_not_found(error):
    return 'Request not identified by Intent Parser', HTTPStatus.NOT_FOUND

@app.route('/status')
def status():
    intent_parser_processor = get_processor()
    ip_status = intent_parser_processor.get_status()
    return ip_status, HTTPStatus.OK

@app.route('/document_report/<doc_id>', methods=['GET'])
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

@app.route('/run_experiment', methods=['GET'])
def run_experiment():
    pass

@app.route('/update_experiment_status', methods=['GET'])
def update_experiment_status():
    pass

@app.route('/analyzeDocument')
def analyzeDocument():
    pass


@app.route('/addBySpelling')
def addBySpelling():
    pass


@app.route('/addToSynBioHub')
def addToSynBioHub():
    pass


@app.route('/buttonClick')
def buttonClick():
    pass


@app.route('/calculateSamples')
def calculateSamples():
    pass


@app.route('/createTableTemplate')
def createTableTemplate():
    pass


@app.route('/executeExperiment')
def executeExperiment():
    pass


@app.route('/generateStructuredRequest')
def generateStructuredRequest():
    pass



@app.route('/message')
def message():
    pass


@app.route('/reportExperimentStatus')
def reportExperimentStatus():
    pass


@app.route('/searchSynBioHub')
def searchSynBioHub():
    pass


@app.route('/submitForm')
def submitForm():
    pass


@app.route('/updateExperimentalResults')
def updateExperimentalResults():
    pass


@app.route('/validateStructuredRequest')
def validateStructuredRequest():
    pass


def initialize_intent_parser_processor():
    pass


def get_processor():
    return g.processor


@app.teardown_appcontext
def teardown_processor(exception):
    intent_server_processor = g.pop('processor', None)

    if intent_server_processor is not None:
        intent_server_processor.stop()


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

    parser.add_argument('-e', '--execute_experiment', nargs='?',
                        required=False,
                        help='Nonce credential used for authorizing an API endpoint to execute an experiment.')

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
        ip_processor.initialize_server()
        g.processor = ip_processor
        app.run(host=input_args.bind_host, port=input_args.bind_port)
    except (KeyboardInterrupt, SystemExit) as ex:
        return
    except Exception as ex:
        logger.warning(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
    finally:
        if ip_processor is not None:
            ip_processor.stop()


if __name__ == "__main__":
    main()
