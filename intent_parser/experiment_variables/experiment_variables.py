class ExperimentVariable(object):

    def __init__(self, sbh_uri, lab_id, common_name, lab_names=[]):
        self._sbh_uri = sbh_uri
        self._lab_id = lab_id
        self._common_name = common_name
        self._lab_names = lab_names

    def get_common_name(self):
        return self._common_name

    def get_lab_id(self):
        return self._lab_id

    def get_lab_names(self):
        return self._lab_names

    def get_sbh_uri(self):
        return self._sbh_uri

    def has_lab_name(self, lab_name):
        return lab_name in self._lab_names


