#!/usr/bin/python2

import socket 
import select

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind(("127.0.0.1", 8000))
s.listen(5)

# Set up read set
rset = [ s ]

# Null write set
wset = [ ]

while True:

  readable, writable, excepts = select.select(rset, wset, rset)

  for socket in readable:

    if socket is s:
      fd, ip = s.accept()

      if ip != '':
        print "Connection from " + ip[0]
        rset.append(fd)

    else:
      data = socket.recv(4096)

      if data:
        socket.send(data)
      else:
        socket.close()
        rset.remove(socket)
        
