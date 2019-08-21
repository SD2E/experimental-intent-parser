import unittest
import warnings
import json
import getopt
import sys
import os
import time
import urllib.request
import pickle

from ips_test_utils import compare_spell_results
from ips_test_utils import get_currently_selected_text

from unittest.mock import Mock, patch, DEFAULT

try:
    from intent_parser_server import IntentParserServer
except Exception as e:
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../src'))
    from intent_parser_server import IntentParserServer

from google_accessor import GoogleAccessor

class TestIntentParserServer(unittest.TestCase):

    spellcheckFile = 'doc_1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA.json'

    expected_spelling_size = 166

    spellcheckResults = 'spell_results.pickle'

    dataDir = 'data'

    def setUp(self):
        """
        Configure an instance of IntentParserServer for spellcheck testing.
        """
        self.doc_content = None
        with open(os.path.join(self.dataDir,self.spellcheckFile), 'r') as fin:
            self.doc_content = json.loads(fin.read())

        if self.doc_content is None:
            self.fail('Failed to read in test document! Path: ' + os.path.join(self.dataDir,self.spellcheckFile))

        # Clear all dictionary information
        if os.path.exists(IntentParserServer.dict_path):
            for file in os.listdir(IntentParserServer.dict_path):
                os.remove(os.path.join(IntentParserServer.dict_path, file))
            os.rmdir(IntentParserServer.dict_path)

        self.doc_id = '1xMqOx9zZ7h2BIxSdWp2Vwi672iZ30N_2oPs8rwGUoTA'
        self.user = 'bbnTest'
        self.user_email = 'test@bbn.com'
        self.json_body = {'documentId' : self.doc_id, 'user' : self.user, 'userEmail' : self.user_email}

        self.ips = IntentParserServer(init_server=False, init_sbh=False)
        self.ips.client_state_lock = Mock()
        self.ips.client_state_map = {}
        self.ips.google_accessor = Mock()
        self.ips.google_accessor.get_document = Mock(return_value=self.doc_content)
        self.ips.send_response = Mock()
        self.ips.get_json_body = Mock(return_value=self.json_body)

        self.ips.process_add_by_spelling([], [])
        
        # Code to save the GT spelling results, when the test doc has been updated
        #with open(os.path.join(self.dataDir, self.spellcheckResults), 'wb') as fout:
        #    pickle.dump(self.ips.client_state_map[self.doc_id]['spelling_results'], fout)
            
        self.spelling_gt = None
        with open(os.path.join(self.dataDir, self.spellcheckResults), 'rb') as fin:
            self.spelling_gt = pickle.load(fin)

        if self.spelling_gt is None:
            self.fail('Failed to read in spelling results! Path: ' + os.join(self.dataDir, self.spellcheckResults))

    def test_spellcheck_basic(self):
        """
        Basic check, ensure that spellcheck runs and the results are as expected
        """
        # Basic sanity checks
        self.assertTrue(self.ips.client_state_map[self.doc_id]['user_id'] == self.user_email)
        self.assertTrue(self.ips.client_state_map[self.doc_id]['document_id'] == self.doc_id)
        self.assertTrue(self.ips.client_state_map[self.doc_id]['spelling_size'] is self.expected_spelling_size)
        self.assertTrue(self.ips.client_state_map[self.doc_id]['spelling_index'] is 0)
        self.assertTrue(compare_spell_results(self.spelling_gt, self.ips.client_state_map[self.doc_id]['spelling_results']), 'Spelling result sets do not match!')
    
    def test_spellcheck_add_dictionary(self):
        """
        Test the ability to add a term into the spelling dictionary
        """
        remove_term = 'proteomics'
        # Find the index of the first instance of 'proteomics'
        first_proteomics_idx = 0
        while not self.ips.client_state_map[self.doc_id]['spelling_results'][first_proteomics_idx]['term'] == remove_term:
            first_proteomics_idx += 1
        self.ips.client_state_map[self.doc_id]['spelling_index'] = first_proteomics_idx

        # Remove proteomics
        self.ips.spellcheck_add_dictionary([], self.ips.client_state_map[self.doc_id])

        # The GT should not match
        self.assertFalse(compare_spell_results(self.spelling_gt, self.ips.client_state_map[self.doc_id]['spelling_results']), 'Spelling result sets should not match!')

        # We expected to remove 15 results
        self.assertTrue(self.ips.client_state_map[self.doc_id]['spelling_size'] is (self.expected_spelling_size - 15))

        # Compare to removed entry
        spelling_gt_no_prot = [res for res in self.spelling_gt if not res['term'] == remove_term]
        self.assertTrue(compare_spell_results(spelling_gt_no_prot, self.ips.client_state_map[self.doc_id]['spelling_results']))

        # Check that a spelling dictionary was saved, to store the users preferences
        dict_path = os.path.join(self.ips.dict_path, self.user_email + '.json')
        self.assertTrue(os.path.exists(dict_path))

    def test_spellcheck_add_ignore(self):
        """
        """
        numResults = self.ips.client_state_map[self.doc_id]['spelling_size']
        for idx in range(1, numResults):
            result = self.ips.spellcheck_add_ignore([], self.ips.client_state_map[self.doc_id])
            self.assertTrue(self.ips.client_state_map[self.doc_id]['spelling_index'] == idx)
            self.assertTrue(len(result) == 2 )

        result = self.ips.spellcheck_add_ignore([], self.ips.client_state_map[self.doc_id])
        self.assertTrue(len(result) == 0)

    def test_spellcheck_add_ignore_all_monotinicity(self):
        """
        This tests a bug that was found where the ignore all feature could cause the results index to not increase monotonically.
        In the case where the next term matched a previously skipped result, the index would jump back to the earlier index.
        For instance, if we had arabinose, proteomic, arabinose, and the order of operations was Ignore, Ignore All, the index would jump back to 0 instead of 1 (since proteomic is removed).
        """

        # Ignore result one, which is arabinose in the test document
        result = self.ips.spellcheck_add_ignore([], self.ips.client_state_map[self.doc_id])
        self.assertTrue(self.ips.client_state_map[self.doc_id]['spelling_index'] == 1)
        self.assertTrue(len(result) == 2)

        # Remove proteomics
        result = self.ips.spellcheck_add_ignore_all([], self.ips.client_state_map[self.doc_id])
        # The index should remove the same, not get smaller
        self.assertTrue(self.ips.client_state_map[self.doc_id]['spelling_index'] == 1)
        self.assertTrue(len(result) == 2)
        
    def test_spellcheck_add_ignore_all(self):
        """
        """
        remove_term = 'proteomics'
        # Find the index of the first instance of 'proteomics'
        first_proteomics_idx = 0
        while not self.ips.client_state_map[self.doc_id]['spelling_results'][first_proteomics_idx]['term'] == remove_term:
            first_proteomics_idx += 1
        self.ips.client_state_map[self.doc_id]['spelling_index'] = first_proteomics_idx

        # Remove proteomics
        self.ips.spellcheck_add_ignore_all([], self.ips.client_state_map[self.doc_id])

        # The GT should not match
        self.assertFalse(compare_spell_results(self.spelling_gt, self.ips.client_state_map[self.doc_id]['spelling_results']), 'Spelling result sets should not match!')

        # We expected to remove 15 results
        self.assertTrue(self.ips.client_state_map[self.doc_id]['spelling_size'] is (self.expected_spelling_size - 15))

        # Compare to removed entry
        spelling_gt_no_prot = [res for res in self.spelling_gt if not res['term'] == remove_term]
        self.assertTrue(compare_spell_results(spelling_gt_no_prot, self.ips.client_state_map[self.doc_id]['spelling_results']))

    def test_spellcheck_add_synbiohub_link(self):
        """
        Test the Link button for SBH Add dialog, SPARQL query results Link
        This will try to link each result in the spelling results set.
        The expectation is that each entry will result in 3 actions from the first call (SBH Add dialog, highlight, sidebar).
        Each time the link action is taken, another 3 actions should be generated, and the index increased (Link action, highlight, sidebar)
        """
        self.item_types = []
        self.json_body['data'] = {}
        self.json_body['data']['isSpellcheck'] = 'True'
        self.json_body['data']['extra'] = {}
        numResults = self.ips.client_state_map[self.doc_id]['spelling_size']
        for idx in range(1, numResults):
            result = self.ips.spellcheck_add_synbiohub([], self.ips.client_state_map[self.doc_id])

            search_result = self.ips.client_state_map[self.doc_id]['spelling_results'][self.ips.client_state_map[self.doc_id]['spelling_index']]
            self.json_body['data']['extra']['action'] = 'link'
            self.json_body['data']['extra']['link'] = 'test'
            self.json_body['data']['selectionStartParagraph'] = search_result['select_start']['paragraph_index']
            self.json_body['data']['selectionStartOffset'] = search_result['select_start']['cursor_index']
            self.json_body['data']['selectionEndOffset'] = search_result['select_end']['cursor_index'] + 1

            self.ips.process_submit_form([], [])

            add_results = json.loads(self.ips.send_response.call_args[0][2])
            actions = add_results['actions']

            self.assertTrue(self.ips.client_state_map[self.doc_id]['spelling_index'] == idx, 'Failed on index %d of %d' % (idx, numResults))
            self.assertTrue(len(result) == 3, 'Failed on index %d of %d' % (idx, numResults))
            self.assertTrue(len(actions) == 3, 'Failed on index %d of %d' % (idx, numResults))
            self.assertTrue(add_results['results']['operationSucceeded'], 'Failed on index %d of %d' % (idx, numResults))

        # Last Result
        result = self.ips.spellcheck_add_synbiohub([], self.ips.client_state_map[self.doc_id])

        search_result = self.ips.client_state_map[self.doc_id]['spelling_results'][self.ips.client_state_map[self.doc_id]['spelling_index']]
        self.json_body['data']['extra']['action'] = 'link'
        self.json_body['data']['extra']['link'] = 'test'
        self.json_body['data']['selectionStartParagraph'] = search_result['select_start']['paragraph_index']
        self.json_body['data']['selectionStartOffset'] = search_result['select_start']['cursor_index']
        self.json_body['data']['selectionEndOffset'] = search_result['select_end']['cursor_index'] + 1

        self.ips.process_submit_form([], [])

        add_results = json.loads(self.ips.send_response.call_args[0][2])
        actions = add_results['actions']

        self.assertTrue(self.ips.client_state_map[self.doc_id]['spelling_index'] == numResults, 'Failed on index %d of %d' % (idx, numResults))
        self.assertTrue(len(result) == 3, 'Failed on index %d of %d' % (idx, numResults))
        self.assertTrue(len(actions) == 1, 'Failed on index %d of %d' % (idx, numResults))
        self.assertTrue(add_results['results']['operationSucceeded'], 'Failed on index %d of %d' % (idx, numResults))

    def test_spellcheck_add_synbiohub_link_all(self):
        """
        Test the Link All button for SBH Add dialog, SPARQL query results Link
        This will try to link each result in the spelling results set.
        The expectation is that each entry will result in 3 actions from the first call (SBH Add dialog, highlight, sidebar).
        Each time the link all action is taken, another 2 + N actions should be generated, and the index increased ( N Link actions, highlight, sidebar)
        The number of iterations will depend on how many results get removed each time Link All is called.
        """
        self.item_types = []
        self.json_body['data'] = {}
        self.json_body['data']['isSpellcheck'] = 'True'
        self.json_body['data']['extra'] = {}
        it_count = 0
        while self.ips.client_state_map[self.doc_id]['spelling_index'] < self.ips.client_state_map[self.doc_id]['spelling_size']:
            search_result = self.ips.client_state_map[self.doc_id]['spelling_results'][self.ips.client_state_map[self.doc_id]['spelling_index']]
            term = search_result['term']
            matching_results = [t for t in self.ips.client_state_map[self.doc_id]['spelling_results'] if t['term'] == term]
            count_of_matches = len(matching_results)

            result = self.ips.spellcheck_add_synbiohub([], self.ips.client_state_map[self.doc_id])

            self.json_body['data']['extra']['action'] = 'linkAll'
            self.json_body['data']['extra']['link'] = 'test'
            self.json_body['data']['selectedTerm'] = term
            self.json_body['data']['documentId'] = self.json_body['documentId']

            self.ips.process_submit_form([], [])

            add_results = json.loads(self.ips.send_response.call_args[0][2])
            actions = add_results['actions']

            if self.ips.client_state_map[self.doc_id]['spelling_index'] + len(actions) < self.ips.client_state_map[self.doc_id]['spelling_size']:
                num_other_actions = 2
            else:
                num_other_actions = 0

            self.assertTrue(len(result) == 3, 'Failed on iteration %d' % (it_count))
            self.assertTrue(len(actions) == num_other_actions + count_of_matches, 'Failed on iteration %d' % (it_count))
            self.assertTrue(add_results['results']['operationSucceeded'], 'Failed on iteration %d' % (it_count))
            it_count += 1

    def test_spellcheck_add_synbiohub_submit(self):
        """
        Test the Submit button for SBH Add dialog
        This will try to link each result in the spelling results set to a new SBH entry.
        The expectation is that each entry will result in 3 actions from the first call (SBH Add dialog, highlight, sidebar).
        Each time the link action is taken, another 3 actions should be generated, and the index increased (Link action, highlight, sidebar)
        """
        self.ips.sbh = Mock()
        self.ips.sbh.submit = Mock()
        self.ips.sbh.exists = Mock(return_value = False)
        self.ips.create_dictionary_entry = Mock()
        self.ips.sbh_uri_prefix = 'https://hub-staging.sd2e.org/user/sd2e/intent_parser/'
        self.ips.sbh_collection_uri = 'https://hub.sd2e.org/user/sd2e/intent_parser/intent_parser_collection/1'

        item_type_list = []
        for sbol_type in self.ips.item_types:
            item_type_list += self.ips.item_types[sbol_type].keys()

        self.item_types = []
        self.json_body['data'] = {}
        self.json_body['data']['isSpellcheck'] = 'True'
        self.json_body['data']['extra'] = {}
        numResults = self.ips.client_state_map[self.doc_id]['spelling_size']
        for idx in range(1, numResults):
            result = self.ips.spellcheck_add_synbiohub([], self.ips.client_state_map[self.doc_id])

            search_result = self.ips.client_state_map[self.doc_id]['spelling_results'][self.ips.client_state_map[self.doc_id]['spelling_index']]
            self.json_body['data']['extra']['action'] = 'submit'
            self.json_body['data']['extra']['link'] = 'test_link'
            self.json_body['data']['selectionStartParagraph'] = search_result['select_start']['paragraph_index']
            self.json_body['data']['selectionStartOffset'] = search_result['select_start']['cursor_index']
            self.json_body['data']['selectionEndParagraph'] = search_result['select_start']['paragraph_index']
            self.json_body['data']['selectionEndOffset'] = search_result['select_end']['cursor_index'] + 1
            self.json_body['data']['documentId'] = self.doc_id
            self.json_body['data']['selectedTerm'] = search_result['term']
            self.json_body['data']['formName'] = 'addToSynBioHub'
            self.json_body['data']['commonName'] = search_result['term']
            self.json_body['data']['displayId'] = self.ips.sanitize_name_to_display_id(search_result['term'])
            self.json_body['data']['itemType'] = item_type_list[idx % len(item_type_list)]
            self.json_body['data']['definitionURI'] = 'test_defn_uri'
            self.json_body['data']['labIdSelect'] = self.ips.lab_ids_list[idx % len(self.ips.lab_ids_list)]
            self.json_body['data']['labId'] = 'test_lab_id'

            self.ips.process_submit_form([], [])

            document_url = self.ips.sbh_uri_prefix + self.json_body['data']['displayId'] + '/1'

            # Ensure that prev link is set for the "Reuse previous link" button
            for res in self.ips.client_state_map[self.doc_id]['spelling_results']:
                if res['term'] == search_result['term']:
                    self.assertTrue('prev_link' in res)
                    self.assertTrue(res['prev_link'] == document_url, 'new link: %s, expected link: %s' % (res['prev_link'], document_url))

            add_results = json.loads(self.ips.send_response.call_args[0][2])
            self.assertTrue('actions' in add_results, 'Failed on index %d of %d' % (idx, numResults))
            actions = add_results['actions']

            self.assertTrue(self.ips.client_state_map[self.doc_id]['spelling_index'] == idx, 'Failed on index %d of %d' % (idx, numResults))
            self.assertTrue(len(result) == 3, 'Failed on index %d of %d' % (idx, numResults))
            self.assertTrue(len(actions) == 3, 'Failed on index %d of %d' % (idx, numResults))
            self.assertTrue(add_results['results']['operationSucceeded'], 'Failed on index %d of %d' % (idx, numResults))

        # Last Result
        result = self.ips.spellcheck_add_synbiohub([], self.ips.client_state_map[self.doc_id])

        search_result = self.ips.client_state_map[self.doc_id]['spelling_results'][self.ips.client_state_map[self.doc_id]['spelling_index']]
        self.json_body['data']['extra']['action'] = 'submit'
        self.json_body['data']['extra']['link'] = 'test_link'
        self.json_body['data']['selectionStartParagraph'] = search_result['select_start']['paragraph_index']
        self.json_body['data']['selectionStartOffset'] = search_result['select_start']['cursor_index']
        self.json_body['data']['selectionEndParagraph'] = search_result['select_start']['paragraph_index']
        self.json_body['data']['selectionEndOffset'] = search_result['select_end']['cursor_index'] + 1
        self.json_body['data']['documentId'] = self.doc_id
        self.json_body['data']['selectedTerm'] = search_result['term']
        self.json_body['data']['formName'] = 'addToSynBioHub'
        self.json_body['data']['commonName'] = search_result['term']
        self.json_body['data']['displayId'] = search_result['term']
        self.json_body['data']['itemType'] = item_type_list[idx % len(item_type_list)]
        self.json_body['data']['definitionURI'] = 'test_defn_uri'
        self.json_body['data']['labIdSelect'] = self.ips.lab_ids_list[idx % len(self.ips.lab_ids_list)]
        self.json_body['data']['labId'] = 'test_lab_id'

        self.ips.process_submit_form([], [])

        add_results = json.loads(self.ips.send_response.call_args[0][2])
        actions = add_results['actions']

        self.assertTrue(self.ips.client_state_map[self.doc_id]['spelling_index'] == numResults, 'Failed on index %d of %d' % (idx, numResults))
        self.assertTrue(len(result) == 3, 'Failed on index %d of %d' % (idx, numResults))
        self.assertTrue(len(actions) == 1, 'Failed on index %d of %d' % (idx, numResults))
        self.assertTrue(add_results['results']['operationSucceeded'], 'Failed on index %d of %d' % (idx, numResults))

    def test_spellcheck_add_synbiohub_submit_link_all(self):
        """
        Test the Link All button for SBH Add dialog, SPARQL query results Link
        This will try to link each result in the spelling results set.
        The expectation is that each entry will result in 3 actions from the first call (SBH Add dialog, highlight, sidebar).
        Each time the link all action is taken, another 2 + N actions should be generated, and the index increased ( N Link actions, highlight, sidebar)
        The number of iterations will depend on how many results get removed each time Link All is called.
        """
        self.ips.sbh = Mock()
        self.ips.sbh.submit = Mock()
        self.ips.sbh.exists = Mock(return_value = False)
        self.ips.create_dictionary_entry = Mock()
        self.ips.sbh_uri_prefix = 'https://hub-staging.sd2e.org/user/sd2e/intent_parser/'
        self.ips.sbh_collection_uri = 'https://hub.sd2e.org/user/sd2e/intent_parser/intent_parser_collection/1'

        item_type_list = []
        for sbol_type in self.ips.item_types:
            item_type_list += self.ips.item_types[sbol_type].keys()

        self.item_types = []
        self.json_body['data'] = {}
        self.json_body['data']['isSpellcheck'] = 'True'
        self.json_body['data']['extra'] = {}
        it_count = 0
        while self.ips.client_state_map[self.doc_id]['spelling_index'] < self.ips.client_state_map[self.doc_id]['spelling_size']:
            search_result = self.ips.client_state_map[self.doc_id]['spelling_results'][self.ips.client_state_map[self.doc_id]['spelling_index']]
            term = search_result['term']
            matching_results = [t for t in self.ips.client_state_map[self.doc_id]['spelling_results'] if t['term'] == term]
            count_of_matches = len(matching_results)

            result = self.ips.spellcheck_add_synbiohub([], self.ips.client_state_map[self.doc_id])

            search_result = self.ips.client_state_map[self.doc_id]['spelling_results'][self.ips.client_state_map[self.doc_id]['spelling_index']]
            self.json_body['data']['extra']['action'] = 'submitLinkAll'
            self.json_body['data']['extra']['link'] = 'test_link'
            self.json_body['data']['selectionStartParagraph'] = search_result['select_start']['paragraph_index']
            self.json_body['data']['selectionStartOffset'] = search_result['select_start']['cursor_index']
            self.json_body['data']['selectionEndParagraph'] = search_result['select_start']['paragraph_index']
            self.json_body['data']['selectionEndOffset'] = search_result['select_end']['cursor_index'] + 1
            self.json_body['data']['documentId'] = self.doc_id
            self.json_body['data']['selectedTerm'] = search_result['term']
            self.json_body['data']['formName'] = 'addToSynBioHub'
            self.json_body['data']['commonName'] = search_result['term']
            self.json_body['data']['displayId'] = self.ips.sanitize_name_to_display_id(search_result['term'])
            self.json_body['data']['itemType'] = item_type_list[it_count % len(item_type_list)]
            self.json_body['data']['definitionURI'] = 'test_defn_uri'
            self.json_body['data']['labIdSelect'] = self.ips.lab_ids_list[it_count % len(self.ips.lab_ids_list)]
            self.json_body['data']['labId'] = 'test_lab_id'

            self.ips.process_submit_form([], [])

            add_results = json.loads(self.ips.send_response.call_args[0][2])
            actions = add_results['actions']

            if self.ips.client_state_map[self.doc_id]['spelling_index'] + len(actions) < self.ips.client_state_map[self.doc_id]['spelling_size']:
                num_other_actions = 2
            else:
                num_other_actions = 0

            self.assertTrue(len(result) == 3, 'Failed on iteration %d' % (it_count))
            self.assertTrue(len(actions) == num_other_actions + count_of_matches, 'Failed on iteration %d' % (it_count))
            self.assertTrue(add_results['results']['operationSucceeded'], 'Failed on iteration %d' % (it_count))
            it_count += 1

    def test_submit_createMeasurementTable(self):
        """
        Test the Create Measurement Table submit action
        """
        self.item_types = []
        self.json_body['data'] = {}
        self.json_body['data']['isSpellcheck'] = 'False'
        self.json_body['data']['extra'] = {}
        self.json_body['data']['extra']['action'] = 'createMeasurementTable'
        self.json_body['data']['numReagents'] = 3
        self.json_body['data']['temperature'] = True
        self.json_body['data']['timepoint'] = False
        self.json_body['data']['numRows'] = 4
        self.json_body['data']['cursorChildIndex'] = 3

        self.ips.process_submit_form([], [])

        add_results = json.loads(self.ips.send_response.call_args[0][2])
        actions = add_results['actions']

        self.assertTrue(len(actions) == 1) # Expect one addTable action
        self.assertTrue(actions[0]['cursorChildIndex'] == self.json_body['data']['cursorChildIndex'])
        self.assertTrue(self.json_body['data']['numRows'] + 1 == len(actions[0]['tableData']))
        self.assertTrue(len(actions[0]['colSizes']) == len(actions[0]['tableData'][0]))
        self.assertTrue(len(actions[0]['colSizes']) ==  self.json_body['data']['numReagents'] + 3 + 1 + 1)


    def test_spellcheck_add_select_functions(self):
        """
        Select previous word button action for additions by spelling
        """
        # Skip first five results
        self.ips.spellcheck_add_ignore([], self.ips.client_state_map[self.doc_id])
        self.ips.spellcheck_add_ignore([], self.ips.client_state_map[self.doc_id])
        self.ips.spellcheck_add_ignore([], self.ips.client_state_map[self.doc_id])
        self.ips.spellcheck_add_ignore([], self.ips.client_state_map[self.doc_id])
        self.ips.spellcheck_add_ignore([], self.ips.client_state_map[self.doc_id])

        #or subgoals
        result = self.ips.spellcheck_add_select_previous([], self.ips.client_state_map[self.doc_id])
        selected_text = get_currently_selected_text(self, self.ips, self.doc_id, self.doc_content)
        self.assertTrue(selected_text == 'or subgoals')

        #goal (or subgoals
        result = self.ips.spellcheck_add_select_previous([], self.ips.client_state_map[self.doc_id])
        selected_text = get_currently_selected_text(self, self.ips, self.doc_id, self.doc_content)
        self.assertTrue(selected_text == 'goal (or subgoals')

        result = self.ips.spellcheck_add_select_next([], self.ips.client_state_map[self.doc_id])
        selected_text = get_currently_selected_text(self, self.ips, self.doc_id, self.doc_content)
        self.assertTrue(selected_text == 'goal (or subgoals). Include')

        result = self.ips.spellcheck_add_drop_first([], self.ips.client_state_map[self.doc_id])
        selected_text = get_currently_selected_text(self, self.ips, self.doc_id, self.doc_content)
        self.assertTrue(selected_text == 'or subgoals). Include')

        result = self.ips.spellcheck_add_drop_last([], self.ips.client_state_map[self.doc_id])
        selected_text = get_currently_selected_text(self, self.ips, self.doc_id, self.doc_content)
        self.assertTrue(selected_text == 'or subgoals')

    def test_spellcheck_link(self):
        """
        Test Manual Link button
        """
        testLink = 'http://test-link.org'
        self.json_body['data'] = {}
        self.json_body['data']['buttonId'] = {}
        self.json_body['data']['buttonId']['link'] = testLink

        while self.ips.client_state_map[self.doc_id]['spelling_index'] < (self.ips.client_state_map[self.doc_id]['spelling_size'] - 1):
            orig_search_result = self.ips.client_state_map[self.doc_id]['spelling_results'][self.ips.client_state_map[self.doc_id]['spelling_index']]
            actions = self.ips.spellcheck_link(self.json_body,self.ips.client_state_map[self.doc_id])
            self.assertTrue(len(actions) == 3)
            self.assertTrue(actions[0]['action'] == 'linkText')

            for res in  self.ips.client_state_map[self.doc_id]['spelling_results']:
                if res['term'] == orig_search_result['term']:
                    self.assertTrue('prev_link' in res)
                    self.assertTrue(res['prev_link'] == testLink )


    def test_spellcheck_reuse_link(self):
        """
        Test Reuse Previous Link button
        """
        testLink = 'http://test-link.org'
        self.json_body['data'] = {}
        self.json_body['data']['buttonId'] = {}
        self.json_body['data']['buttonId']['link'] = testLink

        spelling_results = self.ips.client_state_map[self.doc_id]['spelling_results']
        result_len = self.ips.client_state_map[self.doc_id]['spelling_size']

        num_matching_results = len([r for r in spelling_results  if r['term'] == spelling_results[self.ips.client_state_map[self.doc_id]['spelling_index']]['term']])
        while self.ips.client_state_map[self.doc_id]['spelling_index'] < result_len and num_matching_results < 2:
            self.ips.client_state_map[self.doc_id]['spelling_index'] += 1

        if self.ips.client_state_map[self.doc_id]['spelling_index'] >= result_len:
            self.fail('Unable to find any results with more than one entry!')

        # Link a result
        orig_search_result = spelling_results[self.ips.client_state_map[self.doc_id]['spelling_index']]
        actions = self.ips.spellcheck_link(self.json_body, self.ips.client_state_map[self.doc_id])
        self.assertTrue(len(actions) == 3)
        self.assertTrue(actions[0]['action'] == 'linkText')

        for res in  self.ips.client_state_map[self.doc_id]['spelling_results']:
            if res['term'] == orig_search_result['term']:
                self.assertTrue('prev_link' in res)
                self.assertTrue(res['prev_link'] == testLink )

        # Find the next match index and set it
        index_next_match = self.ips.client_state_map[self.doc_id]['spelling_index']
        while index_next_match < result_len and not spelling_results[index_next_match]['term'] == orig_search_result['term']:
            index_next_match += 1
        self.ips.client_state_map[self.doc_id]['spelling_index'] = index_next_match

        actions = self.ips.spellcheck_reuse_link(self.json_body, self.ips.client_state_map[self.doc_id])
        expected_action_size = 3
        if self.ips.client_state_map[self.doc_id]['spelling_index'] == result_len:
            expected_action_size = 1

        self.assertTrue(len(actions) == expected_action_size)
        self.assertTrue(actions[0]['action'] == 'linkText')


    def tearDown(self):
        """
        Perform teardown.
        """
        self.ips.stop()


if __name__ == '__main__':
    print('Run unit tests')

    unittest.main(argv=[sys.argv[0]])
