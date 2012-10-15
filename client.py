#!/usr/bin/python2

import curses
import curses.textpad
import re
import socket
import select
import sys
import argparse

from collections import defaultdict

current_room = ''
available_rooms = set()
user_name = ''
input_window = None
chat_window = None

def parse_args():
    parser = argparse.ArgumentParser(description='foray into sockets')
    parser.add_argument('--curses', action='store_true')
    return parser.parse_args()

def setup_curses(screen, initial_text):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.curs_set(0)

    height, width = screen.getmaxyx()

    # input_window is the box for user input
    input_window = curses.newwin(1, width, height-1, 0)
    input_window.bkgd(' ', curses.color_pair(1))
    input_window.attron(curses.A_BOLD)
    input_window.scrollok(True)

    # chat_window is updated with other user data
    chat_window = curses.newwin(height-1, width, 0, 0)
    chat_window.bkgd(' ', curses.color_pair(2))
    chat_window.attron(curses.A_BOLD)
    chat_window.scrollok(True)
    chat_window.addstr(initial_text + "\n",
            curses.color_pair(4) | curses.A_BOLD)

    input_window.refresh()
    chat_window.refresh()

    return input_window, chat_window

def user_input(sock):
    if input_window is not None:
        data = input_window.getstr()
    else:
        data = raw_input()
    if data:
        fmt_message = '{room} {message}\n'.format(room=current_room,
                message=data)
        sock.send(fmt_message)
        if chat_window is not None and input_window is not None:
            chat_text = '{u}: {d}\n'.format(u=user_name, d=data)
            chat_window.addstr(chat_text,
                    (curses.color_pair(3) | curses.A_BOLD))
            chat_window.refresh()
            input_window.clear()
            input_window.refresh()


def chat_update(sock):
    data = sock.recv(4096)
    if data:
        handler = message_handlers[data[0]]
        handler(data)

def show_message(room, sender, message):
    if room == current_room:
        fmt_message = "{u}: {m}".format(u=sender, m=message)
        if chat_window is None:
            sys.stdout.write(fmt_message)
            sys.stdout.flush()
        else:
            chat_window.addstr(fmt_message)
            chat_window.refresh()

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
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1',8000))

# Add stdin to the rset so that we know when to read from the user
    rset = [ s, sys.stdin ]

# Null wset
    wset = []

    try:
        data = s.recv(4096)

        # Username Prompt Loop
        while True:
            handler = message_handlers[data[0]]
            handler(data)
            global user_name
            user_name = raw_input()
            s.send(user_name + "\n")
            data = s.recv(4096)
            handler = message_handlers[data[0]]
            if handler(data) is SERVER_COMMAND:
                break

        if args.curses:
            global input_window
            global chat_window
            screen = curses.initscr()
            input_window, chat_window = setup_curses(screen, data)

        # Main chat exchange loop
        while True:
            readable, writable, excepts = select.select(rset, wset, rset)

            for fd in readable:
                if fd is sys.stdin:
                    user_input(s)
                else:
                    chat_update(s)

    except KeyboardInterrupt:
        pass

    finally:
        s.close()
        curses.endwin()

if __name__=='__main__':
    main()
