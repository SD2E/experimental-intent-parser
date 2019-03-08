import socket
import threading
import json
from socket_manager import SocketManager
from google_accessor import GoogleAccessor
import http_message;
import uuid
import traceback
import functools

class ConnectionException(Exception):
    def __init__(self, code, message, content=""):
        super(ConnectionException, self).__init__(message);
        self.code = code
        self.message = message
        self.content = content


class IntentParserServer:
    def __init__(self, bind_port=4454, bind_ip="0.0.0.0"):
        self.bind_port = bind_port
        self.bind_ip = bind_ip

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((bind_ip, bind_port))
        self.server.listen(5)
        self.google_accessor = GoogleAccessor.create()
        self.client_state_map = {}
        self.client_state_lock = threading.Lock()

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

                if httpMessage.getState() == http_message.State.ERROR:
                    client_socket.close()
                    return

                method = httpMessage.getMethod()

                try:
                    if method == 'POST':
                        self.handlePOST(httpMessage, sm)
                    elif method == 'GET':
                        self.handleGET(httpMessage, sm)
                    else:
                        self.sendResponse(501, 'Not Implemented', 'Unrecognized request method\n', sm)
                except ConnectionException as ex:
                    self.sendResponse(ex.code, ex.message, ex.content, sm)

                except Exception as ex:
                    print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
                    self.sendResponse(504, 'Internal Server Error', 'Internal Server Error\n', sm)

        except Exception as e:
            print('Exception: {}'.format(e))

        client_socket.close()

    def sendResponse(self, code, message, content, sm):
            response = http_message.HttpMessage()
            response.setResponseCode(code, message)
            response.setBody(content.encode('utf-8'))
            response.send(sm)

    def handlePOST(self, httpMessage, sm):
        resource = httpMessage.getResource()

        if resource == '/analyzeDocument':
            self.process_analyze_document(httpMessage, sm)
        elif resource == '/message':
            self.process_message(httpMessage, sm)
        elif resource == '/buttonClick':
            self.process_button_click(httpMessage, sm)
        else:
            self.sendResponse(404, 'Not Found', 'Resource Not Found\n', sm)

    def get_json_body(self, httpMessage):
        body = httpMessage.getBody()
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
            self.sendResponse(200, 'OK', json.dumps(actions), sm)
        except Exception as e:
            raise e
        finally:
            self.release_connection(client_state)

    def process_message(self, httpMessage, sm):
        json_body = self.get_json_body(httpMessage)
        if 'message' in json_body:
            print(json_body['message'])
        self.sendResponse(200, 'OK', '[]', sm)


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
            raise ConnectionException('404', 'Not Found',
                                      'Failed to access document ' +
                                      client_state['docId'])

        client_state = self.new_connection(document_id)
        client_state['pos'] = 0
        client_state['doc'] = doc

        try:
            actions = self.analyze_document(client_state, doc)
            self.sendResponse(200, 'OK', json.dumps(actions), sm)

        except Exception as e:
            raise e

        finally:
            self.release_connection(client_state)

    def report_search_results(self, client_state):
        search_results = client_state['search_results']
        search_result_index = client_state['search_result_index']
        if search_result_index >= len(search_results):
            return []

        client_state['search_result_index'] += 1

        search_result = search_results[ search_result_index ]
        paragraph_index = search_result['paragraph_index']
        offset = search_result['offset']
        term = search_result['term']
        end_offset = offset + len(term) - 1

        actions = []

        highlightTextAction = self.highlightText(paragraph_index, offset,
                                                 end_offset)
        actions.append(highlightTextAction)

        dialogAction = self.simple_sidebar_dialog('Process ' + term + ' ?',
                                                  [('Yes', 'process_analyze_yes'),
                                                  ('No', 'process_analyze_no')])
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


    def analyze_document(self, client_state, doc):
        body = doc.get('body');
        doc_content = body.get('content')

        paragraphs = self.get_paragraphs(doc_content)

        search_results = []
        term = 'Kan'
        pos = 0

        itr = 0
        while True:
            result = self.find_text(term, pos, paragraphs)
            if result is None:
                break;

            search_results.append({ 'paragraph_index': result[0],
                                    'offset': result[1],
                                    'term': term })
            pos = result[2] + len(term)

        if len(search_results) == 0:
            return []

        client_state['search_results'] = search_results
        client_state['search_result_index'] = 0

        return self.report_search_results(client_state)

    def process_analyze_yes(self, json_body, client_state):
        return self.report_search_results(client_state)

    def process_analyze_no(self, json_body, client_state):
        return self.report_search_results(client_state)

    def highlightText(self, paragraph_index, offset, end_offset):
        highlightText = {}
        highlightText['action'] = 'highlightText'
        highlightText['paragraph_index'] = paragraph_index
        highlightText['offset'] = offset
        highlightText['end_offset'] = end_offset

        return highlightText

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
        for button in buttons:
            htmlMessage += '<input id=' + button[1] + 'Button value="'
            htmlMessage += button[0] + '" type="button" onclick="'
            htmlMessage += button[1] + 'Click()" />\n'

        action = {}
        action['action'] = 'showSidebar'
        action['html'] = htmlMessage

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

                content = text_run['content'].lower()
                offset = content.find(text.lower(), find_start)
                if offset < 0:
                    continue

                first_index = elements[0]['startIndex']
                offset += start_index - first_index

                pos = first_index + offset
                return (paragraph_index, offset, pos)
        return None

    def handleGET(self, httpMessage, sm):
        resource = httpMessage.getResource()
        if resource == "/status":
            self.sendResponse(200, 'OK', 'SBH Plugin Up and Running\n', sm)
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

sbhPlugin = IntentParserServer()
sbhPlugin.serverRunLoop()
