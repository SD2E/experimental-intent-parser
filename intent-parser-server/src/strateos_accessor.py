from transcriptic import Connection

class StrateosAccessor(object):
    '''
    Retrieve protocols from Strateos
    '''

    def __init__(self):
        self.strateos_api = Connection.from_file("~/.transcriptic")
        
    def get_protocol(self, protocol):
        """
        Return a dictionary of protocol default values for a given protocol.
        
        Args:
            protocol: name of protocol
            
        Return: 
            A dictionary. The key represent the protocol input. 
                The value represents the input's default value.
        
        Raises:
            An Exception to indicate if the given protocol does not exist when calling the Strateos API.
        """
        protocol_list = self.strateos_api.get_protocols()
        matched_protocols = [p for p in protocol_list if p['name'] == protocol]
        
        protocol = matched_protocols[0]['inputs']
        if protocol is None:
            raise Exception('Unable to get %s from Strateos' % protocol)
        
        return self._get_protocol_default_values(protocol)
    
    def _get_protocol_default_values(self, protocol):
        result = {}
        for key,value in protocol.items():
            if 'inputs' not in value:
                continue
            for subkey, subvalue in value['inputs'].items():
                strateos_key = '.'.join([key, subkey])
                result[strateos_key] = str(subvalue['default']) if 'default' in subvalue else ''

        return result
    