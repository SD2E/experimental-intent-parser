import intent_parser.constants.tacc_constants as tacc_constants
import intent_parser.utils.intent_parser_utils as ip_util
import json
import logging
import os.path
import requests

class TACCGoAccessor(object):

    logger = logging.getLogger('intent_parser_strateos_accessor')
    _TACC_GO_ACCESSOR = None

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not cls._TACC_GO_ACCESSOR:
            cls._TACC_GO_ACCESSOR = super(TACCGoAccessor, cls).__new__(cls, *args, **kwargs)
            cls._TACC_GO_ACCESSOR._authenticate_credentials()
        return cls._TACC_GO_ACCESSOR

    def _authenticate_credentials(self):
        credential_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'intent_parser_api_keys.json')
        self._nonce = ip_util.load_json_file(credential_file)['experiment_execution_token']

    def execute_experiment(self, data):
        headers = {
            'Content-type': 'application/json',
        }
        payload = json.dumps(data)
        response = requests.post(tacc_constants.EXPERIMENT_AUTHENTICATION_URL + self._nonce,
                                 headers=headers,
                                 data=payload)
        return response

    def get_failure_experiment_result(self, execution_id: str):
        headers = {
            'Content-type': 'application/json',
        }
        response = requests.post('%s/%s/logs?x-nonce=%s' % (tacc_constants.EXPERIMENT_EXECUTION_URL, execution_id, self._nonce),
                                 headers=headers)
        response_content = response.json()
        return response_content[tacc_constants.EXPERIMENT_EXECUTION_RESULT][tacc_constants.EXPERIMENT_EXECUTION_LOGS]

    def get_status_of_experiment(self, experiment_id: str) -> str:
        response = requests.get('%s/%s?x-nonce=%s' % (tacc_constants.EXPERIMENT_EXECUTION_URL, experiment_id, self._nonce))
        response_content = response.json()
        experiment_result = response_content[tacc_constants.EXPERIMENT_EXECUTION_RESULT]
        if experiment_result[tacc_constants.EXPERIMENT_EXECUTION_EXIT_CODE] != 0:
            return self.get_failure_experiment_result()
        elif experiment_result == 'COMPLETE':
            return 'Successfully executed experiment!'
        elif experiment_result == 'SUBMITTED':
            return 'Experiment is being processed.'


