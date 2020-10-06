from datetime import timedelta
from intent_parser.intent_parser_exceptions import IntentParserException
from transcriptic import Connection
import logging
import time 
import threading

class StrateosAccessor(object):
    """
    Retrieve protocols from Strateos
    """
    SYNC_PERIOD = timedelta(minutes=10)
    logger = logging.getLogger('intent_parser_strateos_accessor')
    
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
            time.sleep(self.SYNC_PERIOD.total_seconds())
            self._fetch_protocols() 

    def _fetch_protocols(self):
        self.logger.info('Fetching strateos')
        protocol_list = self.strateos_api.get_protocols()

        self.protocol_lock.acquire()
        for protocol in protocol_list:
            self.protocols[protocol['name']] = self._parse_protocol(protocol['inputs'])
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
        selected_protocol = self.protocols[protocol]
        self.protocol_lock.release()
        return selected_protocol
    
    def _parse_protocol(self, protocol):
        queue = []
        parameters = {}
        for key, value in protocol.items():
            queue.append(([key], value))

        while len(queue) > 0:
            names, protocol_field = queue.pop(0)
            id = '.'.join(names)

            if 'inputs' in protocol_field:
                for key, value in protocol_field['inputs'].items():
                    queue.append((names + [key], value))
            else:
                parameter_field = ParameterField()
                if 'default_field' in protocol_field:
                    parameter_field.set_default_value(protocol_field['default_field'])
                if 'required' in protocol_field:
                    parameter_field.set_required(protocol_field['required'])
                if 'options' in protocol_field:
                    for option in protocol_field['options']:
                        if 'name' in option and 'value' in option:
                            parameter_field.add_option(option['name'], option['value'])
                parameters[id] = parameter_field

        return parameters

class ParameterField(object):

    def __init__(self, default_value=None, required=False):
        self._default_value = default_value
        self._required = required
        self._options = []

    def add_option(self, name, value):
        option = ParameterFieldOption(name, value)
        self._options.append(option)

    def is_required(self):
        return self._required

    def set_default_value(self, value):
        if self._default_value:
            raise IntentParserException('Conflict setting %s as a default value when it is currently set to %s' % (value, self._default_value))
        self._default_value = value

    def set_required(self, value: bool):
        self._required = value


class ParameterFieldOption(object):

    def __init__(self, name, value):
        self._name = name
        self._value = value
