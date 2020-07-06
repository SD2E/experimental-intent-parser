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
        self.nonce = ip_util.load_json_file(credential_file)['nonce']

    def execute_experiment(self, data):
        """Send request to execute an experiment.

        Args:
            data: experiment to execute.
        Returns:
            Response message
        """
        headers = {
            'Content-type': 'application/json',
        }
        payload = json.dumps(data)
        response = requests.post(self.nonce, headers=headers, data=payload)
        response_content = response.json()
        return response_content['message']


