# -*- coding: utf-8 -*-

import curses
import curses.textpad

#import tkinter as tk
#from tkinter import Tk, RIGHT, LEFT, BOTH, RAISED, Frame, Button, ttk
#from tkinter.ttk import Style

#########################################################
# Displayer classes must implement:                     #
#   get_message, show_room_name, show_message and close #
#########################################################

#class TkDisplayer(Tk):
    #def __init__(self):
#        Tk.__init__(self)
#        self.initUI()

    #def initUI(self):


    #def close(self):
#        from _tkinter import TclError
#        try:
#            self.destroy()
#        except TclError as e:
#            print(e)

class CursesDisplayer(object):
    def __init__(self):
        self.root = curses.initscr()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.curs_set(0)

        self.root_height, self.root_width = self.root.getmaxyx()

        # input_window is the box for user input
        self.input_window = curses.newwin(1, self.root_width,
                self.root_height-1, 0)
        self.input_window.bkgd(' ', curses.color_pair(1))
        self.input_window.attron(curses.A_BOLD)
        self.input_window.scrollok(True)

        # chat_window is updated with other user data
        self.chat_window = curses.newwin(self.root_height-1, self.root_width,
                0, 0)
        self.chat_window.bkgd(' ', curses.color_pair(2))
        self.chat_window.attron(curses.A_BOLD)
        self.chat_window.scrollok(True)
        #self.chat_window.addstr(current_room + "\n",
                #curses.color_pair(4) | curses.A_BOLD)

        self.input_window.refresh()
        self.chat_window.refresh()

    def get_message(self):
        return self.input_window.getstr()

    def show_room_name(self, message):
        self.chat_window.clear()
        self.chat_window.addstr(message+"\n",
                (curses.color_pair(4) | curses.A_BOLD))
        self.chat_window.refresh()

    def show_message(self, message):
        self.chat_window.addstr(message,
                (curses.color_pair(3) | curses.A_BOLD))
        self.chat_window.refresh()
        self.input_window.clear()
        self.input_window.refresh()

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()
        return

    def close(self):
        curses.endwin()


#def TerminalDisplayer(object):
    #def __init__():
        #pass

    #def get_message():
        #return raw_input()

    #def show_message():
