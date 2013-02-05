#!/usr/bin/python2
# -*- coding: utf-8 -*-

# server.py version 0.1

# Send server notifcations with preceeding "%"
# Send server-client commands with preceeding "!"

import socket
import select

from collections import defaultdict

from Crypto.PublicKey import RSA

NAME_MAX_LENGTH  = 10
USERNAME_PROMPT = "%Please choose a user name (max length {}): ".format(
        NAME_MAX_LENGTH)
DEFAULT_ROOM = 'main'


# socket:username dict
users = {}
# list of rooms
rooms = set([DEFAULT_ROOM])
# members
members_rooms = defaultdict(list)
# rooms
room_members = defaultdict(list)
# keys:
#   do we want to generate a key for each user?
SERVER_PRIVATE_KEY = RSA.generate(2048)
SERVER_PUBLIC_KEY = SERVER_PRIVATE_KEY.publickey()
SERVER_PRIVATE_KEY_STR = SERVER_PRIVATE_KEY.exportKey()
SERVER_PUBLIC_KEY_STR = SERVER_PUBLIC_KEY.exportKey()

class User(object):
    def __init__(self, socket, username=None, rooms=None, pub_key=None):
        self.socket = socket
        self.username = username
        self.rooms = rooms
        self.pub_key = pub_key

    def send_message(self, message):
        if self.pub_key:
            send_encrypted_message(self.socket, message, self.pub_key)
        else:
            self.socket.send(message)

    def read_message(self, message_length=4096):
        return self.socket.read(message_length)

def send_encrypted_message(socket, message, key):
    socket.send(key.encrypt(message,0)[0])

def cleanup_client(client):
    print "Client leaving"
    client.close()
    rset.remove(client)
    if client in users:
        del users[client]
    if client in members_rooms:
        del members_rooms[client]
    for room, members in room_members.iteritems():
        if client in members:
           members.remove(client)

def message_room(target_room, sender, sender_id, message):
    members = room_members[target_room]
    targets = [c for c in members if c is not sender]
    #print "There are", len(targets), "targets"
    usernames = [ users[c] for c in targets ]
    #print "Sending to: ", usernames
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
        message_room(room, client, username, message)

message_handlers = defaultdict(lambda: client_message_handler)
message_handlers.update({
    '/': client_request_handler,
    })

def server_loop():

    readable, writable, excepts = select.select(rset, wset, eset)

    for sock in readable:

        # if we are accepting a new client
        if sock is server_socket:
            fd, ip = sock.accept()
            if ip != '':
                # send our public key:
                print "Connection from {addr}".format(addr=ip[0])
                rset.append(fd)
                fd.send(SERVER_PUBLIC_KEY_STR)
                #send_encrypted_message(fd, USERNAME_PROMPT, SERVER_PRIVATE_KEY)
        # cuurent client is sending a message
        else:
            data = sock.recv(4096)
            if data:
                # if we've already initialized the user: data is a message
                if sock in users:
                    _, message = parse_client_message(data)
                    username = users[sock]
                    handler = message_handlers[message[0]]
                    handler(sock, username, data)
                # otherwise: get a username
                else:
                    username = data[:-1]
                    if username in users.values():
                        message = "%Username already taken\n{0}".format(
                            USERNAME_PROMPT[1:])
                        send_encrypted_message(sock, message,
                                SERVER_PRIVATE_KEY)
                    # prevent blank username
                    elif len(username) < 1 or len(username) > NAME_MAX_LENGTH:
                        message = "%Invalid username length\n{0}".format(
                            USERNAME_PROMPT[1:])
                        send_encrypted_message(sock, message, key)
                    # valid username: setup user
                    else:
                        users[sock] = username
                        members_rooms[sock].append(DEFAULT_ROOM)
                        room_members[DEFAULT_ROOM].append(sock)
                        message = "!join {r}\n".format(r=DEFAULT_ROOM)
                        send_encrypted_message(sock, message, key)

            # client has left: cleanup
            else:
                cleanup_client(sock)

if __name__=='__main__':
    # set up listening socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 8000))
    server_socket.listen(5)

    # set up read set
    rset = [server_socket]
    # null write set
    wset = []
    # exception set
    eset = []

    try:
        while True:
            server_loop()
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()
