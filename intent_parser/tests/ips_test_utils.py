"""
Collecton of utility functions for the unit tests
"""
import intent_parser.utils.intent_parser_utils as table_utils

def get_currently_selected_text(testcase, ips, doc_id, doc_content):
    """
    Given select start and end dicts from spelling results, retrieve the text from the test document.
    """
    spelling_index = ips.client_state_map[doc_id]['spelling_index']
    spelling_result = ips.client_state_map[doc_id]['spelling_results'][spelling_index]
    select_start = spelling_result['select_start']
    select_end = spelling_result['select_end']

    if not select_start['paragraph_index'] == select_end['paragraph_index']:
        testcase.fail('Selection starting and ending paragraphs differ! Not supported!')

    paragraphs = ips.get_paragraphs(doc_content)
    paragraph = paragraphs[select_start['paragraph_index']]
    para_text = table_utils.get_paragraph_text(paragraph)
    return para_text[select_start['cursor_index']:(select_end['cursor_index'] + 1)]

def compare_search_results(r1, r2):
    """
    Compares two spellcheck search results to see if they are equal.
    r1 and r2 are lists of search results, where each result contains a term, selection start, and selection end.
    """
    if not len(r1) == len(r2):
        return False

    for idx in range(len(r1)):
        entry1 = r1[idx]
        entry2 = r2[idx]
        if not entry1['term'] == entry2['term']:
            return False
        if not entry1['paragraph_index'] == entry2['paragraph_index']:
            return False
        if not entry1['offset'] == entry2['offset']:
            return False
        if not entry1['end_offset'] == entry2['end_offset']:
            return False
        if not entry1['uri'] == entry2['uri']:
            return False
        if not entry1['link'] == entry2['link']:
            return False
        if not entry1['text'] == entry2['text']:
            return False
    return True

def compare_spell_results(r1, r2):
    """
    Compares two spellcheck search results to see if they are equal.
    r1 and r2 are lists of search results, where each result contains a term, selection start, and selection end.
    """
    if not len(r1) == len(r2):
        return False

    for idx in range(len(r1)):
        entry1 = r1[idx]
        entry2 = r2[idx]
        if not entry1['term'] == entry2['term']:
            return False
        if not entry1['select_start']['paragraph_index'] == entry2['select_start']['paragraph_index']:
            return False
        if not entry1['select_start']['cursor_index']    == entry2['select_start']['cursor_index']:
            return False
        if not entry1['select_start']['element_index']   == entry2['select_start']['element_index']:
            return False
        if not entry1['select_end']['paragraph_index'] == entry2['select_end']['paragraph_index']:
            return False
        if not entry1['select_end']['cursor_index']    == entry2['select_end']['cursor_index']:
            return False
        if not entry1['select_end']['element_index']   == entry2['select_end']['element_index']:
            return False

    return True