import intent_parser.constants.intent_parser_constants as ip_constants
import uuid

"""
Generate unique ID
"""
class IdProvider(object):

    def __init__(self):
        pass

    def get_unique_lab_id(self, lab_namespace):
        return lab_namespace + str(uuid.uuid4().hex)

    def get_unique_sd2_id(self):
        return ip_constants.SD2E_NAMESPACE + 'ip' + str(uuid.uuid4().hex)
