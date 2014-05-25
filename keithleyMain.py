#!/usr/bin/env python

""" Main program for Keithley Power Supply steering and readout.
"""


#######################################
# Imports
#######################################

# Standard Python Modules
import sys
import keithleyReader
import ConfigParser
import argparse
import datetime

import Tkinter
import time
from threading import Thread

# Command Line Interface
from keithleyCLI import CLI


import signal
import sys
def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

#######################################
# Argument Parser
#######################################

parser = argparse.ArgumentParser(description='Keithley Power Supply steering and readout software')
parser.add_argument('--config','-c',help='Config file',default='keithley.cfg')

args = parser.parse_args()
print args

config = ConfigParser.ConfigParser()
config.read(args.config)


#######################################
# Definitions
#######################################

filename_config = "config.txt"
keithleys = keithleyReader.get_keithleys(config)


#######################################
# Spawn line interface
#######################################

myCLI = CLI()
myCLI.set_keithleys(keithleys)
myCLI.start()

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    myCLI.stop()
    sys.exit(0)





#######################################
# Prepare GUI
#######################################

root = Tkinter.Tk()
root.minsize(1000, 200)
root.maxsize(1000, 200)

di_vars   = {}
di_labels = {}

for name in keithleys.keys():
    tmp = Tkinter.StringVar()
    di_vars[name] = tmp
    di_labels[name] = Tkinter.Label(root, textvariable = tmp)

for k in sorted(di_labels.keys()):
    di_labels[k].pack()
now = time.time()
while myCLI.running:
    while time.time()-now < 1:
            time.sleep(.05)
    now = time.time()

    for k,v in sorted(keithleys.iteritems(), key = lambda x:x[0]):
        v.wait_for_device()
        v.isBusy=True
        status = v.getOutputStatus()
        #v.serial.flushInput()

        value = datetime.datetime.fromtimestamp(time.time())

        if status:
            IV = v.readIV()
            di_vars[k].set( k+": "+str(IV)+ "   " +value.strftime('%H:%M:%S'))
        else:
            di_vars[k].set( k+": OFF")
        v.isBusy=False
        root.update()
