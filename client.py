import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect(('127.0.0.1',8000))

try:
    data = s.recv(4096)
    print data
finally:
    s.close()
