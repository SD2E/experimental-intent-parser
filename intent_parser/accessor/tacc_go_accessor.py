import json
import requests

class TACCGoAccessor(object):

    def __init__(self, nonce_credential):
        self.nonce = nonce_credential

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


