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

# socket:username dict
users = {}

def username_prompt(sock):
    sock.send("Please choose a user name:")

while True:

    readable, writable, excepts = select.select(rset, wset, rset)

    for sock in readable:

        if sock is s:
            fd, ip = s.accept()

            if ip != '':
                print "Connection from {addr}".format(addr=ip[0])
                rset.append(fd)
                username_prompt(fd)
        else:
            data = sock.recv(4096)
            if data:
                if sock in users.keys():
                    for client in users.keys():
                        if client is not sock:
                            client.send("{un}: {s}".format(un=users[sock],
                                                           s=data))
                else:
                    if data in users.values():
                        sock.send("Username already taken\n")
                        username_prompt(sock)
                    else:
                        # each sock.recv string comes with +"empty_chat"+"\n"
                        users[sock] = data[:-2]

            else:
                sock.close()
                rset.remove(sock)

