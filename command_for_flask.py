import socket
import struct
import pickle
import cv2
import threading
import time

class ServerCommand:
    def __init__(self):
        HOST = '127.0.0.1'
        port = 12345
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((HOST, port))

        img = cv2.imread('jpg.jpeg')
        self.frame = cv2.imencode('.jpg', img)[1].tobytes()
        self.status = 0

    def send_command(self, command):
        self.status = command
        reply = command
        reply = reply.encode()
        self.s.sendall(reply)
        print(reply)

    def start_reciever(self):
        self.rc = threading.Thread(target=self.recieve_server)
        self.rc.start()
        print('reciever started')

    def close_all(self):
        self.rc._stop()
        print('stopped')


    def recieve_server(self):
        HOST = '127.0.0.1'  # Enter IP or Hostname of your server
        PORT = 12347  # Pick an open Port (1000+ recommended), must match the server port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        payload = struct.calcsize(">L")
        data = b''
        try:
            while True:
                while len(data) < payload:
                    data += s.recv(4096)
                # print('recieved')
                packed_msg_size = data[:payload]
                data = data[payload:]
                msg_size = struct.unpack(">L", packed_msg_size)[0]
                #print(msg_size)

                while len(data) < msg_size:
                    data += s.recv(4096)

                frame_data = data[:msg_size]
                data = data[msg_size:]
                self.frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")

                if self.status == '9':
                    break
        except ConnectionResetError:
            print('reset error')
        finally:
            print('finally')
            time.sleep(5)
            s.close()
            self.s.close()
            print('sockets closed')
            img = cv2.imread('jpg.jpeg')
            self.frame = cv2.imencode('.jpg', img)[1].tobytes()

    def recieve_frame(self):
        return self.frame


if __name__ == '__main__':
    a = Server_command()
    a.send_command('8')
    a.send_command('5')
    a.send_command('99')