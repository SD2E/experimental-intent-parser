
from intent_parser.server.intent_parser_server import app, IntentParserServer
import argparse
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import json
import logging.config
import os

logger = logging.getLogger(__name__)

def cmd_parser():
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
    return input_args

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

def main():
    input_args = cmd_parser()
    _setup_logging()
    ip_server = IntentParserServer(input_args.username, input_args.password, input_args.authn, input_args.transcriptic)
    ip_server.initialize()
    ip_server.run_server(input_args.bind_host, input_args.bind_port)

if __name__ == "__main__":
    main()
