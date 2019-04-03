class SocketManager:
    def __init__(self, socket):
        self.socket = socket
        self.buffer = bytes()
        self.index = 0
        self.BUF_LEN = 8192

    def read_line(self):
        index = 0
        while True:
            while index < len(self.buffer):
                c = self.buffer[index]

                if c == ord('\n'):
                    if self.buffer[index-1] == ord('\r'):
                        line = self.buffer[:index-1].decode('utf-8')
                    else:
                        line = self.buffer[:index].decode('utf-8')
                    self.buffer = self.buffer[(index+1):]
                    self.eol = True
                    return line

                index += 1

            if index == (self.BUF_LEN - 1):
                return None

            data = self.socket.recv( self.BUF_LEN - len(self.buffer) )
            if data == None:
                return None

            if len(data) == 0:
                return None

            self.buffer += data

    def write(self, data):
        return self.socket.send(data)

    def read_bytes(self, byteCount):
        bytesLeft = byteCount

        result = b''
        
        while len(self.buffer) < byteCount:
            self.buffer += self.socket.recv(byteCount - len(self.buffer))

        result = self.buffer[:byteCount]
        self.buffer = self.buffer[byteCount:]
        return result        
