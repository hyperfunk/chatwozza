#!/usr/bin/python2

import re
import socket
import select
import sys

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect(('127.0.0.1',8000))

# Add stdin to the rset so that we know when to read from the user
rset = [ s, sys.stdin ]

# Null wset
wset = []

# so could totally use some more "obscure" leading key that gets stripped

_WELCOME_KEY = "Welcome"

r = re.compile("{key}.+".format(key=_WELCOME_KEY))

try:
    data = s.recv(4096)

    # Prompt for username until we get the welcome message
    while True:
        sys.stdout.write(data)
        uname = raw_input()
        s.send(uname + "\n")
        data = s.recv(4096)
        if r.match(data):
            print data
            break

    while True:
        readable, writable, excepts = select.select(rset, wset, rset)

        for fd in readable:

            if fd is sys.stdin:
                data = raw_input()
            if data:
                s.send(data + "\n")
            else:
                data = s.recv(4096)
                print data.rstrip('\n')

except KeyboardInterrupt:
    pass

finally:
    s.close()
