from flask import Flask, g
from intent_parser.server.intent_parser_processor import IntentParserProcessor
from intent_parser.accessor.strateos_accessor import StrateosAccessor
from intent_parser.accessor.sbol_dictionary_accessor import SBOLDictionaryAccessor
from intent_parser.intent_parser_factory import IntentParserFactory
from intent_parser.intent_parser_sbh import IntentParserSBH
import intent_parser.server.intent_parser_server as ip_server_api
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import argparse
import json
import logging.config
import os
import traceback

logger = logging.getLogger(__name__)

def create_app(ip_processor, test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.register_blueprint(ip_server_api)
    with app.app_context():
        ip_processor.initialize_server()
    return app

def create_intent_parser_processor(input_args):
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
        # ip_processor.initialize_server()
        return ip_processor
    except (KeyboardInterrupt, SystemExit):
        return
    except Exception as ex:
        logger.warning(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
    finally:
        if ip_processor is not None:
            ip_processor.stop()


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
    ip_processor = create_intent_parser_processor(input_args)
    app = create_app()
    g.processor = ip_processor
    app.run(host=input_args.bind_host, port=input_args.bind_port)

if __name__ == "__main__":
    main()
