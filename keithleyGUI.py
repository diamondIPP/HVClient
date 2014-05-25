#!/usr/bin/env python

#######################################
# Imports
#######################################

import Tkinter
import time
from threading import Thread

class keithleyGUI(Thread):

    def __init__(self):

        super(keithleyGUI, self).__init__()
        root = Tkinter.Tk()
        root.minsize(300, 300)
        root.maxsize(300, 300)

        self.li_vars   = []
        self.li_labels = []
        for _ in range(6):
            tmp = Tkinter.StringVar()
            self.li_vars.append( tmp )
            self.li_labels.append( Tkinter.Label(root, textvariable = tmp))

        [ l.pack() for l in self.li_labels]

    def run(self):
        while True:
            time.sleep(1)
            [var.set(str(time.time())) for var in self.li_vars]
            root.update()
