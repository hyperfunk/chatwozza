#!/usr/bin/python2

import socket
import select

from collections import defaultdict

USERNAME_PROMPT = "Please choose a user name: "
DEFAULT_ROOM = 'main'


def server_loop(server_socket, users, rset, wset, eset, rooms,
        members_channels):

    readable, writable, excepts = select.select(rset, wset, eset)

    for sock in readable:

        if sock is server_socket:
            fd, ip = sock.accept()

            if ip != '':
                print "Connection from {addr}".format(addr=ip[0])
                rset.append(fd)
                fd.send(USERNAME_PROMPT)
        else:
            data = sock.recv(4096)
            if data:
                if sock in users:
                    for client in users:
                        if client is not sock:
                            client.send("{u}: {msg}".format(u=users[sock],
                                                            msg=data))
                else:
                    username = data[:-1]
                    if username in users.values():
                        sock.send("Username already taken\n")
                        sock.send(USERNAME_PROMPT)
                    else:
                        # TODO: what does RFC 1459 and 2812 say (need to read)
                        # about EOM
                        users[sock] = username
                        members_channels[sock].append(DEFAULT_ROOM)
                        sock.send("Welcome {u}".format(u=username))

            else:
                sock.close()
                rset.remove(sock)
                users.pop(sock)

if __name__=='__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.bind(("0.0.0.0", 8000))
    s.listen(5)

    # Set up read set
    rset = [ s ]

    # Null write set
    wset = [ ]

    # socket:username dict
    users = {}

    # list of rooms
    rooms = set([DEFAULT_ROOM])

    # members
    members_channels = defaultdict(list)

    try:
        while True:
            server_loop(s, users, rset, wset, rset, rooms, members_channels)
    except KeyboardInterrupt:
        s.close()
