#!/usr/bin/env python

"""
Main program for Keithley Power Supply steering and readout.
"""


#######################################
# Imports
#######################################

# Standard Python Modules
import sys
import signal
import time
import ConfigParser
import argparse
import datetime
import Tkinter
import math
from threading import Thread

# Command Line Interface
from keithleyCLI import CLI
import keithleyReader


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
# Spawn command line interface
#######################################

# The CLI gets its own thread. Tkinter (display GUI) needs to be the
# main thread.

keithleys = keithleyReader.get_keithleys(config)
for k in keithleys:
    keithleys[k].start()
myCLI = CLI()
myCLI.set_keithleys(keithleys)
myCLI.start()


#######################################
# Signal handling
# (make sure we can kill the GUI with
#   ctrl+c)
#######################################

def signal_handler(signal, frame):
    print 'Received SIGINT'
    myCLI.stop()
    for k in keithleys:
        keithleys[k].isKilled=True
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


#######################################
# Prepare GUI
#######################################

root = Tkinter.Tk()
root.minsize(1000, 200) # x/y
root.maxsize(1000, 200)

# Create Tk-variable and -label objects for each keithley
# A label is an object and the variable is the content
di_vars   = {}
di_labels = {}

# create labels and hook them up with variables
for name in keithleys.keys():
    tmp = Tkinter.StringVar()
    di_vars[name] = tmp
    di_labels[name] = Tkinter.Label(root, textvariable = tmp,font=("Courier"),justify=Tkinter.LEFT)
    #if di_labels[name]:
    #    di_labels[name].pack(side='left')

# add the labels to the output window
for k in sorted(di_labels.keys()):
    di_labels[k].pack(padx=10)


#######################################
# Main GUI loop
#######################################

now = time.time()
while myCLI.running:

    # Make sure enough time has passed before we poll again
    while time.time()-now < 1:
        time.sleep(.2)
    now = time.time()

    # Loop over the keithleys, get the voltages and update the display
    for k,v in sorted(keithleys.iteritems(), key = lambda x:x[0]):

        if not myCLI.running:
            break

        status = v.get_status()
        #v.serial.flushInput()

        if status:

            # First try to change the voltage
            #v.doRamp()

            # Then update GUI and display
            value = datetime.datetime.fromtimestamp(v.get_update_time())
            voltage = v.get_bias()
            current = v.get_current()

            # Build display string
            display_string = k
            display_string+= ": U: {0:7.1f} V      I: {1:10.2e} muA    ".format(voltage, current/1e-6)
            display_string+= value.strftime('%H:%M:%S')
            if v.manual:
                display_string = ' MANUAL'
            setBias = v.get_target_bias()
            if v.is_ramping():
                display_string += " ramping to " + str(setBias)

            # Build logging string
            logging_string = k
            logging_string += value.strftime(' %H:%M:%S ')
            logging_string += "{0:10.3e} {1:10.3e}".format(voltage, current)

            # Display and log...
            di_vars[k].set( display_string)
            # (the logfile only exists while we are running)
            if myCLI.running:
                myCLI.logfile.write( logging_string + "\n")


        else:
            value = datetime.datetime.fromtimestamp(time.time())
            display_string = k+": OFF " + value.strftime('%H:%M:%S')
            if v.manual:
                display_string = ' MANUAL'
            logging_string = k+" "+value.strftime('%H:%M:%S')+" OFF"
            di_vars[k].set( display_string )
            # (the logfile only exists while we are running)
            if myCLI.running:
                myCLI.logfile.write( logging_string + "\n")

        v.isBusy=False
        root.update()
    # end of Keithley loop
# End of Main GUI loop
