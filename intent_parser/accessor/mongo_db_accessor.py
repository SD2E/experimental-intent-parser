from intent_parser.table.experiment_status_table import ExperimentStatusTable
import intent_parser.utils.intent_parser_utils as ip_util
import logging
import os.path
import pymongo

class MongoDBAccessor(object):
    """
    Retrieve information from MongoDB
    """

    _LOGGER = logging.getLogger('intent_parser_mongo_db_accessor')

    _MONGODB_ACCESSOR = None

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not cls._MONGODB_ACCESSOR:
            cls._MONGODB_ACCESSOR = super(MongoDBAccessor, cls).__new__(cls, *args, **kwargs)
            cls._MONGODB_ACCESSOR._authenticate_credentials()
        return cls._MONGODB_ACCESSOR

    def _authenticate_credentials(self):
        credential_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'intent_parser_api_keys.json')
        credential = ip_util.load_json_file(credential_file)['dbURI']
        self.database = pymongo.MongoClient(credential).catalog_staging


    def get_experiment_status(self, doc_id):
        """Retrieve a list of Status for an experiment
        """
        structure_requests = self.database.structured_requests.find({"experiment_reference_url":"https://docs.google.com/document/d/%s" % doc_id,
                                                                     "$where": "this.derived_from.length > 0"})

        status_table = ExperimentStatusTable()
        for sr in structure_requests:
            for status_type, status_values in sr['status'].items():
                status_table.add_status(status_type,
                                        status_values['last_updated'],
                                        status_values['state'],
                                        status_values['path'])
        return status_table

