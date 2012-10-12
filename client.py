#!/usr/bin/python2

import re
import socket
import select
import sys

available_rooms = set()
current_room = ""

def show_message(room, sender, message):
    if room == current_room:
        print "{u}: {m}".format(u=sender, m=message)
    # TODO: else append to some file: needs to be efficient though

def is_server_message(message):
    return message[0] == "%"

def parse_server_message(message):
    return message[0], message[1], message[2:]

def is_server_command(message):
    return message[0] == "!"

def parse_server_command(message):
    return message[1:].split()


def notify_client(f):
    def notify():
        f()
        print "Current room is {r}, also in {c}".format(r=current_room,
                c=list(available_rooms.difference([current_room])).join(','))
    return notify

# server command executors
@notify_client
def add_room(room):
    available_rooms.add(room)

@notify_client
def remove_room(room):
    available_rooms.remove(room)
    if current_room == room:
        current_room == available_rooms[0]

@notify_client
def join_room(room):
    add_room(room)
    current_room = room

def print_command(*args):
    show_message(current_room, "SERVER", " ".join(args))


commands=defaultdict(print_command)
commands.update({
        'join': join_room,
        'avail+': add_room,
        'avail-': remove_room,
        }}


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
        sys.stdout.write(data)
        uname = raw_input()
        s.send(uname + "\n")
        data = s.recv(4096)
        if is_server_message(data):
            print data
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
                data = data.rstrip('\n')
                if is_server_command(data):
                    parsed_command = parse_server_command(data)
                    command = parsed_command[0]
                    command_args = parsed_command[1:]
                    commands[command](*command_args)
                else:
                    target_room, sender, message = parse_server_message(data)
                    show_message(target_room, sender, message)

except KeyboardInterrupt:
    pass

finally:
    s.close()
