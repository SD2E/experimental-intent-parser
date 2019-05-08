import socket
import threading
import json
from socket_manager import SocketManager
from google_accessor import GoogleAccessor
import http_message;
import uuid
import traceback
import functools
import sbol
import sys
import getopt
import re
import time
from datetime import date
from datetime import datetime
from operator import itemgetter

class ConnectionException(Exception):
    def __init__(self, code, message, content=""):
        super(ConnectionException, self).__init__(message);
        self.code = code
        self.message = message
        self.content = content


class IntentParserServer:
    def __init__(self, *, bind_port=8080, bind_ip="0.0.0.0",
                 sbh_url, sbh_spoofing_prefix=None,
                 sbh_collection, sbh_collection_user='sd2e',
                 sbh_collection_version='1', spreadsheet_id,
                 sbh_username=None, sbh_password=None,
                 sbh_link_hosts=['hub-staging.sd2e.org',
                                 'hub.sd2e.org']):

        self.bind_port = bind_port
        self.bind_ip = bind_ip

        if sbh_url is not None:
            # log into Syn Bio Hub
            if sbh_username is None:
                print('SynBioHub username was not specified')
                usage()
                sys.exit(2)

            if sbh_password is None:
                print('SynBioHub password was not speficied')
                usage()
                sys.exit(2)

            self.sbh = sbol.PartShop(sbh_url)
            self.sbh_collection = sbh_collection
            self.sbh_spoofing_prefix = sbh_spoofing_prefix
            self.sbh_url = sbh_url
            self.sbh_link_hosts = sbh_link_hosts

            if sbh_spoofing_prefix is not None:
                self.sbh.spoof(sbh_spoofing_prefix)
                self.sbh_collection_uri = sbh_spoofing_prefix \
                    + '/user/' + sbh_collection_user \
                    + '/' + sbh_collection + '/' \
                    + sbh_collection + '_collection/' \
                    + sbh_collection_version
            else:
                self.sbh_collection_uri = sbh_url + '/'
                self.sbh_collection_uri = sbh_url \
                    + '/user/' + sbh_collection_user \
                    + '/' + sbh_collection + '/' \
                    + sbh_collection + '_collection/' \
                    + sbh_collection_version

            self.sbh_uri_prefix = sbh_url \
                + '/user/' + sbh_collection_user \
                + '/' + sbh_collection + '/'

            self.sbh.login(sbh_username, sbh_password)
            print('Logged into {}'.format(sbh_url))

        self.google_accessor = GoogleAccessor.create()
        self.spreadsheet_id = spreadsheet_id
        self.google_accessor.set_spreadsheet_id(self.spreadsheet_id)
        self.spreadsheet_tabs = self.google_accessor.type_tabs.keys()

        self.client_state_map = {}
        self.client_state_lock = threading.Lock()
        self.item_map = self.generate_item_map()

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((bind_ip, bind_port))
        self.server.listen(5)

        self.item_types = {
            'component': {
                'Bead'     : 'http://purl.obolibrary.org/obo/NCIT_C70671',
                'CHEBI'    : 'http://identifiers.org/chebi/CHEBI:24431',
                'DNA'      : 'http://www.biopax.org/release/biopax-level3.owl#DnaRegion',
                'Protein'  : 'http://www.biopax.org/release/biopax-level3.owl#Protein',
                'RNA'      : 'http://www.biopax.org/release/biopax-level3.owl#RnaRegion'
            },
            'module': {
                'Strain'   : 'http://purl.obolibrary.org/obo/NCIT_C14419',
                'Media'    : 'http://purl.obolibrary.org/obo/NCIT_C85504',
                'Stain'    : 'http://purl.obolibrary.org/obo/NCIT_C841',
                'Buffer'   : 'http://purl.obolibrary.org/obo/NCIT_C70815',
                'Solution' : 'http://purl.obolibrary.org/obo/NCIT_C70830'
            },
            'collection': {
                'Challenge Problem' : '',
                'Collection' : ''
            },
            'external': {
                'Attribute' : ''
            }
        }

        # Inverse map of typeTabs
        self.type2tab = {}
        for tab_name in self.google_accessor.type_tabs.keys():
            for type_name in self.google_accessor.type_tabs[tab_name]:
                self.type2tab[type_name] = tab_name

        self.lab_ids_list = sorted(['BioFAB UID',
                                    'Ginkgo UID',
                                    'Transcriptic UID',
                                    'LBNL UID',
                                    'EmeraldCloud UID'])

        f = open('add.html', 'r')
        self.add_html = f.read()
        f.close()

        f = open('findSimilar.sparql', 'r')
        self.sparql_query = f.read()
        f.close()

        print('listening on {}:{}'.format(bind_ip, bind_port))

    def serverRunLoop(self):
        while True:
            client_sock, address = self.server.accept()
            client_handler = threading.Thread(
                target=self.handle_client_connection,
                args=(client_sock,)  # without comma you'd get a... TypeError: handle_client_connection() argument after * must be a sequence, not _socketobject
            )
            client_handler.start()

    def handle_client_connection(self, client_socket):
        print('Connection')
        sm = SocketManager(client_socket)

        try:
            while True:
                httpMessage = http_message.HttpMessage(sm)

                if httpMessage.get_state() == http_message.State.ERROR:
                    client_socket.close()
                    return

                method = httpMessage.get_method()

                try:
                    if method == 'POST':
                        self.handlePOST(httpMessage, sm)
                    elif method == 'GET':
                        self.handleGET(httpMessage, sm)
                    else:
                        self.send_response(501, 'Not Implemented', 'Unrecognized request method\n',
                                           sm)

                except ConnectionException as ex:
                    self.send_response(ex.code, ex.message, ex.content, sm)

                except Exception as ex:
                    print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
                    self.send_response(504, 'Internal Server Error', 'Internal Server Error\n', sm)

        except Exception as e:
            print('Exception: {}'.format(e))

        client_socket.close()

    def send_response(self, code, message, content, sm, content_type='text/html'):
            response = http_message.HttpMessage()
            response.set_response_code(code, message)
            response.set_header('content-type', content_type)
            response.set_body(content.encode('utf-8'))
            response.send(sm)

    def handlePOST(self, httpMessage, sm):
        resource = httpMessage.get_resource()

        if resource == '/analyzeDocument':
            self.process_analyze_document(httpMessage, sm)
        elif resource == '/message':
            self.process_message(httpMessage, sm)
        elif resource == '/buttonClick':
            self.process_button_click(httpMessage, sm)
        elif resource == '/addToSynBioHub':
            self.process_add_to_syn_bio_hub(httpMessage, sm)
        elif resource == '/searchSynBioHub':
            self.process_search_syn_bio_hub(httpMessage, sm)
        elif resource == '/submitForm':
            self.process_submit_form(httpMessage, sm)
        else:
            self.send_response(404, 'Not Found', 'Resource Not Found\n', sm)

    def get_json_body(self, httpMessage):
        body = httpMessage.get_body()
        if body == None or len(body) == 0:
            errorMessage = 'No POST data\n'
            raise ConnectionException(400, 'Bad Request', errorMessage)

        bodyStr = body.decode('utf-8')

        try:
            return json.loads(bodyStr)
        except json.decoder.JSONDecodeError as e:
            errorMessage = 'Failed to decode JSON data: {}\n'.format(e);
            raise ConnectionException(400, 'Bad Request', errorMessage)

    def process_button_click(self, httpMessage, sm):
        (json_body, client_state) = self.get_client_state(httpMessage)

        if 'data' not in json_body:
            errorMessage = 'Missing data'
            raise ConnectionException(400, 'Bad Request', errorMessage)
        data = json_body['data']

        if 'buttonId' not in data:
            errorMessage = 'data missing buttonId'
            raise ConnectionException(400, 'Bad Request', errorMessage)
        buttonId = data['buttonId']

        method = getattr( self, buttonId )

        try:
            actionList = method(json_body, client_state)
            actions = {'actions': actionList}
            self.send_response(200, 'OK', json.dumps(actions), sm,
                               'application/json')
        except Exception as e:
            raise e
        finally:
            self.release_connection(client_state)

    def process_generate_report(self, httpMessage, sm):
        resource = httpMessage.get_resource()
        document_id = resource.split('?')[1]
        client_state = {}

        try:
            doc = self.google_accessor.get_document(
                document_id=document_id
                )
        except Exception as ex:
            print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
            raise ConnectionException('404', 'Not Found',
                                      'Failed to access document ' +
                                      document_id)

        text_runs = self.get_element_type(doc, 'textRun')
        text_runs = list(filter(lambda x: 'textStyle' in x,
                                text_runs))
        text_runs = list(filter(lambda x: 'link' in x['textStyle'],
                                text_runs))
        links_info = list(map(lambda x: (x['content'],
                                         x['textStyle']['link']),
                              text_runs))

        mapped_names = []
        term_map = {}
        for link_info in links_info:
            try:
                term = link_info[0].strip()
                url = link_info[1]['url']
                if len(term) == 0:
                    continue

                if term in term_map:
                    if term_map[term] == url:
                        continue

                url_host = url.split('/')[2]
                if url_host not in self.sbh_link_hosts:
                   continue

                term_map[term] = url
                mapped_name = {}
                mapped_name['label'] = term
                mapped_name['sbh_url'] = url
                mapped_names.append(mapped_name)
            except:
                continue

        client_state = {}
        client_state['doc'] = doc
        self.analyze_document(client_state, doc, 0)

        report = {}
        report['challenge_problem_id'] = 'undefined'
        report['experiment_reference_url'] = \
            'https://docs.google.com/document/d/' + document_id
        report['labs'] = []

        report['mapped_names'] = mapped_names

        self.send_response(200, 'OK', json.dumps(report), sm,
                           'application/json')

    def process_message(self, httpMessage, sm):
        json_body = self.get_json_body(httpMessage)
        if 'message' in json_body:
            print(json_body['message'])
        self.send_response(200, 'OK', '[]', sm,
                           'application/json')


    def get_client_state(self, httpMessage):
        json_body = self.get_json_body(httpMessage)

        if 'documentId' not in json_body:
            raise ConnectionException('400', 'Bad Request',
                                      'Missing documentId')
        document_id = json_body['documentId']

        try:
            client_state = self.get_connection(document_id)
        except:
            client_state = None

        return (json_body, client_state)

    def process_analyze_document(self, httpMessage, sm):
        json_body = self.get_json_body(httpMessage)

        if 'documentId' not in json_body:
            raise ConnectionException('400', 'Bad Request',
                                      'Missing documentId')
        document_id = json_body['documentId']

        try:
            doc = self.google_accessor.get_document(
                document_id=document_id
                )
        except Exception as ex:
            print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
            raise ConnectionException('404', 'Not Found',
                                      'Failed to access document ' +
                                      document_id)

        client_state = self.new_connection(document_id)
        client_state['doc'] = doc

        if 'data' in json_body:
            body = doc.get('body');
            doc_content = body.get('content')
            paragraphs = self.get_paragraphs(doc_content)

            data = json_body['data']
            paragraph_index = data['paragraphIndex']
            offset = data['offset']
            paragraph = paragraphs[ paragraph_index ]
            first_element = paragraph['elements'][0]
            paragraph_offset = first_element['startIndex']
            start_offset = paragraph_offset + offset
        else:
            start_offset = 0

        try:
            actionList = self.analyze_document(client_state, doc, start_offset)
            actions = {'actions': actionList}
            self.send_response(200, 'OK', json.dumps(actions), sm,
                               'application/json')

        except Exception as e:
            raise e

        finally:
            self.release_connection(client_state)

    def add_link(self, search_result):
        paragraph_index = search_result['paragraph_index']
        offset = search_result['offset']
        end_offset = search_result['end_offset'] - 1
        link = search_result['uri']
        search_result['link'] = link

        action = self.link_text(paragraph_index, offset,
                                end_offset, link)

        return [action]


    def report_search_results(self, client_state):
        while True:
            search_results = client_state['search_results']
            search_result_index = client_state['search_result_index']
            if search_result_index >= len(search_results):
                return []

            client_state['search_result_index'] += 1

            search_result = search_results[ search_result_index ]
            paragraph_index = search_result['paragraph_index']
            offset = search_result['offset']
            term = search_result['term']
            uri = search_result['uri']
            link = search_result['link']
            content_term = search_result['text']
            end_offset = offset + len(term) - 1

            actions = []

            if link is not None and link == self.item_map[term]:
                continue

            highlightTextAction = self.highlight_text(paragraph_index, offset,
                                                      end_offset)
            actions.append(highlightTextAction)

            html  = ''
            html += '<center>'
            html += 'Link ' + content_term + ' to ';
            html += '<a href=' + uri + ' target=_blank>'
            html += term + '</a> ?'
            html += '</center>'


            buttons = [('Yes', 'process_analyze_yes'),
                       ('No', 'process_analyze_no'),
                       ('Link All', 'process_link_all')]

            dialogAction = self.simple_sidebar_dialog(html, buttons)

            actions.append(dialogAction)

            return actions

    def get_paragraphs(self, element):
        return self.get_element_type(element, 'paragraph')

    def get_element_type(self, element, element_type):
        elements = []
        if type(element) is dict:
            for key in element:
                if key == element_type:
                    elements.append(element[key])

                elements += self.get_element_type(element[key],
                                                  element_type)

        elif type(element) is list:
            for entry in element:
                elements += self.get_element_type(entry,
                                                  element_type)

        return elements


    def fetch_spreadsheet_data(self):
        tab_data = {}
        for tab in self.spreadsheet_tabs:
            tab_data[tab] = self.google_accessor.get_row_data(tab=tab)
            print('Fetched data from tab ' + tab)

        return tab_data


    def analyze_document(self, client_state, doc, start_offset):
        body = doc.get('body');
        doc_content = body.get('content')
        paragraphs = self.get_paragraphs(doc_content)

        search_results = []

        itr = 0
        for term in self.item_map.keys():
            pos = start_offset
            while True:
                result = self.find_text(term, pos, paragraphs)
                if result is None:
                    break;

                search_results.append({ 'paragraph_index': result[0],
                                        'offset': result[1],
                                        'end_offset': result[1] + len(term),
                                        'term': term,
                                        'uri': self.item_map[term],
                                        'link': result[3],
                                        'text': result[4]})

                pos = result[2] + len(term)

        if len(search_results) == 0:
            return []

        search_results = sorted(search_results,
                                key=itemgetter('paragraph_index',
                                               'offset')
                                )

        client_state['search_results'] = search_results
        client_state['search_result_index'] = 0

        return self.report_search_results(client_state)

    def process_analyze_yes(self, json_body, client_state):
        search_results = client_state['search_results']
        search_result_index = client_state['search_result_index'] - 1
        search_result = search_results[search_result_index]

        actions = self.add_link(search_result);
        actions += self.report_search_results(client_state)
        return actions

    def process_analyze_no(self, json_body, client_state):
        return self.report_search_results(client_state)


    def process_link_all(self, json_body, client_state):
        search_results = client_state['search_results']
        search_result_index = client_state['search_result_index'] - 1
        search_result = search_results[search_result_index]
        term = search_result['term']
        term_search_results = list(filter(lambda x : x['term'] == term,
                                          search_results))

        actions = []

        for term_result in term_search_results:
            actions += self.add_link(term_result);

        actions += self.report_search_results(client_state)

        return actions


    def highlight_text(self, paragraph_index, offset, end_offset):
        highlight_text = {}
        highlight_text['action'] = 'highlightText'
        highlight_text['paragraph_index'] = paragraph_index
        highlight_text['offset'] = offset
        highlight_text['end_offset'] = end_offset

        return highlight_text

    def link_text(self, paragraph_index, offset, end_offset, url):
        link_text = {}
        link_text['action'] = 'linkText'
        link_text['paragraph_index'] = paragraph_index
        link_text['offset'] = offset
        link_text['end_offset'] = end_offset
        link_text['url'] = url

        return link_text

    def simple_sidebar_dialog(self, message, buttons):
        htmlMessage = '<script>\n\n'
        htmlMessage += 'function onSuccess() { \n\
                         google.script.host.close()\n\
                      }\n\n'
        for button in buttons:
            htmlMessage += 'function ' + button[1] + 'Click() {\n'
            htmlMessage += '  google.script.run.withSuccessHandler'
            htmlMessage += '(onSuccess).buttonClick(\''
            htmlMessage += button[1]  + '\')\n'
            htmlMessage += '}\n\n'
        htmlMessage += '</script>\n\n'

        htmlMessage += '<p>' + message + '<p>\n'
        htmlMessage += '<center>'
        for button in buttons:
            htmlMessage += '<input id=' + button[1] + 'Button value="'
            htmlMessage += button[0] + '" type="button" onclick="'
            htmlMessage += button[1] + 'Click()" />\n'
        htmlMessage += '</center>'

        action = {}
        action['action'] = 'showSidebar'
        action['html'] = htmlMessage

        return action

    def simple_modal_dialog(self, message, buttons, title, width, height):
        htmlMessage = '<script>\n\n'
        htmlMessage += 'function onSuccess() { \n\
                         google.script.host.close()\n\
                      }\n\n'
        for button in buttons:
            htmlMessage += 'function ' + button[1] + 'Click() {\n'
            htmlMessage += '  google.script.run.withSuccessHandler'
            htmlMessage += '(onSuccess).buttonClick(\''
            htmlMessage += button[1]  + '\')\n'
            htmlMessage += '}\n\n'
        htmlMessage += '</script>\n\n'

        htmlMessage += '<p>' + message + '<p>\n'
        htmlMessage += '<center>'
        for button in buttons:
            htmlMessage += '<input id=' + button[1] + 'Button value="'
            htmlMessage += button[0] + '" type="button" onclick="'
            htmlMessage += button[1] + 'Click()" />\n'
        htmlMessage += '</center>'

        return self.modal_dialog(htmlMessage, title, width, height)

        return action

    def modal_dialog(self, html, title, width, height):
        action = {}
        action['action'] = 'showModalDialog'
        action['html'] = html
        action['title'] = title
        action['width'] = width
        action['height'] = height

        return action

    def get_paragraph_text(self, paragraph):
        elements = paragraph['elements']
        paragraph_text = '';

        for element_index in range( len(elements) ):
            element = elements[ element_index ]

            if 'textRun' not in element:
                continue
            text_run = element['textRun']

            end_index = element['endIndex']
            start_index = element['startIndex']

            paragraph_text += text_run['content']

        return paragraph_text

    def find_text(self, text, starting_pos, paragraphs):
        elements = []

        for paragraph_index in range( len(paragraphs )):
            paragraph = paragraphs[ paragraph_index ]
            elements = paragraph['elements']

            for element_index in range( len(elements) ):
                element = elements[ element_index ]

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

                # Check for whitespece before found text
                if offset > 0 and content[offset-1].isalpha():
                    continue

                # Check for whitespece after found text
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

    def handleGET(self, httpMessage, sm):
        resource = httpMessage.get_path()

        if resource == "/status":
            self.send_response(200, 'OK', 'Intent Parser Server is Up and Running\n', sm)
        elif resource == '/document_report':
            self.process_generate_report(httpMessage, sm)
        else:
            print('Did not find ' + resource)
            raise ConnectionException(404, 'Not Found', 'Resource Not Found')

    def new_connection(self, document_id):
        self.client_state_lock.acquire()
        if document_id in self.client_state_map:
            if self.client_state_map[document_id]['locked']:
                self.client_state_lock.release()
                raise ConnectionException(503, 'Service Unavailable',
                                          'This document is busy')

        client_state = {}
        client_state['document_id'] = document_id
        client_state['locked'] = True

        self.client_state_map[document_id] = client_state

        self.client_state_lock.release()

        return client_state

    def get_connection(self, document_id):
        self.client_state_lock.acquire()
        if document_id not in self.client_state_map:
            self.client_state_lock.release()
            raise ConnectionException(404, 'Bad Request',
                                      'Invalid session')

        client_state = self.client_state_map[document_id]

        if client_state['locked']:
            self.client_state_lock.release()
            raise ConnectionException(503, 'Service Unavailable',
                                      'This document is busy')
        client_state['locked'] = True
        self.client_state_lock.release()

        return client_state

    def release_connection(self, client_state):
        if client_state is None:
            return

        self.client_state_lock.acquire()

        document_id = client_state['document_id']

        if document_id in self.client_state_map:
            client_state = self.client_state_map[document_id]
            client_state['locked'] = False

        self.client_state_lock.release()

    def generate_item_map(self):
        item_map = {}

        try:
            f = open('item-map.json', 'r')
            item_map = json.loads(f.read())
            return item_map

        except:
            pass

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
                item_map[common_name] = uri

        f = open('item-map.json', 'w')
        f.write(json.dumps(item_map))
        f.close()

        return item_map

    def generate_html_options(self, options):
        options_html = ''
        for item_type in options:
            options_html += '          '
            options_html += '<option>'
            options_html += item_type
            options_html += '</option>\n'

        return options_html

    def generate_existing_link_html(self, title, target):
        html  = '<tr>'
        html += '  <td style="max-width: 250px; word-wrap: break-word;">'
        html += '    <a href=' + target + ' target=_blank name="theLink">' + title + '</a>'
        html += '  </td>'
        html += '  <td>'
        html += '    <input type="button" name=' + target + ' value="Link"'
        html += '    onclick="linkItem(thisForm, this.name)">'
        html += '  </td>'
        html += '  <td>'
        html += '    <input type="button" name=' + target + ' value="Link All"'
        html += '    onclick="linkAll(thisForm, this.name)">'
        html += '  </td>'
        html += '</tr>'

        return html

    def process_add_to_syn_bio_hub(self, httpMessage, sm):
        try:
            json_body = self.get_json_body(httpMessage)

            data = json_body['data']
            start = data['start']
            end = data['end']
            document_id = json_body['documentId']

            item_type_list = []
            for sbol_type in self.item_types:
                item_type_list += self.item_types[sbol_type].keys()

            item_type_list = sorted(item_type_list)
            item_types_html = self.generate_html_options(item_type_list)

            lab_ids_html = self.generate_html_options(self.lab_ids_list)

            try:
                doc = self.google_accessor.get_document(
                    document_id=document_id
                )
            except Exception as ex:
                print(''.join(traceback.format_exception(etype=type(ex),
                                                         value=ex,
                                                         tb=ex.__traceback__)))
                raise ConnectionException('404', 'Not Found',
                                          'Failed to access document ' +
                                          document_id)

            body = doc.get('body');
            doc_content = body.get('content')
            paragraphs = self.get_paragraphs(doc_content)
            start_paragraph = start['paragraphIndex'];
            end_paragraph = end['paragraphIndex'];
            paragraph_text = self.get_paragraph_text(
                paragraphs[start_paragraph])

            start_offset = start['offset']
            end_offset = end['offset'] + 1
            selection = paragraph_text[start_offset:end_offset]
            display_id = self.sanitize_name_to_display_id(selection)

            html = self.add_html

            # Update parameters in html
            html = html.replace('${COMMONNAME}', selection)
            html = html.replace('${DISPLAYID}', display_id)
            html = html.replace('${STARTPARAGRAPH}', str(start_paragraph))
            html = html.replace('${STARTOFFSET}', str(start_offset))
            html = html.replace('${ENDPARAGRAPH}', str(end_paragraph))
            html = html.replace('${ENDOFFSET}', str(end_offset))
            html = html.replace('${ITEMTYPEOPTIONS}', item_types_html)
            html = html.replace('${LABIDSOPTIONS}', lab_ids_html)
            html = html.replace('${SELECTEDTERM}', selection)
            html = html.replace('${DOCUMENTID}', document_id)

            dialog_action = self.modal_dialog(html, 'Add to SynBioHub',
                                              400, 450)
            actionList = [dialog_action]
            actions = {'actions': actionList}

            self.send_response(200, 'OK', json.dumps(actions), sm,
                               'application/json')
        except Exception as e:
            raise e

    def simple_syn_bio_hub_search(self, term):
        sparql_query = self.sparql_query.replace('${TERM}', term)
        query_results = self.sbh.sparqlQuery(sparql_query)
        bindings = query_results['results']['bindings']

        search_results = []
        for binding in bindings:
            title = binding['title']['value']
            target = binding['member']['value']
            if self.sbh_spoofing_prefix is not None:
                target = target.replace(self.sbh_spoofing_prefix, self.sbh_url)
            search_results.append({'title': title, 'target': target})


        return search_results

    def sanitize_name_to_display_id(self, name):
        displayIDfirstChar = '[a-zA-Z_]'
        displayIDlaterChar = '[a-zA-Z0-9_]'

        sanitized = ''
        for i in range(len(name)):
            character = name[i]
            if i==0:
                if re.match(displayIDfirstChar, character):
                    sanitized += character
                else:
                    sanitized += '_' # avoid starting with a number
                    if re.match(displayIDlaterChar, character):
                        sanitized += character
                    else:
                        sanitized += '0x{:x}'.format(ord(character))
            else:
                if re.match(displayIDlaterChar, character):
                    sanitized += character;
                else:
                    sanitized += '0x{:x}'.format(ord(character))

        return sanitized

    def set_item_properties(self, entity, data):
        item_type = data['itemType']
        item_name = data['commonName']
        item_definition_uri = data['definitionURI']
        item_lab_ids = data['labId']

        sbol.TextProperty(entity, 'http://purl.org/dc/terms/title', '0', '1',
                          item_name)

        time_stamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S-00')
        sbol.TextProperty(entity, 'http://purl.org/dc/terms/created', '0', '1',
                          time_stamp)
        sbol.TextProperty(entity, 'http://purl.org/dc/terms/modified', '0', '1',
                          time_stamp)

        if item_type in self.item_types['collection']:
            return

        if len(item_definition_uri) > 0:
            if item_type == 'CHEBI':
                if not item_definition_uri.startswith('http://identifiers.org/chebi/CHEBI'):
                    item_definition_uri = 'http://identifiers.org/chebi/CHEBI:' + \
                        item_definition_uri
            else:
                sbol.URIProperty(entity, 'http://www.w3.org/ns/prov#wasDerivedFrom',
                                 '0', '1', item_definition_uri)

        if len(item_lab_ids) > 0:
            lab_id_tag = data['labIdSelect'].replace(' ', '_')
            tp = None
            for item_lab_id in item_lab_ids.split(','):
                if tp is None:
                    tp = sbol.TextProperty(entity, 'http://sd2e.org#' + lab_id_tag, '0', '1',
                                           item_lab_id)
                else:
                    tp.add(item_lab_id)

    def operation_failed(self, message):
        return {'results': {'operationSucceeded': False,
                            'message': message}
        }

    def create_dictionary_entry(self, data, document_url, item_definition_uri):
        item_type = data['itemType']
        item_name = data['commonName']
        item_lab_ids = data['labId']
        item_lab_id_tag = data['labIdSelect']

        sbh_uri_prefix = self.sbh_uri_prefix
        if self.sbh_spoofing_prefix is not None:
            item_uri = document_url.replace(self.sbh_url,
                                            self.sbh_spoofing_prefix)
        else:
            item_uri = document_url

        tab_name = self.type2tab[item_type]

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

    def create_sbh_stub(self, data):
        # Extract some fields from the form
        try:
            item_type = data['itemType']
            item_name = data['commonName']
            item_definition_uri = data['definitionURI']
            item_display_id = data['displayId']

        except Exception as e:
            return self.operation_failed('Form sumission missing key: ' + str(e))

        # Make sure Common Name was specified
        if len(item_name) == 0:
            return self.operation_failed('Common Name must be specified')

        # Sanitize the display id
        if len(item_display_id) > 0:
             display_id = self.sanitize_name_to_display_id(item_display_id)
             if display_id != item_display_id:
                 return self.operation_failed('Illegal display_id')
        else:
            display_id = self.sanitize_name_to_display_id(item_name)

        # Derive document URL
        document_url = self.sbh_uri_prefix + display_id + '/1'

        # Make sure document does not already exist
        try:
            if self.sbh.exists(document_url):
                return self.operation_failed('"' + display_id +
                                             '" already exists in SynBioHub')
        except:
            return self.operation_failed('Failed to access SynBioHub')

        # Look up sbol type uri
        sbol_type = None
        for sbol_type_key in self.item_types:
            sbol_type_map = self.item_types[ sbol_type_key ]
            if item_type in sbol_type_map:
                sbol_type = sbol_type_key
                break;

        # Fix CHEBI URI
        if item_type == 'CHEBI':
            if len(item_definition_uri) == 0:
                 item_definition_uri = sbol_type_map[ item_type ]
            else:
                if not item_definition_uri.startswith('http://identifiers.org/chebi/CHEBI'):
                    item_definition_uri = 'http://identifiers.org/chebi/CHEBI:' + \
                        item_definition_uri

        # Create a dictionary entry for the item
        try:
            self.create_dictionary_entry(data, document_url, item_definition_uri)

        except Exception as e:
            return self.operation_failed(str(e))

        # Create an entry in SynBioHub
        try:
            document = sbol.Document()
            document.addNamespace('http://sd2e.org#', 'sd2')
            document.addNamespace('http://purl.org/dc/terms/', 'dcterms')
            document.addNamespace('http://www.w3.org/ns/prov#', 'prov')

            if sbol_type == 'component':
                if item_type == 'CHEBI':
                    item_sbol_type = item_definition_uri
                else:
                    item_sbol_type = sbol_type_map[ item_type ]

                component = sbol.ComponentDefinition(display_id, item_sbol_type)

                sbol.TextProperty(component, 'http://sd2e.org#stub_object', '0', '1', 'true')
                self.set_item_properties(component, data)

                document.addComponentDefinition(component)

            elif sbol_type == 'module':
                module = sbol.ModuleDefinition(display_id)
                sbol.TextProperty(module, 'http://sd2e.org#stub_object', '0', '1', 'true')

                module.roles = sbol_type_map[ item_type ]
                self.set_item_properties(module, data)

                document.addModuleDefinition(module)

            elif sbol_type == 'external':
                top_level = sbol.TopLevel('http://http://sd2e.org/types/#attribute', display_id)
                self.set_item_properties(top_level, data)

                document.addTopLevel(top_level)

            elif sbol_type == 'collection':
                collection = sbol.Collection(display_id)
                self.set_item_properties(collection, data)
                document.addCollection(collection)

            else:
                raise Exception()

            self.sbh.submit(document, self.sbh_collection_uri, 3)

            paragraph_index = data['selectionStartParagraph']
            offset = data['selectionStartOffset']
            end_offset = data['selectionEndOffset']

            action = self.link_text(paragraph_index, offset,
                                    end_offset, document_url)

        except Exception as e:
            print(''.join(traceback.format_exception(etype=type(e),
                                                     value=e,
                                                     tb=e.__traceback__)))

            message = 'Failed to add "' + display_id + '" to SynBioHub'
            return self.operation_failed(message)

        return_info = {'actions': [action],
                       'results': {'operationSucceeded': True}
                      }

        return return_info

    def process_nop(self, httpMessage, sm):
        return []

    def process_submit_form(self, httpMessage, sm):
        json_body = self.get_json_body(httpMessage)
        data = json_body['data']
        action = data['extra']['action']

        result = {}

        if action == 'submit':
            result = self.create_sbh_stub(data)

        elif action == 'link':
            search_result = \
                {'paragraph_index' : data['selectionStartParagraph'],
                 'offset'          : int(data['selectionStartOffset']),
                 'end_offset'      : int(data['selectionEndOffset']),
                 'uri'             : data['extra']['link']
                }
            actions = self.add_link(search_result)
            result = {'actions': actions,
                      'results': {'operationSucceeded': True}
            }

        elif action == 'linkAll':
            actions = self.process_form_link_all(data)
            result = {'actions': actions,
                      'results': {'operationSucceeded': True}
            }

        else:
            print('Unsupported form action: {}'.format(action))

        self.send_response(200, 'OK', json.dumps(result), sm,
                           'application/json')


    def process_form_link_all(self, data):
        document_id = data['documentId']
        doc = self.google_accessor.get_document(
            document_id=document_id
        )
        body = doc.get('body');
        doc_content = body.get('content')
        paragraphs = self.get_paragraphs(doc_content)
        selected_term = data['selectedTerm']
        uri = data['extra']['link']

        actions = []
        search_results = []
        pos = 0
        while True:
            result = self.find_text(selected_term, pos, paragraphs)

            if result is None:
                break

            search_result = { 'paragraph_index' : result[0],
                              'offset'          : result[1],
                              'end_offset'      : result[1] + len(selected_term),
                              'term'            : selected_term,
                              'uri'             : uri,
                              'link'            : result[3],
                              'text'            : result[4]}

            actions += self.add_link(search_result)

            pos = result[2] + len(selected_term)

        return actions

    def process_search_syn_bio_hub(self, httpMessage, sm):
        json_body = self.get_json_body(httpMessage)
        data = json_body['data']

        try:
            search_results = self.simple_syn_bio_hub_search(data['term'])

            if len(search_results) > 5:
                search_results = search_results[0:5]

            table_html = ''
            for search_result in search_results:
                title = search_result['title']
                target = search_result['target']
                table_html += self.generate_existing_link_html(title,
                                                               target)

            response = {'results':
                        {'operationSucceeded': True,
                         'search_results': search_results,
                         'table_html': table_html
                        }}
        except:
            response = self.operation_failed('Failed to search SynBioHub')

        self.send_response(200, 'OK', json.dumps(response), sm,
                           'application/json')

spreadsheet_id = '1wHX8etUZFMrvmsjvdhAGEVU1lYgjbuRX5mmYlKv7kdk'
sbh_spoofing_prefix=None
sbh_collection_uri = 'https://hub-staging.sd2e.org/user/sd2e/intent_parser/intent_parser_collection/1'

def usage():
    print('')
    print('intent_parser_server.py: [options]')
    print('')
    print('    -h --help            - show this message')
    print('    -p --pasword         - SynBioHub password')
    print('    -u --username        - SynBioHub username')
    print('    -c --collection      - collection url (default={})'. \
          format(sbh_collection_uri))
    print('    -i --spreadsheet-id  - dictionary spreadsheet id (default={})'. \
          format(spreadsheet_id))
    print('    -s --spoofing-prefix - SBH spoofing prefix (default={})'.
          format(sbh_spoofing_prefix))
    print('')

def main(argv):
    sbh_username = None
    sbh_password = None

    global spreadsheet_id
    global sbh_spoofing_prefix
    global sbh_collection_uri

    try:
        opts, args = getopt.getopt(argv, "u:p:hc:i:s:",
                                   ["username=",
                                    "password=",
                                    "help",
                                    "collection=",
                                    "spreadsheet-id=",
                                    "spoofing-prefix="])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2);

    for opt,arg in opts:
        if opt in ('-u', '--username'):
            sbh_username = arg

        elif opt in ('-p', '--password'):
            sbh_password = arg

        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)

        elif opt in ('-c', '--collection'):
            sbh_collection_uri = arg

        elif opt in ('-i', '--spreadsheet-id'):
            spreadsheet_id = arg

        elif opt in ('-s', '--spoofing-prefix'):
            sbh_spoofing_prefix = arg

    if sbh_collection_uri[:8] == 'https://':
        sbh_url_protocol = 'https://'
        sbh_collection_path = sbh_collection_uri[8:]

    elif sbh_collection_uri[:7] == 'http://':
        sbh_url_protocol = 'http://'
        sbh_collection_path = sbh_collection_uri[7:]

    else:
        print('Invalid collection url: ' + sbh_collection_uri);
        usage();
        sys.exit(3)

    sbh_collection_path_parts = sbh_collection_path.split('/')
    if len(sbh_collection_path_parts) != 6:
        print('Invalid collection url: ' + sbh_collection_uri);
        usage()
        sys.exit(4)

    sbh_collection = sbh_collection_path_parts[3]
    sbh_collection_user = sbh_collection_path_parts[2]
    sbh_collection_version = sbh_collection_path_parts[5]
    sbh_url = sbh_url_protocol + sbh_collection_path_parts[0]

    if sbh_collection_path_parts[4] != (sbh_collection + '_collection'):
        print('Invalid collection url: ' + sbh_collection_uri);
        usage()
        sys.exit(5)

    sbhPlugin = IntentParserServer(sbh_url=sbh_url,
                                   sbh_spoofing_prefix=sbh_spoofing_prefix,
                                   sbh_collection=sbh_collection,
                                   sbh_collection_user=sbh_collection_user,
                                   sbh_collection_version=sbh_collection_version,
                                   sbh_username=sbh_username,
                                   sbh_password=sbh_password,
                                   spreadsheet_id=spreadsheet_id)
    sbhPlugin.serverRunLoop()


if __name__ == "__main__":
    main(sys.argv[1:])
