from intent_parser.accessor.mongo_db_accessor import TA4DBAccessor
from datetime import timedelta
from requests.exceptions import HTTPError
import intent_parser.constants.sd2_datacatalog_constants as dc_constants
import argparse
import json
import logging
import os.path
import requests
import time
import traceback

logger = logging.getLogger('experiment_status_script')
SYNC_PERIOD = timedelta(minutes=10)

def perform_automatic_run(documents):
    try:
        documents = _get_documents_from_ip()
        while len(documents) > 0:
            document_id = documents.pop(0)
            _process_document(document_id)

    except HTTPError as http_err:
        logger.warning(f'HTTP error occurred: {http_err}')

def _process_document(document_id):

    mongodb_accessor = TA4DBAccessor()
    try:
        experiment_statuses = _get_experiment_status_tables(document_id)
        lab_name = experiment_statuses[dc_constants.LAB]
        exp_id_to_table_id = experiment_statuses[dc_constants.EXPERIMENT_ID]
        table_id_to_statuses = experiment_statuses[dc_constants.STATUS_ELEMENT]
        db_exp_id_to_statuses = mongodb_accessor.get_experiment_status(document_id, lab_name)
        for db_exp_id, db_status_table in db_exp_id_to_statuses:
            if db_exp_id in exp_id_to_table_id:
                table_id = set(exp_id_to_table_id[db_exp_id])
                if db_status_table != table_id_to_statuses(table_id):
                    logger.warning('Updating experiment status for document id: %s' % document_id)
                    execute_request('update_experiment_status?%s' % document_id)
                else:
                    logger.warning('Experiment Status are up to date for document ID: %s' % document_id)

    except HTTPError as http_err:
        logger.warning(f'HTTP error occurred: {http_err}')

def _get_documents_from_ip():
    response = execute_request('experiment_request_documents')
    return response['docId']

def _get_experiment_status_tables(document_id):
    experiment_statuses = execute_request('experiment_status?%s' % document_id)

def execute_request(request_type):
    request_url = 'http://intentparser.sd2e.org/%s' % (request_type)
    response = requests.get(request_url)
    response.raise_for_status()
    return response

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
    parser = argparse.ArgumentParser(description='Script to synchronize experiment status tables across Experiment Docs.')
    parser.add_argument('-f', '--folder_id', nargs='?',
                        required=True, help='Google Drive folder id.')

    input_args = parser.parse_args()
    setup_logging()

    try:
        logger.info('Running synchronizing experiment status script for release')
        while True:
            perform_automatic_run()
            time.sleep(SYNC_PERIOD.total_seconds())
            logger.info('Scheduling next run.')

    except (KeyboardInterrupt, SystemExit, Exception) as ex:
        logger.info('Script stopped!')
        logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
        return

if __name__ == '__main__':
    main()