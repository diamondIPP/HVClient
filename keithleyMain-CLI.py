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

#import Tkinter
import time
#from threading import Thread

# Command Line Interface
from keithleyCLI import CLI


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
# Read  and handle the config file
#######################################

# Implement...


#######################################
# Hand over to command line interface
#######################################

myCLI = CLI()
myCLI.set_keithleys(keithleys)
myCLI.cmdloop()


# root = Tkinter.Tk()
# root.minsize(300, 300)
# root.maxsize(300, 300)
#
# li_vars   = []
# li_labels = []
# for _ in range(6):
#     tmp = Tkinter.StringVar()
#     self.li_vars.append( tmp )
#     self.li_labels.append( Tkinter.Label(root, textvariable = tmp))
#
# [ l.pack() for l in self.li_labels]
#
# while True:
#     time.sleep(1)
#     [var.set(str(time.time())) for var in li_vars]
#     root.update()
