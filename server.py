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
    m_split = message.split()
    room, message = m_split[0], m_split[1:]
    return room, message

def message_room(target_room, room_members, sender, sender_id, message):
    targets = [c for c in room_members if c is not sender]
    for client in targets:
        client.send("{r} {u} {m}".format(r=target_room, u=sender_id, m=message))

def is_client_request(message_leader):
    return message_leader[0] == '/'

def parse_client_request(message):
    request = message[0][1:]
    args = message[1:]
    return request, args

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
                    room, message = parse_message(data)
                    if is_client_request(message[0]):
                        request, args = parse_client_request(message)
                        print "command:", request, "args:", args
                    else:
                        avail_rooms = members_rooms[sock]
                        if room in avail_rooms:
                            room_users = room_members[room]
                            text = " ".join(message)
                            message_room(room, room_users, sock, users[sock],
                                    text)
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
                        #sock.send("^Welcome {u}\n".format(u=username))
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
        pass
    finally:
        s.close()
