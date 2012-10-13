#!/usr/bin/python2

import socket
import select

from collections import defaultdict

USERNAME_PROMPT = "%Please choose a user name: "
DEFAULT_ROOM = 'main'

def message_room(target_room, room_members, sender, sender_id, message):
    targets = [c for c in room_members if c is not sender]
    for client in targets:
        client.send("{r} {u} {m}".format(r=target_room, u=sender_id,
            m=message))

def parse_client_message(message):
    m_split = message.split()
    room, message = m_split[0], ' '.join(m_split[1:])
    return room, message

def parse_client_request(message):
    m_split = message.split()
    room, request, args = m_split[0], m_split[1][1:], m_split[2:]
    return room, request, args

def client_request_handler(client, username, data):
    room, request, args = parse_client_request(data)
    print "received client request", request

def client_message_handler(client, username, data):
    room, message = parse_client_message(data)
    avail_rooms = members_rooms[client]
    if room in avail_rooms:
        room_users = room_members[room]
        text = " ".join(message)
        message_room(room, room_users, client, username, text)

message_handlers = defaultdict(lambda: client_message_handler)
message_handlers.update({
    '/': client_request_handler,
    })

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
                    room, message = parse_client_message(data)
                    username = users[sock]
                    handler = message_handlers[message[0]]
                    handler(sock, username, data)
                else:
                    username = data[:-1]
                    if username in users.values():
                        sock.send("%Username already taken\n{0}".format(
                            USERNAME_PROMPT[1:]))
                    else:
                        users[sock] = username
                        members_rooms[sock].append(DEFAULT_ROOM)
                        room_members[DEFAULT_ROOM].append(sock)
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
    finally:
        s.close()
