#!/usr/bin/python2

import socket
import select

def run_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.bind(("0.0.0.0", 8000))
    s.listen(5)

    # Set up read set
    rset = [ s ]

    # Null write set
    wset = [ ]

    # socket:username dict
    users = {}

    def username_prompt(sock):
        sock.send("Please choose a user name: ")

    while True:

        readable, writable, excepts = select.select(rset, wset, rset)

        for sock in readable:

            if sock is s:
                fd, ip = s.accept()

                if ip != '':
                    print "Connection from {addr}".format(addr=ip[0])
                    rset.append(fd)
                    username_prompt(fd)
            else:
                data = sock.recv(4096)
                if data:
                    if sock in users.keys():
                        for client in users.keys():
                            if client is not sock:
                                client.send("{u}: {msg}".format(u=users[sock],
                                                                msg=data))
                    else:
                        username = data[:-1]
                        if username in users.values():
                            sock.send("Username already taken\n")
                            username_prompt(sock)
                        else:
                            # each sock.recv string ends with "empty_chat"+"\n"
			    # this appears to be telnet behaviour - it sends carriage return line feed
			    # the client only sends a newline so I have changed to 1 for now
                            users[sock] = username

                else:
                    sock.close()
                    rset.remove(sock)

if __name__=='__main__':
    run_server()
