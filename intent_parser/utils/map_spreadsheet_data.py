import intent_parser.constants.intent_parser_constants as intent_parser_constants
import intent_parser.constants.sbol_dictionary_constants as dictionary_constants
import intent_parser.utils.intent_parser_utils as intent_parser_utils
import logging
import os
import time

logger = logging.getLogger('intent_parser')

curr_path = os.path.dirname(os.path.realpath(__file__))
ITEM_MAP_FILE = os.path.join(curr_path, 'item-map.json')

def map_common_names_and_tacc_id(spreadsheet_tab_data):
    result = {}
    for row in spreadsheet_tab_data:
        if dictionary_constants.COLUMN_COMMON_NAME in row and dictionary_constants.COLUMN_TACC_UID in row:
            common_name = row[dictionary_constants.COLUMN_COMMON_NAME]
            tacc_id = row[dictionary_constants.COLUMN_TACC_UID]
            if tacc_id:
                result[common_name] = tacc_id
    return result

def get_common_name_from_tacc_id(tacc_id, attribute_tab):
    mappings = map_common_names_and_tacc_id(attribute_tab)
    for key, value in mappings.items():
        if tacc_id == value:
            return key
    return None

def get_common_name_from_trascriptic_id(transcriptic_id, attribute_tab):
    mappings = map_common_names_and_transcriptic_id(attribute_tab)
    for key, value in mappings.items():
        if transcriptic_id == value:
            return key
    return None

def map_common_names_and_transcriptic_id(attribute_tab):
    result = {}
    for row in attribute_tab:
        if dictionary_constants.COLUMN_COMMON_NAME in row and dictionary_constants.COLUMN_TRANSCRIPT_UID in row:
            common_name = row[dictionary_constants.COLUMN_COMMON_NAME]
            strateos_id = row[dictionary_constants.COLUMN_TRANSCRIPT_UID]
            if strateos_id:
                result[common_name] = strateos_id
    return result

def get_common_names_to_uri(sheet_data, use_cache=False):
    """
    Use the SBOL Dictionary to generate a dictionary of common names referring to its SBH URI and store it into a local item-map.json file
    """
    item_map = {}
    logger.info('Generating item map, %d' % time.time())
    if use_cache:
        item_map = intent_parser_utils.load_json_file(ITEM_MAP_FILE)
        logger.info('Num items in item_map: %d' % len(item_map))

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
                        else: # Otherwise, we need to check for an error
                            # If the UID has been used  before, we might have a conflict
                            if uid_str in lab_uid_src_map:
                                # If the common name was the same for different UIDs, this won't have an effect
                                # But if they differ, we have a conflict
                                if not lab_uid_common_map[uid_str] == common_name:
                                    logger.error('Trying to add %s %s for common name %s, but the item map already contains %s from %s for common name %s!' %
                                                      (lab_uid, uid_str, common_name, uid_str, lab_uid_src_map[uid_str], lab_uid_common_map[uid_str]))
                            else: # If the UID wasn't used before, then it matches the common name and adding it would be redundant
                                pass
                                # If it matches the common name, that's fine
                                #self.logger.error('Trying to add %s %s, but the item map already contains %s from common name!' % (lab_uid, uid_str, uid_str))
                    else:
                        logger.debug('Filtered %s %s for length' % (lab_uid, uid_str))
    intent_parser_utils.write_json_to_file(item_map, ITEM_MAP_FILE)
    logger.info('Num items in item_map: %d' % len(item_map))
    return item_map

