from datetime import timedelta
from intent_parser.accessor.google_accessor import GoogleAccessor
from intent_parser.intent_parser_exceptions import DictionaryMaintainerException
import logging
import time
import threading

class SBOLDictionaryAccessor(object):
    """
    Provide functionalities to read and write information to the SBOL Dictionary Maintainer Google Spreadsheet.
    """

    logger = logging.getLogger('intent_parser_sbol_dictionary')

    # Some lab UIDs are short but still valid.  This defines an exceptions to the length threshold.
    UID_LENGTH_EXCEPTION = ['M9', 'LB']
    
    # Determine how long a lab UID string has to be in order to be added to the item map.
    # Strings below this size are ignored.
    UID_LENGTH_THRESHOLD = 3

    SYNC_PERIOD = timedelta(minutes=30)

    def __init__(self, spreadsheet_id, sbh):
        self.google_accessor = GoogleAccessor.create()
        self.google_accessor.set_spreadsheet_id(spreadsheet_id)
        self.sbh = sbh
        
        self.spreadsheet_lock = threading.Lock()
        self.spreadsheet_tab_data = {}
        self.spreadsheet_thread = threading.Thread(target=self._periodically_fetch_spreadsheet)

    def initial_fetch(self):
        self._fetch_spreadsheet_data()

    def get_spreadsheet_data(self):
        self.spreadsheet_lock.acquire()
        sheet_data = self.spreadsheet_tab_data.copy()
        self.spreadsheet_lock.release()
        return sheet_data

    def start_synchronizing_spreadsheet(self):
        self._fetch_spreadsheet_data()
        self.spreadsheet_thread.start()

    def stop_synchronizing_spreadsheet(self):
        self.spreadsheet_thread.join()

    def _periodically_fetch_spreadsheet(self):
        while True:
            time.sleep(self.SYNC_PERIOD.total_seconds())
            self.fetch_spreadsheet_data()

    def _fetch_spreadsheet_data(self):
        self.logger.info('Fetching SBOL Dictionary spreadsheet')
        spreadsheet_tabs = self.google_accessor.type_tabs.keys()

        self.spreadsheet_lock.acquire()
        update_spreadsheet_data = {}
        for tab in spreadsheet_tabs:
            update_spreadsheet_data[tab] = self.google_accessor.get_row_data(tab=tab)
            self.logger.info('Fetched data from tab ' + tab)
        self.spreadsheet_tab_data = update_spreadsheet_data
        self.spreadsheet_lock.release()

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

        try:
            self.google_accessor.set_row_data(dictionary_entry)
        except:
            raise Exception('Failed to add entry to the dictionary spreadsheet')
    
    def get_tab_sheet(self, tab_name):
        """Retrieve contents from a spreadsheet tab.
        Args:
            tab_name: name of tab.
        Returns:
            A spreadsheet tab.
        Raises:
            DictionaryMaintainerException to indicate if a tab does not exist within a spreadsheet.
        """
        self.spreadsheet_lock.acquire()
        sheet_data = self.spreadsheet_tab_data.copy()
        self.spreadsheet_lock.release()
        target_tab = None
        for tab in sheet_data:
            if tab == tab_name:
                target_tab = sheet_data[tab]
                break 
        if target_tab is None:
            raise DictionaryMaintainerException('Unable to locate %s tab in spreadsheet.' % tab_name)
        return target_tab
        
    def load_type2tab(self):
        # Inverse map of typeTabs
        type2tab = {}
        for tab_name in self.google_accessor.type_tabs.keys():
            for type_name in self.google_accessor.type_tabs[tab_name]:
                type2tab[type_name] = tab_name
        return type2tab
 