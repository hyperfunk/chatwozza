#!/usr/bin/python2
# -*- coding: utf-8 -*-

import re
import socket
import select
import sys
import argparse

from collections import defaultdict
from Crypto.PublicKey import RSA

from Displayers import CursesDisplayer

server_ip, server_port = '127.0.0.1', 8000
current_room = ''
available_rooms = set()
user_name = ''
displayer = None

SERVER_PUBLIC_KEY_STR = None
SERVER_PUBLIC_KEY = None

def get_displayer(args):
    return CursesDisplayer()

def parse_args():
    parser = argparse.ArgumentParser(description='foray into sockets')
    parser.add_argument('--curses', action='store_true')
    parser.add_argument('--gui', action='store_true')
    args = parser.parse_args()
    if args.curses and args.gui:
        parser.print_help()
        print "Must choose only gui or curses interface"
        exit()
    return args

def user_input(sock):
    data = displayer.get_message()
    if data:
        fmt_message = '{room} {message}\n'.format(room=current_room,
                message=data)
        sock.send(fmt_message)
        chat_text = '{u}: {d}\n'.format(u=user_name, d=data)
        displayer.show_message(chat_text)

def chat_update(sock):
    data = sock.recv(4096)
    if data:
        handler = message_handlers[data[0]]
        handler(data)

def show_message(room, sender, message):
    if room == current_room:
        fmt_message = "{u}: {m}".format(u=sender, m=message)
        displayer.show_message(fmt_message)

def notify_client(f):
    def notify(*args):
        f(*args)
        #fmt_current = "Current room is {r}".format(r=current_room)
        displayer.show_room_name(current_room)
        other_rooms = available_rooms.difference([current_room])
        if len(other_rooms) > 0:
            fmt_other = "also in {c}".format(c=','.join(other_rooms))
            displayer.show_message(fmt_other)
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
    data = data.split()
    target_room, sender, message = data[0], data[1], ' '.join(data[2:])
    show_message(target_room, sender, message+'\n')
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


message_handlers=defaultdict(lambda: room_message_handler)
message_handlers.update({ # prefix : function
        #'m': room_message_handler,
        '%': server_message_handler,
        '!': server_command_handler,
        })

commands = {
        'join': join_room,
        'avail+': add_room,
        'avail-': remove_room,
        }

def main():
    args = parse_args()

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, server_port))
    except socket.error:
        print "Unable to communicate with server @ {ip}:{port}".format(
                ip=server_ip, port=server_port)
        exit()

    global displayer
    #displayer = get_displayer(args)

    # Add stdin to the rset so that we know when to read from the user
    rset = [ client_socket, sys.stdin ]
    # Null wset
    wset = []

    try:
        # receive the server public key
        global SERVER_PUBLIC_KEY_STR
        SERVER_PUBLIC_KEY_STR = client_socket.recv(2048)
        global SERVER_PUBLIC_KEY
        SERVER_PUBLIC_KEY = RSA.importKey(SERVER_PUBLIC_KEY_STR)

        crypt_data = client_socket.recv(4096)
        data = SERVER_PUBLIC_KEY.decrypt(crypt_data)
        print data
        exit()

        # Username Prompt Loop
        handler = message_handlers[data[0]]
        handler(data)
        while True:
            global user_name
            user_name = displayer.get_message()
            client_socket.send(user_name + "\n")
            data = client_socket.recv(4096)
            handler = message_handlers[data[0]]
            # keep prompting for username until receiving a command from the
            # server
            if handler(data) is SERVER_COMMAND:
                break

        # Main chat exchange loop
        while True:
            readable, writable, excepts = select.select(rset, wset, rset)

            for fd in readable:
                if fd is sys.stdin:
                    user_input(client_socket)
                else:
                    chat_update(client_socket)

    except KeyboardInterrupt:
        pass

    finally:
        client_socket.close()
        #displayer.close()

if __name__=='__main__':
    main()
