#!/usr/bin/python2

import socket
import select

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind(("0.0.0.0", 8000))
s.listen(5)

# Set up read set
rset = [ s ]

# Null write set
wset = [ ]

while True:

    readable, writable, excepts = select.select(rset, wset, rset)

    for sock in readable:

        if sock is s:
            fd, ip = s.accept()

            if ip != '':
                print "Connection from {addr}".format(addr=ip[0])
                rset.append(fd)

        else:
            data = sock.recv(4096)
            if data:
                for client in [ c for c in rset if c not in [s,sock] ]:
                    client.send(data)
            else:
                sock.close()
                rset.remove(sock)

