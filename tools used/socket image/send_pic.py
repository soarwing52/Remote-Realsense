import pickle
import socket
import struct
import cv2

HOST = '192.168.4.1' # Enter IP or Hostname of your server
PORT = 13343 # Pick an open Port (1000+ recommended), must match the server port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST,PORT))

img = cv2.imread('besr result.png')
encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
result, frame = cv2.imencode('.jpg', img, encode_param)

data = pickle.dumps(frame,0)
size = len(data)

s.sendall(struct.pack(">L",size) + data)

s.send(b'end')

payload = struct.calcsize(">L")
reply = b""
while True:
    while len(reply) < payload:
        reply = s.recv(4096)
    packed_msg_size = reply[:payload]
    income = reply[payload:]
    msg_size = struct.unpack(">L", packed_msg_size)[0]

    while len(income) < msg_size:
        income += s.recv(4096)

    frame_data = income[:msg_size]
    data = income[msg_size:]
    frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
    cv2.imwrite('asdasd.jpg', frame)
    cv2.imshow('wind', frame)
    cv2.waitKey(0)
    print(reply)
    if reply == 'end':
        break