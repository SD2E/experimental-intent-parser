from intent_parser.intent_parser_exceptions import IntentParserException, RequestErrorException
from http import HTTPStatus
import json
import opil
import sbol3
import re

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

