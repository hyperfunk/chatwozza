#!/usr/bin/python2

#
# could have a dict { '%' : func(), '!': func(), ... }
# that you simply look up for message[0] the nthen pass func message [1:]
# with a default being a callable that just prints it as though it's a user
#

import socket
import select

from collections import defaultdict

USERNAME_PROMPT = "%Please choose a user name: "
DEFAULT_ROOM = 'main'

def parse_message(message):
    print message
    m_split = message.split()
    room, message = m_split[0], m_split[1:]

def message_room(target_room, room_members, username, data):
    for client in room_members:
        client.send("{r} {u} {d}".format(r=target_room, u=username, d=data))

def is_request(message):
    return message[0] == '/'

def parse_client_request(message):
    m_split = message.split()
    request = m_split[0]
    args = m_split[1:]
    return command, args

def server_loop(server_socket, users, rset, wset, eset, rooms,
        members_rooms, room_members):

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
                    target_room, message = parse_message(data)
                    if is_request(message):
                        request, args = parse_client_request(message)
                    else:
                        avail_rooms = members_rooms[sock]
                        if target_room in avail_rooms:
                            room_users = room_members[target_room]
                            targets = [c for c in room_users if c is not sock]
                            username=users[sock]
                            message_room(target_room, room_members, username,
                                data)
                else:
                    username = data[:-1]
                    #print username
                    #print users.values()
                    if username in users.values():
                        #print "username taken"
                        sock.send("%Username already taken\n")
                        sock.send(USERNAME_PROMPT)
                    else:
                        users[sock] = username
                        members_rooms[sock].append(DEFAULT_ROOM)
                        room_members[DEFAULT_ROOM].append(sock)
                        sock.send("^Welcome {u}\n".format(u=username))
                        sock.send("!join {r}\n".format(r=DEFAULT_ROOM))

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
    members_rooms = defaultdict(list)

    # rooms
    room_members = defaultdict(list)

    try:
        while True:
            server_loop(s, users, rset, wset, rset, rooms, members_rooms,
                    room_members)
    except KeyboardInterrupt:
        s.close()
