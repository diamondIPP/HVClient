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

# Command Line Interface
from CLI import CLI
import DeviceReader


#######################################
# Argument Parser
#######################################
parser = argparse.ArgumentParser(description='Keithley Power Supply steering and readout software')
parser.add_argument('--config', '-c', help='Config file', default='keithley.cfg')
parser.add_argument('--hotstart', '-H', action='store_true',
                    help='Hot start (leave Keithleys ON and current voltage)')

args = parser.parse_args()
print '\nConfiguration file:', args.config
print 'Hotstart:', args.hotstart


#######################################
# CONFIGPARSER
#######################################
config = ConfigParser.ConfigParser()
config.read(args.config)


#######################################
# QUERY FOR HOTSTART
#######################################
def query(hot=0):
    string = raw_input()
    if string.lower() in ['yes', 'y', '1']:
        hot_start = (True if hot == 1 else False)
    else:
        print 'exiting program'
        sys.exit(-2)
    return hot_start

if args.hotstart:
    print '\nENABLED HOTSTART. All Keitlheys should already be ON\n'
    print 'You want to have HOTSTART enabled? (yes/no)',
    hotstart = query(1)
else:
    print '\nDISABLED HOTSTART. All Keitlheys will be reset.\n'
    print 'You want to have HOTSTART disabled? (yes/no)',
    hotstart = query(0)


#######################################
# Spawn command line interface
#######################################

# The CLI gets its own thread. Tkinter (display GUI) needs to be the
# main thread.
devices = DeviceReader.get_devices(config, hotstart)
for k in devices:
    devices[k].start()
myCLI = CLI()
myCLI.set_keithleys(devices)
myCLI.start()


#######################################
# Signal handling
#######################################
def signal_handler(signal, frame):
    print 'Received SIGINT'
    print 'press ctrl + D to exit the interpreter'

signal.signal(signal.SIGINT, signal_handler)


#######################################
# Prepare GUI
#######################################

root = Tkinter.Tk()
root.minsize(1000, 200)  # x/y
root.maxsize(1000, 200)

# Create Tk-variable and -label objects for each keithley
# A label is an object and the variable is the content
di_vars = {}
di_labels = {}

# create labels and hook them up with variables
for name in devices.keys():
    tmp = Tkinter.StringVar()
    di_vars[name] = tmp
    di_labels[name] = Tkinter.Label(root, textvariable=tmp, font="Courier", justify=Tkinter.LEFT)
    # if di_labels[name]:
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
    while time.time() - now < 1:
        time.sleep(.2)
    now = time.time()

    # Loop over the keithleys, get the voltages and update the display
    for k, v in sorted(devices.iteritems(), key=lambda x: x[0]):

        if not myCLI.running:
            break

        status = v.get_status()
        # v.serial.flushInput()

        if status:

            # First try to change the voltage
            # v.ramp()

            # Then update GUI and display
            value = datetime.datetime.fromtimestamp(v.get_update_time())
            voltage = v.get_bias()
            current = v.get_current()

            # Build display string
            display_string = k
            display_string += ": U: {0:7.1f} V      I: {1:10.2e} muA    ".format(voltage, current / 1e-6)
            display_string += value.strftime('%H:%M:%S')
            if v.manual:
                display_string = ' MANUAL'
            setBias = v.get_target_bias()
            if v.is_ramping():
                display_string += " ramping to " + str(setBias)

            # Display
            di_vars[k].set(display_string)

        else:
            value = datetime.datetime.fromtimestamp(time.time())
            display_string = k + ": OFF " + value.strftime('%H:%M:%S')
            if v.manual:
                display_string = ' MANUAL'
            di_vars[k].set(display_string)

        v.isBusy = False
        root.update()
        # end of Keithley loop
# End of Main GUI loop
