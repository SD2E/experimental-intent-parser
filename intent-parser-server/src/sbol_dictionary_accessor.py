
from google_accessor import GoogleAccessor
from intent_parser_exceptions import DictionaryMaintainerException
import constants
import logging
import os 
import intent_parser_utils
import time

class SBOLDictionaryAccessor(object):
    '''
    Provide functionalities to read and write information to the SBOL Dictionary Maintainer Google Spreadsheet.
    '''
    
    logger = logging.getLogger('intent_parser_sbol_dictionary')

    # Some lab UIDs are short but still valid.  This defines an exceptions to the length threshold.
    UID_LENGTH_EXCEPTION = ['M9', 'LB']
    
    # Determine how long a lab UID string has to be in order to be added to the item map.
    # Strings below this size are ignored.
    UID_LENGTH_THRESHOLD = 3
    

    def __init__(self, spreadsheet_id, sbh):
        self.google_accessor = GoogleAccessor.create()
        self.google_accessor.set_spreadsheet_id(spreadsheet_id)
        self.sbh = sbh
        
        curr_path = os.path.dirname(os.path.realpath(__file__))
        self.item_map_file = os.path.join(curr_path, 'item-map.json')
    
    def create_dictionary_entry(self, data, document_url, item_definition_uri):
        item_type = data['itemType']
        item_name = data['commonName']
        item_lab_ids = data['labId']
        item_lab_id_tag = data['labIdSelect']

        #sbh_uri_prefix = self.sbh_uri_prefix
        if self.sbh_spoofing_prefix is not None:
            item_uri = document_url.replace(self.sbh.get_sbh_url(),
                                            self.sbh.get_sbh_spoofing_prefix())
        else:
            item_uri = document_url
        
        type2tab = self.load_type2tab()
        tab_name = type2tab[item_type]

        try:
            tab_data = self.google_accessor.get_row_data(tab=tab_name)
        except:
            raise Exception('Failed to access dictionary spreadsheet')

        # Get common names
        item_map = {}
        for row_data in tab_data:
            common_name = row_data['Common Name']
            if common_name is None or len(common_name) == 0:
                continue
            item_map[common_name] = row_data

        if item_name in item_map:
            raise Exception('"' + item_name + '" already exists in dictionary spreadsheet')

        dictionary_entry = {}
        dictionary_entry['tab'] = tab_name
        dictionary_entry['row'] = len(tab_data) + 3
        dictionary_entry['Common Name'] = item_name
        dictionary_entry['Type'] = item_type
        if tab_name == 'Reagent':
            dictionary_entry['Definition URI / CHEBI ID'] = \
                item_definition_uri
        else:
            dictionary_entry['Definition URI'] = \
                item_definition_uri

        if item_type != 'Attribute':
            dictionary_entry['Stub Object?'] = 'YES'

        dictionary_entry[item_lab_id_tag] = item_lab_ids
        dictionary_entry['SynBioHub URI'] = item_uri

        try:
            self.google_accessor.set_row_data(dictionary_entry)
        except:
            raise Exception('Failed to add entry to the dictionary spreadsheet')
    
    def fetch_spreadsheet_data(self):
        tab_data = {}
        spreadsheet_tabs = self.google_accessor.type_tabs.keys()
        for tab in spreadsheet_tabs:
            tab_data[tab] = self.google_accessor.get_row_data(tab=tab)
            self.logger.info('Fetched data from tab ' + tab)

        return tab_data
    
    def generate_item_map(self, *, use_cache=True):
        """
        Use the SBOL Dictionary to generate a dictionary of common names referring to its SBH URI and store it into a local item-map.json file
        """
        item_map = {}
        self.logger.info('Generating item map, %d' % time.time())
        if use_cache:
            item_map = intent_parser_utils.load_json_file(self.item_map_file)
            self.logger.info('Num items in item_map: %d' % len(item_map))

        lab_uid_src_map = {}
        lab_uid_common_map = {}
        sheet_data = self.fetch_spreadsheet_data()
        for tab in sheet_data:
            for row in sheet_data[tab]:
                if not 'Common Name' in row :
                    continue

                if len(row['Common Name']) == 0 :
                    continue

                if not 'SynBioHub URI' in row :
                    continue

                if len(row['SynBioHub URI']) == 0 :
                    continue

                common_name = row['Common Name']
                uri = row['SynBioHub URI']
                # Add common name to the item map
                item_map[common_name] = uri
                # There are also UIDs for each lab to add
                for lab_uid in constants.LAB_IDS_LIST:
                    # Ignore if the spreadsheet doesn't contain this lab
                    if not lab_uid in row or row[lab_uid] == '':
                        continue
                    # UID can be a CSV list, parse each value
                    for uid_str in row[lab_uid].split(sep=','):
                        # Make sure the UID matches the min len threshold, or is in the exception list
                        if len(uid_str) >= self.UID_LENGTH_THRESHOLD or uid_str in self.UID_LENGTH_EXCEPTION:
                            # If the UID isn't in the item map, add it with this URI
                            if uid_str not in item_map:
                                item_map[uid_str] = uri
                                lab_uid_src_map[uid_str] = lab_uid
                                lab_uid_common_map[uid_str] = common_name
                            else: # Otherwise, we need to check for an error
                                # If the UID has been used  before, we might have a conflict
                                if uid_str in lab_uid_src_map:
                                    # If the common name was the same for different UIDs, this won't have an effect
                                    # But if they differ, we have a conflict
                                    if not lab_uid_common_map[uid_str] == common_name:
                                        self.logger.error('Trying to add %s %s for common name %s, but the item map already contains %s from %s for common name %s!' %
                                                          (lab_uid, uid_str, common_name, uid_str, lab_uid_src_map[uid_str], lab_uid_common_map[uid_str]))
                                else: # If the UID wasn't used before, then it matches the common name and adding it would be redundant
                                    pass
                                    # If it matches the common name, that's fine
                                    #self.logger.error('Trying to add %s %s, but the item map already contains %s from common name!' % (lab_uid, uid_str, uid_str))
                        else:
                            self.logger.debug('Filtered %s %s for length' % (lab_uid, uid_str))

        
        intent_parser_utils.write_json_to_file(item_map, self.item_map_file)

        self.logger.info('Num items in item_map: %d' % len(item_map))

        return item_map
    
    def get_strateos_mappings(self):
        attribute_tab = self.get_tab_sheet('Attribute') 
        result = {}
        for row in attribute_tab:
            if not 'Common Name' in row and not 'Transcriptic UID' in row:
                continue
            
            common_name = row['Common Name']
            strateos_id = row ['Transcriptic UID']
            if strateos_id:
                result[common_name] =  strateos_id
   
        return result
    
    def get_tab_sheet(self, tab_name):
        sheet_data = self.fetch_spreadsheet_data()
        target_tab = None
        for tab in sheet_data:
            if tab == tab_name:
                target_tab = sheet_data[tab]
                break 
        
        if target_tab is None:
            raise DictionaryMaintainerException(tab_name + ' tab', 'cannot be found in spreadsheet.')
        
        return target_tab
        
    def load_type2tab(self):
        # Inverse map of typeTabs
        type2tab = {}
        for tab_name in self.google_accessor.type_tabs.keys():
            for type_name in self.google_accessor.type_tabs[tab_name]:
                type2tab[type_name] = tab_name
        return type2tab
 