from collections import namedtuple as _namedtuple
from intent_parser.intent_parser_exceptions import IntentParserException, RequestErrorException
from difflib import Match
from http import HTTPStatus
import json
import opil
import sbol3
import re

IPSMatch = _namedtuple('Match', 'a b size content_word_length')

def get_google_doc_id(doc_url):
    url_pattern = 'https://docs.google.com/document/d/(?P<id>[^//]+)'
    matched_pattern = re.match(url_pattern, doc_url)
    doc_id = matched_pattern.group('id')
    return doc_id

def load_opil_xml_file(file_path):
    opil_doc = opil.Document()
    try:
        opil_doc.read(file_path, sbol3.RDF_XML)
    except ValueError:
        raise IntentParserException('Unable to load sbol file.')
    return opil_doc

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