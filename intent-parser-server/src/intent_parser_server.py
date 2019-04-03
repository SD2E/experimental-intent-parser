import socket
import threading
import json
from socket_manager import SocketManager
from google_accessor import GoogleAccessor
import http_message;
import uuid
import traceback
import functools
from operator import itemgetter

class ConnectionException(Exception):
    def __init__(self, code, message, content=""):
        super(ConnectionException, self).__init__(message);
        self.code = code
        self.message = message
        self.content = content


class IntentParserServer:
    def __init__(self, bind_port=8080, bind_ip="0.0.0.0"):
        self.bind_port = bind_port
        self.bind_ip = bind_ip

        self.google_accessor = GoogleAccessor.create()
        self.spreadsheet_id = "1oLJTTydL_5YPyk-wY-dspjIw_bPZ3oCiWiK0xtG8t3g";
        self.google_accessor.set_spreadsheet_id(self.spreadsheet_id)
        self.spreadsheet_tabs = self.google_accessor.type_tabs.keys()

        self.client_state_map = {}
        self.client_state_lock = threading.Lock()
        self.item_map = self.generate_item_map()

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((bind_ip, bind_port))
        self.server.listen(5)

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
            actions = method(json_body, client_state)
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

        client_state = self.get_connection(document_id)

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
            actions = self.analyze_document(client_state, doc, start_offset)
            self.send_response(200, 'OK', json.dumps(actions), sm,
                               'application/json')

        except Exception as e:
            raise e

        finally:
            self.release_connection(client_state)

    def add_link(self, search_result):
            paragraph_index = search_result['paragraph_index']
            offset = search_result['offset']
            term = search_result['term']
            link = self.item_map[term]
            end_offset = offset + len(term) - 1
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

            use_sidebar = True

            html  = ''
            html += '<center>'
            html += 'Link ' + content_term + ' to ';
            html += '<a href=' + uri + ' target=_blank>'
            html += term + '</a> ?'
            html += '</center>'


            buttons = [('Yes', 'process_analyze_yes'),
                       ('No', 'process_analyze_no'),
                       ('Link All', 'process_link_all')]

            if use_sidebar:
                dialogAction = self.simple_sidebar_dialog(html, buttons)
            else:
                dialogAction = self.simple_modal_dialog(html, buttons)

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
        for button in buttons:
            htmlMessage += '<input id=' + button[1] + 'Button value="'
            htmlMessage += button[0] + '" type="button" onclick="'
            htmlMessage += button[1] + 'Click()" />\n'

        action = {}
        action['action'] = 'showModalDialog'
        action['html'] = htmlMessage
        action['title'] = title
        action['width'] = width
        action['height'] = height

        return action

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
        self.client_state_lock.acquire()

        document_id = client_state['document_id']

        if document_id in self.client_state_map:
            client_state = self.client_state_map[document_id]
            client_state['locked'] = False

        self.client_state_lock.release()

    def generate_item_map(self):
        item_map = {}

        #f = open('item-map.json', 'r')
        #item_map = json.loads(f.read())
        #return item_map

        sheet_data = self.fetch_spreadsheet_data()
        for tab in sheet_data:
            for row in sheet_data[tab]:
                if 'Common Name' in row and 'SynBioHub URI' in row:
                    common_name = row['Common Name']
                    uri = row['SynBioHub URI']
                    item_map[common_name] = uri

        #f = open('item-map.json', 'w')
        #f.write(json.dumps(item_map))
        #f.close()
        return item_map


sbhPlugin = IntentParserServer()
sbhPlugin.serverRunLoop()
