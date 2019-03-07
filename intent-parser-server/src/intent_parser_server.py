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
        if resource == '/message':
            self.process_message(httpMessage, sm)
        else:
            self.sendResponse(404, 'Not Found', 'Resource Not Found\n', sm)

    def get_json_body(self, httpMessage):
        body = httpMessage.getBody()
        if body == None or len(body) == 0:
            errorMessage = 'No POST data\n'
            raise ConnectionException(400, 'Bad Request', errorMessage, sm)

        bodyStr = body.decode('utf-8')

        try:
            return json.loads(bodyStr)
        except json.decoder.JSONDecodeError as e:
            errorMessage = 'Failed to decode JSON data: {}\n'.format(e);
            raise ConnectionException(400, 'Bad Request', errorMessage, sm)

    def process_message(self, httpMessage, sm):
        json_body = self.get_json_body(httpMessage)
        if 'message' in json_body:
            print(json_body['message'])
        
    def process_analyze_document(self, httpMessage, sm):
        json_body = self.get_json_body(httpMessage)

        client_state = self.get_connection(json_body)

        if client_state is None:
            raise ConnectionException('400', 'Bad Request',
                                      'Invalid connection state')

        if 'documentId' not in json_body:
            raise ConnectionException('404' 'Bad Request',
                                      'Missing documentId');

        client_state['docId'] = json_body['documentId']

        try:
            doc = self.google_accessor.get_document(
                document_id=client_state['docId']
                )
        except Exception as ex:
            print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
            raise ConnectionException('404', 'Not Found',
                                      'Failed to access document ' +
                                      client_state['docId'])

        self.analyze_document(client_state, doc, sm)

    def analyze_document(self, client_state, doc, sm):
        body = doc.get('body');
        doc_content = body.get('content')
        paragraph_content = list(filter(lambda x : 'paragraph' in x, doc_content))
        paragraphs = list(map(lambda x : x['paragraph'], paragraph_content))

        term = 'Kan'
        pos = self.find_text(term, client_state['pos'], paragraphs)

        if pos is not None:
            client_state['highlight_start'] = pos - 1
            client_state['highlight_end'] = pos + len(term) - 2
            client_state['pos'] = pos + len(term)

            htmlMessage = ''

            htmlMessage += "<script>"
            htmlMessage += 'function yesClick() { '
            htmlMessage += '  google.script.run.sendEmptyMessage() '
            htmlMessage += '}'
            htmlMessage += "</script>"

            htmlMessage += "<script>"
            htmlMessage += 'function noClick() { '
            htmlMessage += '  google.script.run.sendMessage(\'' + json.dumps(client_state) + '\')'
            htmlMessage += '}'
            htmlMessage += "</script>"

            htmlMessage += '<p>Link test to test'
            htmlMessage += '<input id="yesButton" value="Yes" type="button" onclick="yesClick()" />'
            htmlMessage += '<input id="noButton" value="No" type="button" onclick="noClick()" />'

            client_state['html'] = htmlMessage


        self.sendResponse(200, 'OK', json.dumps(client_state), sm)


    def find_text(self, text, starting_pos, paragraphs):
        elements = []
        for paragraph in paragraphs:
            elements += paragraph['elements']

        for element in elements:
            if 'endIndex' not in element:
                print(element)
                continue

            if element['endIndex'] < starting_pos:
                continue

            if 'textRun' not in element:
                continue

            textRun = element['textRun']
            content = textRun['content']
            index = content.find(text)
            if index < 0:
                continue

            return index + element['startIndex']

        return None


    def handleGET(self, httpMessage, sm):
        resource = httpMessage.getResource()
        if resource == "/status":
            self.sendResponse(200, 'OK', 'SBH Plugin Up and Running\n', sm)
        else:
            raise ConnectionException(404, 'Not Found', 'Resource Not Found')

    def new_connection(self):
        new_id = str(uuid.uuid4())
        client_state = {}
        client_state['id'] = new_id
        client_state['pos'] = 0

        self.client_state_lock.acquire()
        self.client_state_map[new_id] = client_state
        self.client_state_lock.release()

        return client_state

    def get_connection(self, request):
        if 'connection_id' in request:
            self.client_state_lock.acquire()
            client_state = self.client_state_map[
                request['connection_id']
                ]
            self.client_state_lock.release()
            return client_state

        else:
            return self.new_connection()

sbhPlugin = IntentParserServer()
sbhPlugin.serverRunLoop()
