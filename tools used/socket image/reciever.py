import pickle
import socket
import struct
import cv2

HOST = '192.168.4.1'  # Enter IP or Hostname of your server
PORT = 13367 # Pick an open Port (1000+ recommended), must match the server port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

reply = b""
payload = struct.calcsize(">L")

while True:
    print(payload)
    while len(reply) < payload:
        print('recieve {}'.format(len(reply)))
        reply = s.recv(4096)

    packed_msg_size = reply[:payload]
    reply = reply[payload:]
    msg_size = struct.unpack(">L", packed_msg_size)[0]
    print('magsize:{}'.format(msg_size))
    while len(reply) < msg_size:
        reply += s.recv(4096)

    frame_data = reply[:msg_size]
    reply = reply[msg_size:]
    frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

    cv2.namedWindow('Color', cv2.WINDOW_AUTOSIZE)
    cv2.setWindowProperty('Color', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imwrite('asd.jpg',frame)
    cv2.imshow('Color', frame)
    key = cv2.waitKeyEx(1)
    print(reply)
