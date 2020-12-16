from intent_parser.server.intent_parser_server import app, IntentParserServer
import os
import logging.config
import os

logger = logging.getLogger(__name__)

def _setup_logging():
    logging.basicConfig(level=logging.INFO,
                        format="[%(levelname)-8s] %(asctime)-24s %(filename)-23s line:%(lineno)-4s  %(message)s")

    logger.addHandler(logging.FileHandler('intent_parser_server.log'))

# Switch flask to production mode using WSGI
def run():
    app.config['DEBUG'] = False
    _setup_logging()
    intent_parser_server = IntentParserServer(os.environ.get("SBH_USERNAME"),
                                             os.environ.get("SBH_PASSWORD"),
                                             os.environ.get("AUTHN"),
                                             '')
    intent_parser_server.initialize()
    return app

my_app = run()