from collections import namedtuple as _namedtuple
from intent_parser.intent_parser_exceptions import RequestErrorException
from difflib import Match
from http import HTTPStatus
import json
import Levenshtein
import re

IPSMatch = _namedtuple('Match', 'a b size content_word_length')

def get_google_doc_id(doc_url):
    url_pattern = 'https://docs.google.com/document/d/(?P<id>[^//]+)'
    matched_pattern = re.match(url_pattern, doc_url)
    doc_id = matched_pattern.group('id')
    return doc_id

def load_json_file(file_path):
    with open(file_path, 'r') as file:
        json_data = json.load(file)
        return json_data

def load_file(file_path):
    with open(file_path, 'r') as file:
        f = file.read()
        return f

def write_json_to_file(data, file_path):
    with open(file_path, 'w') as outfile:
        json.dump(data, outfile)

def char_is_not_wordpart(ch):
    """ Determines if a character is part of a word or not
    This is used when parsing the text to tokenize words.
    """
    return ch is not '\'' and not ch.isalnum()

def should_ignore_token(word):
    """ Determines if a token/word should be ignored
    For example, if a token contains no alphabet characters, we should ignore it.
    """

    contains_alpha = False
    # This was way too slow
    #term_exists_in_sbh = len(self.simple_syn_bio_hub_search(word)) > 0
    term_exists_in_sbh = False
    for ch in word:
        contains_alpha |= ch.isalpha()

    return not contains_alpha  or term_exists_in_sbh

def strip_leading_trailing_punctuation(word):
    """ Remove any leading of trailing punctuation (non-alphanumeric characters
    """
    start_index = 0
    end_index = len(word)
    while start_index < len(word) and not word[start_index].isalnum():
        start_index += 1
    while end_index > 0 and not word[end_index - 1].isalnum():
        end_index -= 1

    # If the word was only non-alphanumeric, we could get into a strange case
    if end_index <= start_index:
        return ''
    else:
        return word[start_index:end_index]

def get_paragraph_text(paragraph):
    elements = paragraph['elements']
    paragraph_text = ''

    for element_index in range(len(elements)):
        element = elements[element_index]

        if 'textRun' not in element:
            continue
        text_run = element['textRun']
        paragraph_text += text_run['content']

    return paragraph_text

def cull_overlapping(search_results):
    """
    Find any results that overlap and take the one with the largest term.
    """
    new_results = []
    ignore_idx = set()
    for idx in range(0, len(search_results)):
        overlaps, max_idx, overlap_idx = find_overlaps(idx, search_results)
        if len(overlaps) > 1:
            if max_idx not in ignore_idx:
                new_results.append(search_results[max_idx])
            ignore_idx = ignore_idx.union(overlap_idx)
        else:
            if idx not in ignore_idx:
                new_results.append(search_results[idx])
    return new_results

def get_document_id_from_json_body(json_body):
    if 'documentId' not in json_body:
        raise RequestErrorException(HTTPStatus.BAD_REQUEST, errors=['Missing documentId'])
    return json_body['documentId']

def get_element_type(element, element_type):
    elements = []
    if type(element) is dict:
        for key in element:
            if key == element_type:
                elements.append(element[key])

            elements += get_element_type(element[key], element_type)

    elif type(element) is list:
        for entry in element:
            elements += get_element_type(entry, element_type)

    return elements

def analyze_term(entry):
    term = entry[0]
    start_offset = entry[1]
    paragraphs = entry[2]
    partial_match_min_size = entry[3]
    partial_match_thresh = entry[4]
    uri = entry[5]
    results = find_text(term, start_offset, paragraphs, partial_match_min_size, partial_match_thresh)
    search_results = []
    for result in results:
        search_results.append(
            {'paragraph_index': result[0],
             'offset': result[1],
             'end_offset': result[2],
             'term': term,
             'uri': uri,
             'link': result[3],
             'text': result[4]})
    return search_results

def find_exact_text(text, starting_pos, paragraphs):
    """
    Search through the whole document, beginning at starting_pos and return the first exact match to text.
    """
    elements = []

    for paragraph_index in range(len(paragraphs)):
        paragraph = paragraphs[ paragraph_index]
        elements = paragraph['elements']

        for element_index in range(len(elements)):
            element = elements[element_index]

            if 'textRun' not in element:
                continue
            text_run = element['textRun']

            end_index = element['endIndex']
            if end_index < starting_pos:
                continue

            start_index = element['startIndex']
            if start_index < starting_pos:
                find_start = starting_pos - start_index
            else:
                find_start = 0

            content = text_run['content']
            offset = content.lower().find(text.lower(), find_start)

            # Check for whitespace before found text
            if offset > 0 and content[offset-1].isalpha():
                continue

            # Check for whitespace after found text
            next_offset = offset + len(text)
            if next_offset < len(content) and content[next_offset].isalpha():
                continue

            if offset < 0:
                continue

            content_text = content[offset:(offset+len(text))]

            first_index = elements[0]['startIndex']
            offset += start_index - first_index

            link = None

            if 'textStyle' in text_run:
                text_style = text_run['textStyle']
                if 'link' in text_style:
                    link = text_style['link']
                    if 'url' in link:
                        link = link['url']

            pos = first_index + offset
            return (paragraph_index, offset, pos, link,
                    content_text)

    return None

def find_text(text, abs_start_offset, paragraphs, partial_match_min_size, partial_match_thresh):
    """
    Search through the whole document and return a collection of matches, including partial, to the search term.
    """
    results = []
    for paragraph_index in range( len(paragraphs )):
        paragraph = paragraphs[ paragraph_index ]
        elements = paragraph['elements']

        for element_index in range( len(elements) ):
            element = elements[ element_index ]

            if 'textRun' not in element:
                continue
            text_run = element['textRun']

            # Don't start the search until after the starting position
            end_index = element['endIndex']
            if end_index < abs_start_offset:
                continue

            start_index = element['startIndex']
            content = text_run['content']

            # Trim off content if it starts after the starting position
            start_offset = max(0,abs_start_offset - start_index)
            if start_offset > 0:
                content = content[start_offset:]

            matches = find_common_substrings(content.lower(), text.lower(), partial_match_min_size, partial_match_thresh)
            for match in matches:
                # Need to exceed partial match threshold - content word length
                if match.size < int(match.content_word_length * partial_match_thresh):
                    continue

                # Need to exceed partial match threshold - dictionary term length
                if match.size < int(len(text) * partial_match_thresh):
                    continue

                offset = match.a

                # Require whitespace before found text
                if offset > 0 and content[offset-1].isalpha():
                    continue

                # Require whitespace after found text
                next_offset = offset + match.size
                if next_offset < len(content) and content[next_offset].isalpha():
                    continue

                content_text = content[offset:(offset + match.size)]

                first_index = elements[0]['startIndex']
                offset += (start_index + start_offset) - first_index

                link = None

                if 'textStyle' in text_run:
                    text_style = text_run['textStyle']
                    if 'link' in text_style:
                        link = text_style['link']
                        if 'url' in link:
                            link = link['url']

                # If the text is linked, we must have an exact match, otherwise ignore
                if link is not None and (not match.size == len(content) or not match.size == len(text)):
                    continue

                results.append((paragraph_index, offset, offset + match.size - 1, link, content_text))
    return results

def find_common_substrings(content, dict_term, partial_match_min_size, partial_match_thresh):
    """
    Scan dict_term finding any common substrings from dict_term.  For each possible common substring, only the first one is found.
    """
    results = []
    len_content = len(content)
    len_term = len(dict_term)
    i = 0
    while i < len_content:
        match_start = -1
        matched_chars = 0
        # Ignore white space
        if content[i].isspace():
            i += 1
            continue;
        match = None
        for j in range(len_term):
            char_match = (i + matched_chars < len_content and content[i + matched_chars] == dict_term[j])
            if char_match and match_start == -1:
                match_start = j
            elif match_start > -1 and not char_match:
                match = Match(i, match_start, j - match_start)
                break
            if char_match:
                matched_chars += 1
        # Check for match at the end
        if match is None and match_start > -1:
            match = Match(i, match_start, len_term - match_start)
        # Process content match
        if not match is None:
            # Ignore matches if they aren't big enough
            # No partial matches for small terms
            if len_term <= partial_match_min_size:
                if match.size >= len_term:
                    results.append(match)
            # If the term is larger, we can have content partial match
            elif match.size >= int(len_term * partial_match_thresh):
                results.append(match)
            i += match.size
        else:
            i += 1

    # Compute word length for matched substrings
    # The word is terminated by whitespace, or /, unless the character in question is also present in the dictionary term at the same location
    results_mod = []
    for res in results:
        start_idx = res.a
        start_idx_b = res.b
        while (start_idx > 0 and (content[start_idx - 1].isalpha() or content[start_idx - 1] == '_')) or (start_idx > 0 and start_idx_b > 0 and content[start_idx - 1] == dict_term[start_idx_b - 1]):
            start_idx -= 1
            start_idx_b -= 1
        end_idx = res.a
        end_idx_b = res.b
        while (end_idx < len_content and (content[end_idx].isalpha() or content[end_idx] == '_')) or (end_idx < len_content and end_idx_b < len_term and content[end_idx] == dict_term[end_idx_b]):
            end_idx += 1
            end_idx_b += 1
        content_word_length = end_idx - start_idx
        results_mod.append(IPSMatch(res.a, res.b, res.size, content_word_length))
    return results_mod


def find_overlaps(start_idx, search_results, ignore_idx=set()):
    """
    Given a start index, find any entries in the results that overlap with the result at the start index
    In the case where the amount of overlap is equal, we pick the one that has the lowest Levenshtein (edit) distance between the matched text and the dictionary term.
    """
    query = search_results[start_idx]
    overlaps = [query]
    overlap_idx = [start_idx]
    best_overlap_idx = start_idx
    best_overlap_len = query['end_offset'] - query['offset']
    best_edit_dist = Levenshtein.distance(query['term'], query['text'])
    for idx in range(start_idx + 1, len(search_results)):

        if idx in ignore_idx:
            continue
        comp = search_results[idx]

        if not comp['paragraph_index'] == query['paragraph_index']:
            continue
        overlap = max(0, min(comp['end_offset'], query['end_offset']) - max(comp['offset'], query['offset'])) > 0
        if overlap:
            overlaps.append(comp)
            overlap_idx.append(idx)
            dist = Levenshtein.distance(comp['term'], comp['text'])
            overlap_amount = comp['end_offset'] - comp['offset']
            if overlap_amount >= best_overlap_len or (overlap_amount == best_overlap_len and dist < best_edit_dist):
                best_overlap_idx = idx
                best_overlap_len = dist

    return overlaps, best_overlap_idx, overlap_idx

