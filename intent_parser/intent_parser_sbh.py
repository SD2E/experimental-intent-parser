from http import HTTPStatus
from intent_parser.accessor.sbh_accessor import SBHAccessor
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.utils.intent_parser_view as intent_parser_view
from datetime import datetime
import logging
import re
import sbol2 as sbol
import traceback

class IntentParserSBH(object):
    """
    An accessor to a SynBioHub instance for Intent Parser
    """
    
    logger = logging.getLogger('intent_parser_sbh')

    def __init__(self, 
                 sbh_collection_uri,
                 spreadsheet_id,
                 sbh_username, 
                 sbh_password,
                 sbh_spoofing_prefix=None,
                 item_map_cache=True,
                 sbh_link_hosts=['hub-staging.sd2e.org',
                                 'hub.sd2e.org']):
        self.sbh_collection_uri = sbh_collection_uri
        self.sbh_spoofing_prefix = sbh_spoofing_prefix
        self.spreadsheet_id = spreadsheet_id
        self.item_map_cache = item_map_cache
        self.sbh_username = sbh_username
        self.sbh_password = sbh_password
        self.sbh_link_hosts = sbh_link_hosts
        self.sbh = None
    
    def initialize_sbh(self):
        """
        Initialize the connection to SynbioHub.
        """

        if self.sbh_collection_uri[:8] == 'https://':
            sbh_url_protocol = 'https://'
            sbh_collection_path = self.sbh_collection_uri[8:]
        elif self.sbh_collection_uri[:7] == 'http://':
            sbh_url_protocol = 'http://'
            sbh_collection_path = self.sbh_collection_uri[7:]
        else:
            raise Exception('Invalid collection url: ' + self.sbh_collection_uri)

        sbh_collection_path_parts = sbh_collection_path.split('/')
        if len(sbh_collection_path_parts) != 6:
            raise Exception('Invalid collection url: ' + self.sbh_collection_uri)

        sbh_collection = sbh_collection_path_parts[3]
        sbh_collection_user = sbh_collection_path_parts[2]
        sbh_collection_version = sbh_collection_path_parts[5]
        sbh_url = sbh_url_protocol + sbh_collection_path_parts[0]

        if sbh_collection_path_parts[4] != (sbh_collection + '_collection'):
            raise Exception('Invalid collection url: ' + self.sbh_collection_uri)

        self.sbh = SBHAccessor(sbh_url=sbh_url)
        self.sbh_collection = sbh_collection
        self.sbh_collection_user = sbh_collection_user
        self.sbh_spoofing_prefix = self.sbh_spoofing_prefix
        self.sbh_url = sbh_url
        self.sbh_link_hosts = self.sbh_link_hosts

        if self.sbh_spoofing_prefix is not None:
            self.sbh.spoof(self.sbh_spoofing_prefix)
            self.sbh_collection_uri = self.sbh_spoofing_prefix \
                + '/user/' + sbh_collection_user \
                + '/' + sbh_collection + '/' \
                + sbh_collection + '_collection/' \
                + sbh_collection_version
        else:
            self.sbh_collection_uri = sbh_url + '/'
            self.sbh_collection_uri = sbh_url \
                + '/user/' + sbh_collection_user \
                + '/' + sbh_collection + '/' \
                + sbh_collection + '_collection/' \
                + sbh_collection_version

        self.sbh_uri_prefix = sbh_url \
            + '/user/' + sbh_collection_user \
            + '/' + sbh_collection + '/'

        if self.sbh is not None:
            self.sbh.login(self.sbh_username, self.sbh_password)
            self.logger.info('Logged into {}'.format(sbh_url))
            
    def stop(self):
        if self.sbh is not None:
            self.sbh.stop()
    
    def create_sbh_stub(self, data):
        # Extract some fields from the form
        try:
            item_type = data['itemType']
            item_name = data['commonName']
            item_definition_uri = data['definitionURI']
            item_display_id = data['displayId']

        except Exception as e:
            return intent_parser_view.operation_failed('Form submission missing key: ' + str(e))

        # Make sure Common Name was specified
        if len(item_name) == 0:
            return intent_parser_view.operation_failed('Common Name must be specified')

        # Sanitize the display id
        if len(item_display_id) > 0:
            display_id = self.sanitize_name_to_display_id(item_display_id)
            if display_id != item_display_id:
                return intent_parser_view.operation_failed('Illegal display_id')
        else:
            display_id = self.sanitize_name_to_display_id(item_name)

        # Derive document URL
        document_url = self.sbh_uri_prefix + display_id + '/1'

        # Make sure document does not already exist
        try:
            if self.sbh.exists(document_url):
                return intent_parser_view.operation_failed('"' + display_id +
                                             '" already exists in SynBioHub')
        except:
            return intent_parser_view.operation_failed('Failed to access SynBioHub')

        # Look up sbol type uri
        sbol_type = None
        for sbol_type_key in intent_parser_constants.ITEM_TYPES:
            sbol_type_map = intent_parser_constants.ITEM_TYPES[ sbol_type_key ]
            if item_type in sbol_type_map:
                sbol_type = sbol_type_key
                break;

        # Fix CHEBI URI
        if item_type == 'CHEBI':
            if len(item_definition_uri) == 0:
                item_definition_uri = sbol_type_map[ item_type ]
            else:
                if not item_definition_uri.startswith('http://identifiers.org/chebi/CHEBI'):
                    item_definition_uri = 'http://identifiers.org/chebi/CHEBI:' + \
                        item_definition_uri

        # Create a dictionary entry for the item
        try:
            self.create_dictionary_entry(data, document_url, item_definition_uri)

        except Exception as e:
            return intent_parser_view.operation_failed(str(e))

        # Create an entry in SynBioHub
        try:
            document = sbol.Document()
            document.addNamespace('http://sd2e.org#', 'sd2')
            document.addNamespace('http://purl.org/dc/terms/', 'dcterms')
            document.addNamespace('http://www.w3.org/ns/prov#', 'prov')

            if sbol_type == 'component':
                if item_type == 'CHEBI':
                    item_sbol_type = item_definition_uri
                else:
                    item_sbol_type = sbol_type_map[ item_type ]

                component = sbol.ComponentDefinition(display_id, item_sbol_type)

                sbol.TextProperty(component, 'http://sd2e.org#stub_object', '0', '1', 'true')
                self.set_item_properties(component, data)

                document.addComponentDefinition(component)

            elif sbol_type == 'module':
                module = sbol.ModuleDefinition(display_id)
                sbol.TextProperty(module, 'http://sd2e.org#stub_object', '0', '1', 'true')

                module.roles = sbol_type_map[ item_type ]
                self.set_item_properties(module, data)

                document.addModuleDefinition(module)

            elif sbol_type == 'external':
                top_level = sbol.TopLevel('http://sd2e.org/types/#attribute', display_id)
                self.set_item_properties(top_level, data)

                document.addTopLevel(top_level)

            elif sbol_type == 'collection':
                collection = sbol.Collection(display_id)
                self.set_item_properties(collection, data)
                document.addCollection(collection)

            else:
                raise Exception()

            self.sbh.submit(document, self.sbh_collection_uri, 3)

            paragraph_index = data['selectionStartParagraph']
            offset = data['selectionStartOffset']
            end_offset = data['selectionEndOffset']

            action = intent_parser_view.link_text(paragraph_index, offset,
                                    end_offset, document_url)

        except Exception as e:
            self.logger.error(''.join(traceback.format_exception(etype=type(e),
                                                     value=e,
                                                     tb=e.__traceback__)))

            message = 'Failed to add "' + display_id + '" to SynBioHub'
            return intent_parser_view.operation_failed(message)

        return_info = {'actions': [action],
                       'results': {'operationSucceeded': True}
                      }

        return return_info  
    
    def get_sbh_collection_user(self):
        return self.sbh_collection_user
    
    def get_sbh_link_host(self):
        return self.sbh_link_hosts 
    
    def get_sbh_spoofing_prefix(self):
        return self.sbh_spoofing_prefix
    
    def get_sbh_url(self):
        return self.sbh_url
    
    def set_item_properties(self, entity, data):
        item_type = data['itemType']
        item_name = data['commonName']
        item_definition_uri = data['definitionURI']
        item_lab_ids = data['labId']

        sbol.TextProperty(entity, 'http://purl.org/dc/terms/title', '0', '1',
                          item_name)

        time_stamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S-00')
        sbol.TextProperty(entity, 'http://purl.org/dc/terms/created', '0', '1',
                          time_stamp)
        sbol.TextProperty(entity, 'http://purl.org/dc/terms/modified', '0', '1',
                          time_stamp)

        if item_type in intent_parser_constants.ITEM_TYPES['collection']:
            return

        if len(item_definition_uri) > 0:
            if item_type == 'CHEBI':
                if not item_definition_uri.startswith('http://identifiers.org/chebi/CHEBI'):
                    item_definition_uri = 'http://identifiers.org/chebi/CHEBI:' + \
                        item_definition_uri
            else:
                sbol.URIProperty(entity, 'http://www.w3.org/ns/prov#wasDerivedFrom',
                                 '0', '1', item_definition_uri)

        if len(item_lab_ids) > 0:
            lab_id_tag = data['labIdSelect'].replace(' ', '_')
            tp = None
            for item_lab_id in item_lab_ids.split(','):
                if tp is None:
                    tp = sbol.TextProperty(entity, 'http://sd2e.org#' + lab_id_tag, '0', '1',
                                           item_lab_id)
                else:
                    tp.add(item_lab_id)
     
    def query_experiments(self, target_collection):
        """
        Search the target collection and return references to all Experiment objects
    
        Parameters
        ----------
        synbiohub : SynBioHubQuery
            An instance of a SynBioHubQuery SPARQL wrapper from synbiohub_adapter
        target_collection : str
            A URI for a target collection
        """
    
        # Correct the target collection URI in case the user specifies the wrong synbiohub namespace
        # (a common mistake that can be hard to debug)
        if self.sbh_spoofing_prefix is not None:
            target_collection = target_collection.replace(self.sbh_url, self.sbh_spoofing_prefix)
    
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX sbol: <http://sbols.org/v2#>
        PREFIX sd2: <http://sd2e.org#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT DISTINCT ?entity ?timestamp ?title WHERE {
                <%s> sbol:member ?entity .
                ?entity rdf:type sbol:Experiment .
                ?entity dcterms:created ?timestamp .
                ?entity dcterms:title ?title
        }
        """ %(target_collection)
        response = self.sbh.sparqlQuery(query)
        experiments = []
        if response.status_code() != HTTPStatus.OK:
            self.logger.warning('Unable to query from SynBioHub. HTTP %s' % response.status_code)
            return experiments
        sbh_query = response.json()
        for m in sbh_query['results']['bindings']:
            uri = m['entity']['value']
            timestamp = m['timestamp']['value']
            title = m['title']['value']
            
            if self.sbh_spoofing_prefix is not None: # We need to re-spoof the URL
                uri = uri.replace(self.sbh_spoofing_prefix, self.sbh_url)
            
            experiments.append({'uri': uri, 'timestamp': timestamp, 'title': title})
        
        return experiments
    
    def query_experiment_request(self, experiment_uri):
        """
        Return a URL to the experiment request form on Google Docs that initiated the Experiment

        Parameters
        ----------
        synbiohub : SynBioHubQuery
            An instance of a SynBioHubQuery SPARQL wrapper from synbiohub_adapter
        experiment_uri : str
            A URI for an Experiment object
        """

        # Correct the experiment_uri in case the user specifies the wrong synbiohub namespace
        # (a common mistake that can be hard to debug)
        if self.sbh_spoofing_prefix is not None:
            experiment_uri = experiment_uri.replace(self.sbh_url, self.sbh_spoofing_prefix)

        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX sbol: <http://sbols.org/v2#>
        PREFIX sd2: <http://sd2e.org#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT DISTINCT ?request_url WHERE {
                <%s> sd2:experimentReferenceURL ?request_url .
        }
        """ %(experiment_uri)
        response = self.sbh.sparqlQuery(query).json()
        request_url = [m['request_url']['value'] for m in response['results']['bindings']]
        
        if request_url:
            return request_url[0]
        else:
            return "NOT FOUND"

    def query_experiment_source(self, experiment_uri):
        """
        Return a reference to a samples.json file on Agave file system that generated the Experiment

        Parameters
        ----------
        synbiohub : SynBioHubQuery
            An instance of a SynBioHubQuery SPARQL wrapper from synbiohub_adapter
        experiment_uri : str
            A URI for an Experiment object
        """

        # Correct the experiment_uri in case the user specifies the wrong synbiohub namespace
        # (a common mistake that can be hard to debug)
        if self.sbh_spoofing_prefix is not None:
            experiment_uri = experiment_uri.replace(self.sbh_url, self.sbh_spoofing_prefix)

        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX sbol: <http://sbols.org/v2#>
        PREFIX sd2: <http://sd2e.org#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT DISTINCT ?source WHERE {
                <%s> prov:wasDerivedFrom ?source .
        }
        """ %(experiment_uri)
        response = self.sbh.sparqlQuery(query).json()
        source = [ m['source']['value'] for m in response['results']['bindings']]
        return source

    def sanitize_name_to_display_id(self, name):
        displayIDfirstChar = '[a-zA-Z_]'
        displayIDlaterChar = '[a-zA-Z0-9_]'

        sanitized = ''
        for i in range(len(name)):
            character = name[i]
            if i==0:
                if re.match(displayIDfirstChar, character):
                    sanitized += character
                else:
                    sanitized += '_' # avoid starting with a number
                    if re.match(displayIDlaterChar, character):
                        sanitized += character
                    else:
                        sanitized += '0x{:x}'.format(ord(character))
            else:
                if re.match(displayIDlaterChar, character):
                    sanitized += character;
                else:
                    sanitized += '0x{:x}'.format(ord(character))

        return sanitized
