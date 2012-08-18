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

r = re.compile("Welcome.+")

try:
    data = s.recv(4096)

    # Prompt for username until we get the welcome message
    while True:
        sys.stdout.write(data)
        uname = raw_input()
        s.send(uname + "\n")
        data = s.recv(4096)

        match = r.match(data)
        if not match:
            continue
        else:
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

finally:
    s.close()
