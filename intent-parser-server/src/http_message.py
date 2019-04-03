from enum import Enum

from socket_manager import SocketManager

class State(Enum):
    REQUEST = 1
    HEADER = 2
    DONE = 3
    ERROR = 4

class HttpMessage:
    ERROR = 1
    PENDING = 2
    DONE = 3
    maxHeaderCount = 100

    def reset(self):
        self.header = {}
        self.resource = ''
        self.requestLine = ''
        self.method = ''
        self.isRequest = True
        self.state = State.REQUEST
        self.httpVersion = 1.1
        self.body = bytes()
        self.headerCount = 0

    def __init__(self, socketManager=None):
        self.reset()

        if socketManager == None:
            return

        while (self.state != State.DONE) and (self.state != State.ERROR):
            line = socketManager.read_line()

            if line == None:
                self.state = State.ERROR
                return

            if self.process_line(line) == self.ERROR:
                self.state = State.ERROR
                return

        self.fetch_body(socketManager)

    def set_response_code(self, code, message):
        if self.state != State.REQUEST:
            self.state = State.ERROR
            return self.ERROR

        self.requestLine = 'HTTP/1.1 ' + str(code) + ' ' + message
        self.state = State.HEADER

    def set_header(self, key, value):
        if self.state != State.HEADER:
            self.state = State.ERROR
            return self.ERROR

        if key not in self.header:
            self.header[key] = []

        self.header[key].append(value)

    def send(self):
        return self.send(self.socketManager)

    def send(self, socketManager):
        self.send_line(socketManager, self.requestLine)

        for header in self.header:
            for value in self.header[header]:
                self.send_line(socketManager, header + ': ' + value)

        self.send_line(socketManager, '');

        if self.body != None:
            socketManager.write(self.body)


    def send_line(self, socketManager, line):
        return socketManager.write((line + '\r\n').encode('utf-8'))


    def set_body(self, body):
        self.body = body
        return self.set_header('Content-Length',
                               str(len(body)))

    def get_body(self):
        return self.body

    def get_state(self):
        return self.state

    def get_resource(self):
        return self.resource

    def get_path(self):
        return self.resource.split('?')[0]

    def get_request_line(self):
        return self.requestLine

    def get_method(self):
        return self.method

    def get_header(self, headerName):
        if headerName not in self.header:
            return None

        return self.header[headerName][0]

    def get_headers(self, headerName):
        if headerName not in self.header:
            return None

        return self.header[headerName]

    def process_line(self, line):
        if self.state == State.REQUEST:
            return self.process_request(line)

        elif self.state == State.HEADER:
            return self.process_header(line)

        elif self.state == State.HEADER:
            return self.DONE

        else:
            return self.ERROR

    def process_header(self, line):
        if self.headerCount >= self.maxHeaderCount:
            raise Exception("Too many HTTP Headers")

        if len(line) == 0:
            self.state = State.DONE
            return self.DONE

        sep = line.find(':')
        if sep < 0:
            self.state = State.ERROR
            return self.ERROR

        key = line[:sep].strip()
        value = line[(sep+1):].strip()

        if key not in self.header:
            self.header[key] = []

        self.header[key].append(value)
        self.headerCount += 1

    def process_request(self, line):
        self.requestLine = line

        fields = line.split()
        if len(fields) != 3:
            self.state = State.ERROR
            return self.ERROR

        if fields[2][:5] != 'HTTP/':
            self.state = State.ERROR
            return self.ERROR

        self.method = fields[0]
        self.resource = fields[1]

        self.state = State.HEADER;
        return self.PENDING

    def fetch_body(self, socketManager):
        if 'Transfer-Encoding' in self.header:
            if self.header['Transfer-Encoding'][0] == 'chunked':
                self.read_chunked_body(socketManager);
                return

        if 'Content-Length' in self.header:
            self.fetch_raw_body(socketManager)


    def fetch_raw_body(self, socketManager):
        lengthStr = self.header['Content-Length'][0]
        self.body = socketManager.read_bytes(int(lengthStr))


    def read_chunked_body(self, socketManager):
        self.body = b'';
        while True:
            chunkLenStr = socketManager.read_line()
            if chunkLenStr == None:
                break;
            chunkLen = int(chunkLenStr, 16)
            if chunkLen == 0:
                val = socketManager.read_line()
                socketManager.read_line()
                break;
            self.body += socketManager.read_bytes(chunkLen)
            socketManager.read_line()
        pass
