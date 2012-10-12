#!/usr/bin/python2

import re
import socket
import select
import sys

from collections import defaultdict

current_room = ''
available_rooms = set()


def show_message(room, sender, message):
    if room == current_room:
        sys.stdout.write("{u}: {m}".format(u=sender, m=message))
        sys.stdout.flush()
    # TODO: else append to some file: needs to be efficient though

def notify_client(f):
    def notify(*args):
        f(*args)
        print "Current room is {r}".format(r=current_room)
        other_rooms = available_rooms.difference([current_room])
        if len(other_rooms) > 0:
            print "also in {c}".format(c=','.join(other_rooms))
    return notify

# server command executors
@notify_client
def add_room(room):
    available_rooms.add(room)

@notify_client
def remove_room(room):
    global current_room
    available_rooms.remove(room)
    if current_room == room:
        current_room = available_rooms[0]

@notify_client
def join_room(room):
    global current_room
    current_room = room
    available_rooms.add(room)

# lol enum
ROOM_MESSAGE, SERVER_MESSAGE, SERVER_COMMAND = range(1,4)

def room_message_handler(data):
    data = data.rstrip('\n')
    target_room, sender, message = message[0], message[1], message[2:]
    show_message(target_room, sender, message)
    return ROOM_MESSAGE

def server_message_handler(data):
    show_message(current_room, "SERVER", data[1:])
    return SERVER_MESSAGE

def server_command_handler(data):
    parsed_command = data[1:].split()
    command = parsed_command[0]
    command_args = parsed_command[1:]
    commands[command](*command_args)
    return SERVER_COMMAND


message_handlers=defaultdict(room_message_handler)
message_handlers.update({ # prefix : function
        '%': server_message_handler,
        '!': server_command_handler,
        })

commands = {
        'join': join_room,
        'avail+': add_room,
        'avail-': remove_room,
        }


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect(('127.0.0.1',8000))

# Add stdin to the rset so that we know when to read from the user
rset = [ s, sys.stdin ]

# Null wset
wset = []

try:
    data = s.recv(4096)

    # Prompt for username until we get the welcome message
    while True:
        # could have get_handler but avoiding 1line functions
        handler = message_handlers[data[0]]
        handler(data)
        # may want to make this a response to !name command from server
        # then make the condition that currente room isn't NULL or something
        # or !g_name (give_name) so the server intructs the cleitn what their
        # name is
        uname = raw_input()
        s.send(uname + "\n")
        data = s.recv(4096)
        handler = message_handlers[data[0]]
        if handler(data) is SERVER_COMMAND:
            break

    while True:
        readable, writable, excepts = select.select(rset, wset, rset)

        for fd in readable:
            if fd is sys.stdin:
                data = raw_input()
                if data:
                    s.send("{room} {message}\n".format(room=current_room,
                                                       message=data))
            else:
                data = s.recv(4096)
                if data:
                    print "received:", data, "[from server]"
                    print data[0]
                    handler = message_handlers[data[0]]
                    handler(data)

except KeyboardInterrupt:
    pass

finally:
    s.close()
