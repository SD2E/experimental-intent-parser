from datetime import datetime
from http import HTTPStatus
from intent_parser.accessor.sbh_accessor import SBHAccessor
from intent_parser.intent_parser_exceptions import DictionaryMaintainerException, IntentParserException
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.utils.intent_parser_utils as ip_utils
import logging
import os
import re
import sbol2 as sbol

class IntentParserSBH(object):
    """
    An accessor to a SynBioHub instance for Intent Parser
    """
    
    _LOGGER = logging.getLogger('intent_parser_sbh')
    _CREDENTIAL_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                    'intent_parser_api_keys.json')

    def __init__(self, sbh_username, sbh_password, item_map_cache=True):
        self.sbh_url = intent_parser_constants.SYNBIOHUB_DEPLOYED_DATABASE_URL
        self._is_item_map_cache = item_map_cache
        self._sbh_username = sbh_username
        self._sbh_password = sbh_password
        self._sbol_dictionary = None

        self.sbh = None
        self.sbh_collection = intent_parser_constants.SYBIOHUB_COLLECTION_NAME_DESIGN
        self.sbh_uri_prefix = intent_parser_constants.SYNBIOHUB_DESIGN_COLLECTION_PREFIX
        self.sbh_collection_uri = intent_parser_constants.SYNBIOHUB_DESIGN_COLLECTION_URI
        self.sbh_collection_user = intent_parser_constants.SYNBIOHUB_DESIGN_COLLECTION_USER

    def initialize_sbh(self):
        if self.sbh is None:
            self.sbh = SBHAccessor(self.sbh_url)

        self.sbh.login(self._sbh_username,
                       self._sbh_password)

        self._LOGGER.info('Logged into {}'.format(self.sbh_url))

    def set_sbol_dictionary(self, sbol_dictionary):
        self._sbol_dictionary = sbol_dictionary

    def stop(self):
        if self.sbh is not None:
            self.sbh.stop()

    def _get_or_create_display_id(self, item_name, item_display_id):
        if len(item_display_id) == 0:
            return self.generate_display_id(item_name)

        display_id = self.generate_display_id(item_display_id)
        if display_id != item_display_id:
            raise IntentParserException('Illegal display_id')
        return display_id

    def get_item_type_mapping(self):
        sbol_type_map = {}
        for sbol_type_key in intent_parser_constants.ITEM_TYPES.keys():
            for sbol_value in intent_parser_constants.ITEM_TYPES[sbol_type_key].values():
                if sbol_value:
                    sbol_type_map.update(intent_parser_constants.ITEM_TYPES[sbol_type_key])
        return sbol_type_map

    def get_or_create_new_item_definition_uri(self, item_type, item_definition_uri, sbol_type_map):
        targeted_item_definition_uri = item_definition_uri
        # Check for item type not supported in sbol and assign them an appropriate definition uri
        if item_type == 'CHEBI':
            if len(item_definition_uri) == 0:
                targeted_item_definition_uri = sbol_type_map[item_type]
            else:
                if not item_definition_uri.startswith('http://identifiers.org/chebi/CHEBI'):
                    targeted_item_definition_uri = 'http://identifiers.org/chebi/CHEBI:' + item_definition_uri
        return targeted_item_definition_uri

    def create_synbiohub_entry(self,
                               sbol_type,
                               sbol_type_map,
                               display_id,
                               item_type,
                               item_name,
                               item_definition_uri,
                               item_lab_ids,
                               item_lab_id_tag):

        document = sbol.Document()
        document.addNamespace('http://sd2e.org#', 'sd2')
        document.addNamespace('http://purl.org/dc/terms/', 'dcterms')
        document.addNamespace('http://www.w3.org/ns/prov#', 'prov')
        document.displayId = 'foo'
        document.version = '1'

        if sbol_type == 'component':
            if item_type == 'CHEBI':
                item_sbol_type = item_definition_uri
            else:
                item_sbol_type = sbol_type_map[item_type]

            component = sbol.ComponentDefinition(display_id, item_sbol_type)
            sbol.TextProperty(component, 'http://sd2e.org#stub_object', '0', '1', 'true')
            self.set_item_properties(component,
                                     item_type,
                                     item_name,
                                     item_definition_uri,
                                     item_lab_ids,
                                     item_lab_id_tag)
            document.addComponentDefinition(component)
        elif sbol_type == 'module':
            module = sbol.ModuleDefinition(display_id)
            sbol.TextProperty(module, 'http://sd2e.org#stub_object', '0', '1', 'true')

            module.roles = sbol_type_map[item_type]
            self.set_item_properties(module,
                                     item_type,
                                     item_name,
                                     item_definition_uri,
                                     item_lab_ids,
                                     item_lab_id_tag)
            document.addModuleDefinition(module)
        elif sbol_type == 'external':
            top_level = sbol.TopLevel('http://sd2e.org/types/#attribute', display_id)
            self.set_item_properties(top_level,
                                     item_type,
                                     item_name,
                                     item_definition_uri,
                                     item_lab_ids,
                                     item_lab_id_tag)
            document.addTopLevel(top_level)
        elif sbol_type == 'collection':
            collection = sbol.Collection(display_id)
            self.set_item_properties(collection,
                                     item_type,
                                     item_name,
                                     item_definition_uri,
                                     item_lab_ids,
                                     item_lab_id_tag)
            document.addCollection(collection)
        else:
            raise IntentParserException('Failed to create a SynBioHub entry: %s as a supported sbol type in Intent Parser' % sbol_type)

        return document

    def _get_sbol_type_from_item_type(self, item_type):
        sbol_type = None
        for key, value_dict in intent_parser_constants.ITEM_TYPES.items():
            for value_type, value_uri in value_dict.items():
                if item_type == value_type:
                    sbol_type = key

        if sbol_type is None:
            err = '%s does not match one of the following sbol types: \n %s' % (
                item_type, ' ,'.join((map(str, intent_parser_constants.ITEM_TYPES.keys()))))
            raise IntentParserException(err)
        return sbol_type


    def create_sbh_stub(self, item_type, item_name, item_definition_uri, item_display_id, item_lab_ids, item_lab_id_tag):
        sbol_type_map = self.get_item_type_mapping()
        sbol_type = self._get_sbol_type_from_item_type(item_type)
        new_item_definition_uri = self.get_or_create_new_item_definition_uri(item_type,
                                                                             item_definition_uri,
                                                                             sbol_type_map)
        display_id = self._get_or_create_display_id(item_name, item_display_id)
        sbh_document = self.create_synbiohub_entry(sbol_type,
                                                   sbol_type_map,
                                                   display_id,
                                                   item_type,
                                                   item_name,
                                                   new_item_definition_uri,
                                                   item_lab_ids,
                                                   item_lab_id_tag)

        # Derive document URL
        document_url = self.sbh_uri_prefix + display_id + '/1'
        if self.sbh.exists(sbh_document, document_url):
            message = '%s already exists in SynBioHub' % document_url
            raise IntentParserException(message)
        sbh_merge_collection_flag = 2
        self.sbh.submit(sbh_document, self.sbh_collection_uri, sbh_merge_collection_flag)
        self.create_dictionary_entry(item_type,
                                     item_name,
                                     item_lab_ids,
                                     item_lab_id_tag,
                                     document_url,
                                     new_item_definition_uri)
        return document_url

    def get_sbh_collection_user(self):
        return self.sbh_collection_user
    
    def get_sbh_link_hosts(self):
        return [intent_parser_constants.SYNBIOHUB_STAGING_DATABASE,
                intent_parser_constants.SYNBIOHUB_DEPLOYED_DATABASE]
    
    def get_sbh_url(self):
        return self.sbh_url
    
    def set_item_properties(self, entity, item_type, item_name, item_definition_uri, item_lab_ids, lab_id_select):
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
                    item_definition_uri = 'http://identifiers.org/chebi/CHEBI:' + item_definition_uri
            else:
                sbol.URIProperty(entity, 'http://www.w3.org/ns/prov#wasDerivedFrom',
                                 '0', '1', item_definition_uri)

        if len(item_lab_ids) > 0:
            lab_id_tag = lab_id_select.replace(' ', '_')
            tp = None
            for item_lab_id in item_lab_ids.split(','):
                if tp is None:
                    tp = sbol.TextProperty(entity, 'http://sd2e.org#' + lab_id_tag, '0', '1',
                                           item_lab_id)
                else:
                    tp.add(item_lab_id)

    def query(self, query):
        response = self.sbh.sparqlQuery(query)
        if response.status_code != HTTPStatus.OK:
            raise IntentParserException('SBH response failed: %s' % str(response.status_code))
        return response.json()

    def query_experiments(self, target_collection):
        """
        Search the target collection and return references to all Experiment objects
    
        Parameters
        ----------
        target_collection : str
            A URI for a target collection
        """
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
        """ % target_collection
        response = self.sbh.sparqlQuery(query).json()
        experiments = []
        for m in response['results']['bindings']:
            uri = m['entity']['value']
            timestamp = m['timestamp']['value']
            title = m['title']['value']
            experiments.append({'uri': uri,
                                'timestamp': timestamp,
                                'title': title})

        return experiments
    
    def query_experiment_request(self, experiment_uri):
        """
        Return a URL to the experiment request form on Google Docs that initiated the Experiment

        Parameters
        ----------
        experiment_uri : str
            A URI for an Experiment object
        """
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX sbol: <http://sbols.org/v2#>
        PREFIX sd2: <http://sd2e.org#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT DISTINCT ?request_url WHERE {
                <%s> sd2:experimentReferenceURL ?request_url .
        }
        """ % experiment_uri
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
        experiment_uri : str
            A URI for an Experiment object
        """
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX sbol: <http://sbols.org/v2#>
        PREFIX sd2: <http://sd2e.org#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT DISTINCT ?source WHERE {
                <%s> prov:wasDerivedFrom ?source .
        }
        """ % experiment_uri
        response = self.sbh.sparqlQuery(query).json()
        source = [m['source']['value'] for m in response['results']['bindings']]
        return source

    def generate_display_id(self, name):
        display_id_first_char = '[a-zA-Z_]'
        display_id_later_char = '[a-zA-Z0-9_]'

        sanitized = ''
        for i in range(len(name)):
            character = name[i]
            if i == 0:
                if re.match(display_id_first_char, character):
                    sanitized += character
                else:
                    # avoid starting with a number
                    sanitized += '_'
                    if re.match(display_id_later_char, character):
                        sanitized += character
                    else:
                        sanitized += '0x{:x}'.format(ord(character))
            else:
                if re.match(display_id_later_char, character):
                    sanitized += character
                else:
                    sanitized += '0x{:x}'.format(ord(character))

        return sanitized

    def create_dictionary_entry(self,
                                item_type,
                                item_name,
                                item_lab_ids,
                                item_lab_id_tag,
                                document_url,
                                item_definition_uri):
        item_uri = document_url
        tab_name = self._sbol_dictionary.get_tab_name_from_item_type(item_type)
        tab_data = self._sbol_dictionary.get_row_data(tab=tab_name)

        # Get common names
        item_map = {}
        for row_data in tab_data:
            common_name = row_data['Common Name']
            if common_name is None or len(common_name) == 0:
                continue
            item_map[common_name] = row_data

        if item_name in item_map:
            raise DictionaryMaintainerException('"' + item_name + '" already exists in dictionary spreadsheet')

        dictionary_entry = {'tab': tab_name,
                            'row': len(tab_data) + 3,
                            'Common Name': item_name,
                            'Type': item_type}
        if tab_name == 'Reagent':
            dictionary_entry['Definition URI / CHEBI ID'] = item_definition_uri
        else:
            dictionary_entry['Definition URI'] = item_definition_uri

        if item_type != 'Attribute':
            dictionary_entry['Stub Object?'] = 'YES'

        dictionary_entry[item_lab_id_tag] = item_lab_ids
        dictionary_entry['SynBioHub URI'] = item_uri

        self._sbol_dictionary.set_row_data(dictionary_entry)

