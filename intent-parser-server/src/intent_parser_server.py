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
                 sbh_username=None, sbh_password=None):

        self.bind_port = bind_port
        self.bind_ip = bind_ip

        if sbh_url is not None:
            # log into Syn Bio Hub
            if sbh_username is None:
                raise Exception('SBH username was not specified')

            if sbh_password is None:
                raise Exception('SBH password was not speficied')

            self.sbh = sbol.PartShop(sbh_url)
            self.sbh_collection = sbh_collection
            self.sbh_spoofing_prefix = sbh_spoofing_prefix
            self.sbh_url = sbh_url

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

        client_state = {}
        client_state['doc'] = doc
        self.analyze_document(client_state, doc, 0)

        report = {}
        terms = []
        search_results = client_state['search_results']
        for search_result in search_results:
            term = {}
            term['term'] = search_result['term']
            terms.append(term)

        report['terms'] = terms

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
        paragraphs = []
        if type(element) is dict:
            for key in element:
                if key == 'paragraph':
                    paragraphs.append(element[key])

                paragraphs += self.get_paragraphs(element[key])

        elif type(element) is list:
            for entry in element:
                paragraphs += self.get_paragraphs(entry)

        return paragraphs


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

        f = open('item-map.json', 'r')
        item_map = json.loads(f.read())
        return item_map

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

        #f = open('item-map.json', 'w')
        #f.write(json.dumps(item_map))
        #f.close()
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

            html = self.add_html

            # Update parameters in html
            html = html.replace('${COMMONNAME}', selection)
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
        # TODO
        return name

    def set_item_properties(self, entity, data):
        item_type = data['itemType']
        item_title = data['title']
        item_definition_uri = data['definitionURI']
        item_lab_ids = data['labId']

        if len(item_title):
            sbol.TextProperty(entity, 'http://purl.org/dc/terms/title', '0', '1',
                              item_title)

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

    def create_sbh_stub(self, data):
        item_type = data['itemType']
        item_name = data['commonName']
        item_title = data['title']
        item_definition_uri = data['definitionURI']

        display_id = self.sanitize_name_to_display_id(item_name)
        document_url = self.sbh_uri_prefix + display_id + '/1'

        if self.sbh.exists(document_url):
            return {'results': {'operationSucceeded': False,
                                'message': display_id + ' already exists in SynBioHub'}
                    }

        try:
            document = sbol.Document()
            document.addNamespace('http://sd2e.org#', 'sd2')
            document.addNamespace('http://purl.org/dc/terms/', 'dcterms')
            document.addNamespace('http://www.w3.org/ns/prov#', 'prov')

            sbol_type = None
            for sbol_type_key in self.item_types:
                sbol_type_map = self.item_types[ sbol_type_key ]
                if item_type in sbol_type_map:
                    sbol_type = sbol_type_key
                    break;

            if sbol_type == 'component':
                if item_type == 'CHEBI':
                    if len(item_definition_uri) == 0:
                        item_sbol_type = sbol_type_map[ item_type ]
                    else:
                        item_sbol_type = item_definition_uri

                    if not item_sbol_type.startswith('http://identifiers.org/chebi/CHEBI'):
                        item_sbol_type = 'http://identifiers.org/chebi/CHEBI:' + \
                            item_sbol_type
                    component = sbol.ComponentDefinition(display_id, item_sbol_type)
                else:
                    component = sbol.ComponentDefinition(display_id, sbol_type_map[ item_type ])

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
                sbol.TextProperty(collection, 'http://sd2e.org#stub_object', '0', '1', 'true')
                if len(item_title):
                    sbol.TextProperty(top_level, 'http://purl.org/dc/terms/title', '0', '1',
                                      item_title)
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
            return {'results': {'operationSucceeded': False,
                                'message': message}
                    }

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
            actions = self.process_link_all(data)
            result = {'actions': actions,
                      'results': {'operationSucceeded': True}
            }

        else:
            print('Unsupported form action: {}'.format(action))

        self.send_response(200, 'OK', json.dumps(result), sm,
                           'application/json')


    def process_link_all(self, data):
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
                    {'search_results': search_results,
                     'table_html': table_html
                    }}


        self.send_response(200, 'OK', json.dumps(response), sm,
                           'application/json')

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "u:p:", ["username=", "password="])
    except getopt.GetoptError:
        print("intent_parser_server.py: -u <sbh username> -p <sbh password>")
        sys.exit(2);

    sbh_username = None
    sbh_password = None
    spreadsheet_id = '1oLJTTydL_5YPyk-wY-dspjIw_bPZ3oCiWiK0xtG8t3g'
    sbh_url='https://hub-staging.sd2e.org'
    sbh_spoofing_prefix='https://hub.sd2e.org'
    sbh_collection='scratch_test'
    sbh_collection_user='sd2e'
    sbh_collection_version='1'

    for opt,arg in opts:
        if (opt == '-u') or (opt == '--username'):
            sbh_username = arg
        elif (opt == '-p') or (opt == '--password'):
            sbh_password = arg

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
