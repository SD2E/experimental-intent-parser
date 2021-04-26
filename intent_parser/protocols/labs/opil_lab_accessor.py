
class OpilLabAccessors(object):
    """
    Define functions for getting an experimental protocol interface in opil.
    """
    def __init__(self):
        pass

    def get_experiment_id_from_protocol(self, protocol_name):
        raise NotImplementedError('not implemented')

    def get_experimental_protocol(self, experimental_request_name):
        raise NotImplementedError('not implemented')

    def get_experimental_protocol_names(self):
        raise NotImplementedError('not implemented')
