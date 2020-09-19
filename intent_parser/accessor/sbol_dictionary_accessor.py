from datetime import timedelta
from intent_parser.experiment_variables.experiment_variables import ExperimentVariable
from intent_parser.accessor.google_accessor import GoogleAccessor
from intent_parser.intent_parser_exceptions import DictionaryMaintainerException
import intent_parser.table.cell_parser as cell_parser
import intent_parser.constants.sbol_dictionary_constants as dictionary_constants
import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.utils.intent_parser_utils as intent_parser_utils
import logging
import os
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

    curr_path = os.path.dirname(os.path.realpath(__file__))
    ITEM_MAP_FILE = os.path.join(curr_path, 'item-map.json')

    SYNC_PERIOD = timedelta(minutes=30)

    def __init__(self, spreadsheet_id, sbh):
        self.google_accessor = GoogleAccessor().get_google_spreadsheet_accessor()
        self.sbh = sbh
        
        self.spreadsheet_lock = threading.Lock()
        self.spreadsheet_tab_data = {}
        self.spreadsheet_thread = threading.Thread(target=self._periodically_fetch_spreadsheet)

        self._spreadsheet_id = spreadsheet_id
        self._tab_headers = dict()
        self._inverse_tab_headers = dict()
        self.MAPPING_FAILURES = 'Mapping Failures'

        self.type_tabs = {
            'Attribute': ['Attribute'],
            'Reagent': ['Bead', 'CHEBI', 'Protein',
                        'Media', 'Stain', 'Buffer',
                        'Solution'],
            'Genetic Construct': ['DNA', 'RNA'],
            'Strain': ['Strain'],
            'Protein': ['Protein'],
            'Collections': ['Challenge Problem']
        }
        self._dictionary_headers = ['Common Name',
                                    'Type',
                                    'SynBioHub URI',
                                    'Stub Object?',
                                    'Definition URI',
                                    'Definition URI / CHEBI ID',
                                    'Status']

        self.mapping_failures_headers = ['Experiment/Run',
                                         'Lab',
                                         'Item Name',
                                         'Item ID',
                                         'Item Type (Strain or Reagent Tab)',
                                         'Status']

        self.labs = ['BioFAB',
                     'Ginkgo',
                     'Transcriptic',
                     'LBNL',
                     'EmeraldCloud',
                     'CalTech',
                     'PennState (Salis)']

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
            self._fetch_spreadsheet_data()

    def _fetch_spreadsheet_data(self):
        self.logger.info('Fetching SBOL Dictionary spreadsheet')
        spreadsheet_tabs = self.type_tabs.keys()

        self.spreadsheet_lock.acquire()
        update_spreadsheet_data = {}
        for tab in spreadsheet_tabs:
            update_spreadsheet_data[tab] = self.get_row_data(tab=tab)
            self.logger.info('Fetched data from tab ' + tab)
        self.spreadsheet_tab_data = update_spreadsheet_data
        self.spreadsheet_lock.release()

    def create_dictionary_entry(self, data, document_url, item_definition_uri):
        item_type = data['itemType']
        item_name = data['commonName']
        item_lab_ids = data['labId']
        item_lab_id_tag = data['labIdSelect']

        if self.sbh.get_sbh_spoofing_prefix() is not None:
            item_uri = document_url.replace(self.sbh.get_sbh_url(),
                                            self.sbh.get_sbh_spoofing_prefix())
        else:
            item_uri = document_url
        
        type2tab = self.load_type2tab()
        tab_name = type2tab[item_type]

        try:
            tab_data = self.get_row_data(tab=tab_name)
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
            self.set_row_data(dictionary_entry)
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
        for tab_name in self.type_tabs.keys():
            for type_name in self.type_tabs[tab_name]:
                type2tab[type_name] = tab_name
        return type2tab

    def add_sheet_request(self, sheet_title):
        """ Creates a Google request to add a tab to the current spreadsheet

        Args:
            sheet_title: name of the new tab
        """

        request = {
            'addSheet': {
                'properties': {
                    'title': sheet_title
                    }
                }
            }
        return request

    def create_dictionary_sheets(self):
        """ Creates the standard tabs on the current spreadsheet.
            The tabs are not populated with any data
        """
        add_sheet_requests = list(map(lambda x: self.add_sheet_request(x),
                                    list(self.type_tabs.keys())))
        # Mapping Failures tab
        add_sheet_requests.append(
            self.add_sheet_request(self.MAPPING_FAILURES)
        )
        self.google_accessor.execute_requests(add_sheet_requests)

        # Add sheet column headers
        headers = self._dictionary_headers
        headers += list(map(lambda x: x + ' UID', self.labs))

        for tab in self.type_tabs.keys():
            self._set_tab_data(tab + '!2:2', [headers])

        self._set_tab_data(self.MAPPING_FAILURES + '!2:2',
                           [self.mapping_failures_headers])

    def _cache_tab_headers(self, tab):
        """
        Cache the headers (and locations) in a tab
        returns a map that maps headers to column indexes
        """
        tab_data = self.google_accessor.get_tab_data(tab + "!2:2", self._spreadsheet_id)

        if 'values' not in tab_data:
            raise Exception('No header values found in tab "' +
                            tab + '"')

        header_values = tab_data['values'][0]
        header_map = {}
        for index in range(len(header_values)):
            header_map[header_values[index]] = index

        inverse_header_map = {}
        for key in header_map.keys():
            inverse_header_map[header_map[key]] = key

        self._tab_headers[tab] = header_map
        self._inverse_tab_headers[tab] = inverse_header_map

    def _clear_tab_header_cache(self):
        self._tab_headers.clear()
        self._inverse_tab_headers.clear()

    def get_tab_headers(self, tab):
        """
        Get the headers (and locations) in a tab
        returns a map that maps headers to column indexes
        """
        if tab not in self._tab_headers.keys():
            self._cache_tab_headers(tab)

        return self._tab_headers[tab]

    def _get_tab_inverse_headers(self, tab):
        """
        Get the headers (and locations) in a tab
        returns a map that maps column indexes to headers
        """
        if tab not in self._inverse_tab_headers.keys():
            self._cache_tab_headers(tab)

        return self._inverse_tab_headers[tab]

    def get_row_data(self, tab, row=None):
        """
        Retrieve data in a tab.  Returns a list of maps, where each list
        element maps a header name to the corresponding row value.  If
        no row is specified all rows are returned
        """
        if tab not in self._tab_headers.keys():
            self._cache_tab_headers(tab)

        header_value = self._inverse_tab_headers[tab]

        if row is None:
            value_range = tab + '!3:9999'
        else:
            value_range = tab + '!' + str(row) + ":" + str(row)

        tab_data = self.google_accessor.get_tab_data(value_range, self._spreadsheet_id)

        row_data = []
        if 'values' not in tab_data:
            return row_data

        values = tab_data['values']
        row_index = 3
        for row_values in values:
            this_row_data = {}
            for i in range(len(header_value)):
                if i >= len(row_values):
                    break
                header = header_value[i]
                value = row_values[i]

                if value is not None:
                    this_row_data[header] = value

            if len(this_row_data) > 0:
                this_row_data['row'] = row_index
                this_row_data['tab'] = tab
                row_data.append(this_row_data)
            row_index += 1
        return row_data

    def set_row_data(self, entry):
        """
        Write a row to the spreadsheet.  The entry is a map that maps
        column headers to the corresponding values, with an additional
        set of keys that specify the tab and the spreadsheet row
        """
        tab = entry['tab']
        row = entry['row']
        row_data = self.gen_row_data(entry=entry, tab=tab)
        row_range = '{}!{}:{}'.format(tab, row, row)
        self.google_accessor.set_tab_data(row_range, [row_data], self._spreadsheet_id)

    def set_row_value(self, entry, column):
        """
        Write a single cell value, given an entry, and the column name
        of the entry to be written
        """
        return self.set_cell_value(
            tab=entry['tab'],
            row=entry['row'],
            column=column,
            value=entry[column]
        )

    def set_cell_value(self, tab, row, column, value):
        """
        Write a single cell value, given an tab, row, column name, and value.
        """
        headers = self.get_tab_headers(tab)
        if column not in headers:
            raise Exception('No column "{}" on tab "{}"'.
                            format(column, tab))

        col = chr(ord('A') + headers[column])
        row_range = tab + '!' + col + str(row)
        self.google_accessor.set_tab_data(row_range, [[value]], self._spreadsheet_id)

    def gen_row_data(self, entry, tab):
        """
        Generate a list of spreadsheet row value given a map the maps
        column headers to values
        """
        headers = self._get_tab_inverse_headers(tab)
        row_data = [''] * (max(headers.keys()) + 1)

        for index in headers.keys():
            header = headers[index]
            if header not in entry:
                continue
            row_data[index] = entry[header]

        return row_data

    def map_common_names_and_tacc_id(self):
        result = {}
        attribute_tab = self.get_tab_sheet(dictionary_constants.TAB_ATTRIBUTE)
        for row in attribute_tab:
            if dictionary_constants.COLUMN_COMMON_NAME in row and dictionary_constants.COLUMN_TACC_UID in row:
                common_name = row[dictionary_constants.COLUMN_COMMON_NAME]
                tacc_id = row[dictionary_constants.COLUMN_TACC_UID]
                if tacc_id:
                    result[tacc_id] = common_name
        return result

    def get_mapped_strain(self, lab_name):
        """Create a mapping for strains from the Strains tab.
        Args:
            lab_name: A string to represent the name of a Lab.

        Returns:
            A Tuple of StrainMapping objects. The key represents the sbh uri.
            The value is a StrainMapping object
        """
        mapped_strains = {}
        if lab_name not in dictionary_constants.MAPPED_LAB_UID:
            message = 'Unable to map %s to a LAB_UID in the SBOL Dictionary for processing strains.' % lab_name
            raise DictionaryMaintainerException(message)
        lab_uid = dictionary_constants.MAPPED_LAB_UID[lab_name]

        strain_tab = self.get_tab_sheet(dictionary_constants.TAB_STRAIN)
        for row in strain_tab:
            if (dictionary_constants.COLUMN_COMMON_NAME in row
                and dictionary_constants.COLUMN_SYNBIOHUB_URI in row
                and lab_uid in row):
                sbh_uri = row[dictionary_constants.COLUMN_SYNBIOHUB_URI]
                common_name = row[dictionary_constants.COLUMN_COMMON_NAME]
                lab_strain_names = {}
                if row[lab_uid]:
                    lab_strain_names = [name for name in cell_parser.PARSER.extract_name_value(row[lab_uid])]
                mapped_strains[sbh_uri] = ExperimentVariable(sbh_uri, lab_name, common_name, lab_names=lab_strain_names)
        return mapped_strains

    def create_experiment_variables_from_spreadsheet_tab(self, tab):
        experiment_variables ={}
        for row in tab:
            if (dictionary_constants.COLUMN_COMMON_NAME in row and dictionary_constants.COLUMN_SYNBIOHUB_URI in row):
                sbh_uri = row[dictionary_constants.COLUMN_SYNBIOHUB_URI]
                common_name = row[dictionary_constants.COLUMN_COMMON_NAME]
                for lab_name, lab_uid in dictionary_constants.MAPPED_LAB_UID.items():
                    if lab_uid and lab_uid in row:
                        if row[lab_uid]:
                            lab_strain_names = [name for name in cell_parser.PARSER.extract_name_value(row[lab_uid])]
                            experiment_variables[common_name] = ExperimentVariable(sbh_uri, lab_name, common_name, lab_names=lab_strain_names)
                        else:
                            experiment_variables[common_name] = ExperimentVariable(sbh_uri, lab_name, common_name)
        return experiment_variables

    def get_common_name_from_transcriptic_id(self, transcriptic_id):
        mappings = self.map_common_names_and_transcriptic_id()
        for key, value in mappings.items():
            if transcriptic_id == value:
                return key
        return None

    def map_common_names_and_transcriptic_id(self):
        result = {}
        attribute_tab = self.get_tab_sheet(dictionary_constants.TAB_ATTRIBUTE)
        for row in attribute_tab:
            if dictionary_constants.COLUMN_COMMON_NAME in row and dictionary_constants.COLUMN_TRANSCRIPT_UID in row:
                common_name = row[dictionary_constants.COLUMN_COMMON_NAME]
                strateos_id = row[dictionary_constants.COLUMN_TRANSCRIPT_UID]
                if strateos_id:
                    result[common_name] = strateos_id
        return result

    def get_common_names_to_uri_new(self):
        tabs_to_process = [dictionary_constants.TAB_PROTEIN,
                           dictionary_constants.TAB_STRAIN,
                           dictionary_constants.TAB_GENETIC_CONSTRUCTS,
                           dictionary_constants.TAB_REAGENT]
        result = {}
        for tab_name in tabs_to_process:
            tab = self.get_tab_sheet(tab_name)
            exper_var = self.create_experiment_variables_from_spreadsheet_tab(tab)
            result.update(exper_var)
        return result

    def get_common_names_to_uri(self, use_cache=False):
        """
        Use the SBOL Dictionary to generate a dictionary of common names referring to its SBH URI and store it into a local item-map.json file
        """
        sheet_data = self.get_spreadsheet_data()
        item_map = {}
        self.logger.info('Generating item map, %d' % time.time())
        if use_cache:
            item_map = intent_parser_utils.load_json_file(self.ITEM_MAP_FILE)
            self, self.logger.info('Num items in item_map: %d' % len(item_map))

        lab_uid_src_map = {}
        lab_uid_common_map = {}

        for tab in sheet_data:
            for row in sheet_data[tab]:
                if dictionary_constants.COLUMN_COMMON_NAME not in row:
                    continue

                if len(row[dictionary_constants.COLUMN_COMMON_NAME]) == 0:
                    continue

                if 'SynBioHub URI' not in row:
                    continue

                if len(row['SynBioHub URI']) == 0:
                    continue

                common_name = row[dictionary_constants.COLUMN_COMMON_NAME]
                uri = row['SynBioHub URI']
                # Add common name to the item map
                item_map[common_name] = uri
                # There are also UIDs for each lab to add
                for lab_uid in intent_parser_constants.LAB_IDS_LIST:
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
                            else:  # Otherwise, we need to check for an error
                                # If the UID has been used  before, we might have a conflict
                                if uid_str in lab_uid_src_map:
                                    # If the common name was the same for different UIDs, this won't have an effect
                                    # But if they differ, we have a conflict
                                    if not lab_uid_common_map[uid_str] == common_name:
                                        self.logger.error(
                                            'Trying to add %s %s for common name %s, but the item map already contains %s from %s for common name %s!' %
                                            (lab_uid, uid_str, common_name, uid_str, lab_uid_src_map[uid_str],
                                             lab_uid_common_map[uid_str]))
                                else:  # If the UID wasn't used before, then it matches the common name and adding it would be redundant
                                    pass
                                    # If it matches the common name, that's fine
                                    # self.logger.error('Trying to add %s %s, but the item map already contains %s from common name!' % (lab_uid, uid_str, uid_str))
                        else:
                            self.logger.debug('Filtered %s %s for length' % (lab_uid, uid_str))
        intent_parser_utils.write_json_to_file(item_map, self.ITEM_MAP_FILE)
        self.logger.info('Num items in item_map: %d' % len(item_map))
        return item_map

