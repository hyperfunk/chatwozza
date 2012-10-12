#!/usr/bin/python2

import socket
import select

from collections import defaultdict

USERNAME_PROMPT = "Please choose a user name: "
DEFAULT_ROOM = 'main'

def parse_message(message):
    m_split = message.split()
    room, user, message = m_split[0], m_split[1], m_split[2:]


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
                    target_room, sender, message = parse_message(data)
                    avail_channels = members_channels[sock]
                    if sender == users[sock] and target_room in avail_channels:
                        for client in [u for u in users if u is not sock]:
                            # TODO: need to send room to client
                            client.send("{u}: {msg}".format(u=users[sock],
                                                            msg=data))
                else:
                    username = data[:-1]
                    if username in users.values():
                        sock.send("Username already taken\n")
                        sock.send(USERNAME_PROMPT)
                    else:
                        users[sock] = username
                        members_channels[sock].append(DEFAULT_ROOM)
                        channel_members[DEFAULT_ROOM].append(sock)
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

    # channels
    channel_members = defaultdict(list)

    try:
        while True:
            server_loop(s, users, rset, wset, rset, rooms, members_channels)
    except KeyboardInterrupt:
        s.close()
