from datetime import timedelta
from requests.exceptions import HTTPError
import json
import logging
import os.path
import requests
import time
import traceback

logger = logging.getLogger('experiment_status_script')
SYNC_PERIOD = timedelta(minutes=5)

def perform_automatic_run():
    try:
        documents = _get_documents_from_ip()
        while len(documents) > 0:
            document_id = documents.pop(0)
            logger.warning('Processing document id: %s' % document_id)
            _update_status(document_id)
            logger.warning('Update complete for document id: %s' % document_id)

    except HTTPError as http_err:
        logger.warning(f'HTTP error occurred: {http_err}')

def _get_documents_from_ip():
    response = execute_request('experiment_request_documents')
    doc_dict = response.json()
    return doc_dict['docId']

def _update_status(document_id):
    response = execute_request('update_experiment_status?%s' % document_id)
    content = response.json()
    for status_message in content['messages']:
        logger.warning(status_message)


def execute_request(request_type):
    request_url = 'http://intentparser2.sd2e.org/%s' % (request_type)
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

    hdlr = logging.FileHandler('experiment_status_script.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)

    logger.setLevel(logging.INFO)

def main():
    setup_logging()
    try:
        logger.info('Running synchronizing experiment status script')
        while True:
            perform_automatic_run()
            logger.info('Scheduling next run.')
            time.sleep(SYNC_PERIOD.total_seconds())

    except (KeyboardInterrupt, SystemExit, Exception) as ex:
        logger.info('Script stopped!')
        logger.info(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
        return

if __name__ == '__main__':
    main()
