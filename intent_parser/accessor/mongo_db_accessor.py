from datetime import timedelta
import logging
import pymongo
import time
import threading

class MongoDBAccessor(object):
    """
    Retrieve information from MongoDB
    """

    SYNC_PERIOD = timedelta(minutes=5)
    _LOGGER = logging.getLogger('intent_parser_mongo_db_accessor')

    def __init__(self, credentials):
        self.database = pymongo.MongoClient(credentials).catalog_staging

        self.mongo_db_lock = threading.Lock()
        self.mongo_db = {}
        self.mongo_db_thread = threading.Thread(target=self._periodically_fetch_mongo_db)

    def get_experiment_status(self, experiment_reference_url):
        """Retrieve a list of Status for an experiment
        """
        experiment = self.mongo_db[experiment_reference_url]
        result = []
        for status_type, status_values in experiment['status'].items():
            status = _Status(status_type,
                    status_values['last_updated'],
                    status_values['state'],
                    status_values['path'])
            result.append(status)
        return result

    def start_synchronize_mongo_db(self):
        self._fetch_mongo_db()
        self.mongo_db_thread.start()

    def stop_synchronizing_mongo_db(self):
        self.mongo_db_thread.join()

    def _periodically_fetch_mongo_db(self):
        while True:
            time.sleep(self.SYNC_PERIOD.total_seconds())
            self._fetch_mongo_db()

    def _fetch_mongo_db(self):
        self._LOGGER.info('Fetching Mongo database')
        structure_requests = self.database.structured_requests.find({'$where': 'this.derived_from.length > 0'})

        self.mongo_db_lock.acquire()
        for sr in structure_requests:
            self.mongo_db[sr['experiment_reference_url']] = sr
        self.mongo_db_lock.release()

class _Status(object):

    def __init__(self, status_type, last_updated, state, path):
        self.status_type = status_type
        self.last_updated = last_updated
        self.state = state
        self.path = path

    def status_type(self):
        """Indicate the type of status

        Returns: A string
        """
        return self.status_type

    def last_updated(self):
        """
        Returns: Datetime
        """
        return self.last_updated

    def state(self):
        """
        Returns: A boolean
        """
        return self.state

    def path(self):
        """
        Returns: A string
        """
        return self.path