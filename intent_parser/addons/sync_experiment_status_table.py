from intent_parser.accessor.google_accessor import GoogleAccessor
from intent_parser.accessor.mongo_db_accessor import MongoDBAccessor
from datetime import timedelta
import argparse
import json
import logging
import os.path
import time
import traceback

logger = logging.getLogger('experiment_status_script')
SYNC_PERIOD = timedelta(minutes=10)

def perform_automatic_run(documents, mongodb_accessor):
    while len(documents) > 0:
        doc = documents.pop(0)
        doc_id = doc
        logger.info('Processing doc: ' + doc_id)
        # TODO: fetch information from mongodb
        db_information = mongodb_accessor.get_experiment_status(doc_id)
        # TODO: fetch table from document
        # TODO: diff content from mongodb and document
        # TODO: if document does not have experiment table(s), create them
        # TODO: if content not equal, update document table. Else don't update table

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
        logging.basicConfig(level=default_level, format="[%(levelname)-8s] %(asctime)-24s %(filename)-23s line:%(lineno)-4s  %(message)s")

    hdlr = logging.FileHandler('ip_addon_script.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)

    logger.setLevel(logging.INFO)

    logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.CRITICAL)
    logging.getLogger("googleapiclient.discovery").setLevel(logging.CRITICAL)

def main():
    parser = argparse.ArgumentParser(description='Script to synchronize experiment status tables across Experiment Intent Google Docs.')
    parser.add_argument('-f', '--folder_id', nargs='?',
                        required=True, help='Google Drive folder id.')

    parser.add_argument('-m', '--mongodb_credential', nargs='?',
                        required=True, help='MongoDB credential.')

    input_args = parser.parse_args()
    setup_logging()

    try:
        logger.info('Running synchronizing experiment status script for release')
        drive_access = GoogleAccessor().get_google_drive_accessor()
        list_of_docs = drive_access.get_all_docs(input_args.folder_id)
        mongodb_accessor = MongoDBAccessor(input_args.mongodb_credential)
        while True:
            perform_automatic_run(list_of_docs, mongodb_accessor)
            time.sleep(SYNC_PERIOD.total_seconds())

    except (KeyboardInterrupt, SystemExit, Exception) as ex:
        logger.info('Script stopped!')
        logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
        return

if __name__ == '__main__':
    main()