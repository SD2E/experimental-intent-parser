from transcriptic import Connection
import logging
import time 
import threading

class StrateosAccessor(object):
    """
    Retrieve protocols from Strateos
    """
    SYNC_PERIOD_SECS = 60*10
    logger = logging.getLogger('intent_parser_sbh')
    
    def __init__(self, credential_path=None):
        if credential_path:
            self.strateos_api = Connection.from_file(credential_path)
        else:
            self.strateos_api = Connection.from_default_config()

        self.protocol_lock = threading.Lock()
        self.protocols = {}
        self._protocol_thread = threading.Thread(target=self._periodically_fetch_protocols)
        
    def start_synchronize_protocols(self):
        self._fetch_protocols()
        self._protocol_thread.start()
             
    def stop_synchronizing_protocols(self):
        self._protocol_thread.join() 
    
    def _periodically_fetch_protocols(self):
        while True:
            time.sleep(self.SYNC_PERIOD_SECS)
            self._fetch_protocols() 

    def _fetch_protocols(self):
        self.logger.info('Fetching strateos')
        protocol_list = self.strateos_api.get_protocols()

        self.protocol_lock.acquire()
        for protocol in protocol_list:
            self.protocols[protocol['name']] = protocol
        self.protocol_lock.release()
        
    def get_protocol(self, protocol):
        """
        Get default parameter values for a given protocol.
        
        Args:
            protocol: name of protocol
            
        Return: 
            A dictionary. The key represent a parameter.
                The value represents a parameter's default value.
        
        Raises:
            An Exception to indicate if a given protocol does not exist when calling the Strateos API.
        """
        
        self.protocol_lock.acquire()
        if protocol not in self.protocols:
            raise Exception('Unable to get %s from Strateos' % protocol)
        selected_protocol = self.protocols[protocol]['inputs']
        self.protocol_lock.release()
        return self._get_protocol_default_values(selected_protocol)
    
    def _get_protocol_default_values(self, protocol):
        result = {}
        for key,value in protocol.items():
            if 'inputs' not in value:
                continue
            for subkey, subvalue in value['inputs'].items():
                strateos_key = '.'.join([key, subkey])
                result[strateos_key] = str(subvalue['default']) if 'default' in subvalue else ''

        return result
    