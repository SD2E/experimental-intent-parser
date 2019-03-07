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
            line = socketManager.readLine()

            if line == None:
                self.state = State.ERROR
                return

            if self.processLine(line) == self.ERROR:
                self.state = State.ERROR
                return

        self.fetchBody(socketManager)

    def setResponseCode(self, code, message):
        if self.state != State.REQUEST:
            self.state = State.ERROR
            return self.ERROR

        self.requestLine = 'HTTP/1.1 ' + str(code) + ' ' + message
        self.state = State.HEADER

    def setHeader(self, key, value):
        if self.state != State.HEADER:
            self.state = State.ERROR
            return self.ERROR

        if key not in self.header:
            self.header[key] = []

        self.header[key].append(value)

    def send(self):
        return self.send(self.socketManager)

    def send(self, socketManager):
        self.sendLine(socketManager, self.requestLine)

        for header in self.header:
            for value in self.header[header]:
                self.sendLine(socketManager, header + ': ' + value)

        self.sendLine(socketManager, '');

        if self.body != None:
            socketManager.write(self.body)


    def sendLine(self, socketManager, line):
        return socketManager.write((line + '\r\n').encode('utf-8'))


    def setBody(self, body):
        self.body = body
        return self.setHeader('Content-Length',
                              str(len(body)))

    def getBody(self):
        return self.body

    def getState(self):
        return self.state

    def getResource(self):
        return self.resource

    def getRequestLine(self):
        return self.requestLine

    def getMethod(self):
        return self.method

    def getHeader(self, headerName):
        if headerName not in self.header:
            return None

        return self.header[headerName][0]

    def getHeaders(self, headerName):
        if headerName not in self.header:
            return None

        return self.header[headerName]

    def processLine(self, line):
        if self.state == State.REQUEST:
            return self.processRequest(line)

        elif self.state == State.HEADER:
            return self.processHeader(line)

        elif self.state == State.HEADER:
            return self.DONE

        else:
            return self.ERROR

    def processHeader(self, line):
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

    def processRequest(self, line):
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

    def fetchBody(self, socketManager):
        if 'Transfer-Encoding' in self.header:
            if self.header['Transfer-Encoding'][0] == 'chunked':
                self.readChunkedBody(socketManager);
                return

        if 'Content-Length' in self.header:
            self.fetchRawBody(socketManager)
        
    
    def fetchRawBody(self, socketManager):
        lengthStr = self.header['Content-Length'][0]
        self.body = socketManager.readBytes(int(lengthStr))


    def readChunkedBody(self, socketManager):
        self.body = b'';
        while True:
            chunkLenStr = socketManager.readLine()
            if chunkLenStr == None:
                break;
            chunkLen = int(chunkLenStr, 16)
            if chunkLen == 0:
                val = socketManager.readLine()
                socketManager.readLine()
                break;
            self.body += socketManager.readBytes(chunkLen)
            socketManager.readLine()
        pass
