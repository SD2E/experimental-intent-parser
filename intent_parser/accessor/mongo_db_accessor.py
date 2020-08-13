from intent_parser.table.experiment_status_table import ExperimentStatusTableParser
import intent_parser.utils.intent_parser_utils as ip_util
import intent_parser.constants.intent_parser_constants as ip_constants
import intent_parser.constants.ta4_db_constants as ta4_constants
import logging
import os.path
import pymongo

class TA4DBAccessor(object):
    """
    Retrieve job pipeline status for an experiment from TA4 MongoDB.
    """

    _LOGGER = logging.getLogger('intent_parser_mongo_db_accessor')
    _MONGODB_ACCESSOR = None

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not cls._MONGODB_ACCESSOR:
            cls._MONGODB_ACCESSOR = super(TA4DBAccessor, cls).__new__(cls, *args, **kwargs)
            cls._MONGODB_ACCESSOR._authenticate_credentials()
        return cls._MONGODB_ACCESSOR

    def _authenticate_credentials(self):
        credential_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'intent_parser_api_keys.json')
        credential = ip_util.load_json_file(credential_file)['dbURI']
        self.database = pymongo.MongoClient(credential).catalog_staging


    def get_experiment_status(self, doc_id, lab_name):
        """Retrieve of Status for an experiment.

        Args:
            doc_id: id of Google Doc.
            lab_name: name of lab
        Returns:
            A dictionary. The key represents the experiment_id. The value represents a ExperimentStatusTableParser.
        """
        experiment_ref = ip_constants.GOOGLE_DOC_URL_PREFIX + doc_id
        db_response = self.database.structured_requests.find({ta4_constants.EXPERIMENT_REFERENCE_URL: experiment_ref,
                                                              '$where': 'this.derived_from.length > 0'})
        result = {}
        status_table = ExperimentStatusTableParser()
        for status in db_response:
            if lab_name.lower() in status[ta4_constants.LAB].lower():
                for status_type, status_values in status[ta4_constants.STATUS].items():
                    status_path = status_values[ta4_constants.PATH]
                    if status_type == ta4_constants.XPLAN_REQUEST_SUBMITTED:
                        status_path = status[ta4_constants.PARENT_GIT_PATH]
                    status_table.add_status(status_type,
                                            status_values[ta4_constants.LAST_UPDATED],
                                            status_values[ta4_constants.STATE],
                                            status_path)
                result[status[ta4_constants.EXPERIMENT_ID]] = status_table
        return result
