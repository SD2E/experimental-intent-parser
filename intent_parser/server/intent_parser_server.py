from flask import Flask, g, jsonify
from intent_parser.server.intent_parser_processor import IntentParserServer
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


@app.route('/status')
def status():
    return jsonify('Intent Parser Server is Up and Running')


@app.route('/document_report/<resource>')
def document_report():
    intent_parser_processor = get_intent_parser_processor()
    intent_parser_processor.process_document_report()

@app.route('/document_request')
def document_request():
    pass


@app.route('/run_experiment')
def run_experiment():
    pass


@app.route('/experiment_request_documents')
def experiment_request_documents():
    pass


@app.route('/experiment_status')
def experiment_status():
    pass


@app.route('/update_experiment_status')
def update_experiment_status():
    pass


@app.route('/insert_table_hints')
def insert_table_hints():
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


@app.route('/executeExperiment')
def executeExperiment():
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


def get_intent_parser_processor():
    return g.ip_processor


@app.teardown_appcontext
def teardown_intent_parser_processor():
    intent_server_processor = g.pop('ip_processor', None)

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
