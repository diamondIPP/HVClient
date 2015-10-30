#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
from HVGui import HVGui

# Command Line Interface
from CLI import CLI
import DeviceReader


#######################################
# Argument Parser
#######################################
parser = argparse.ArgumentParser(description='Keithley Power Supply steering and readout software')
parser.add_argument('--config', '-c', help='Config file', default='config/keithley.cfg')
parser.add_argument('--nogui',  help='No Gui mode', action='store_true')
parser.add_argument('--hotstart', '-H', action='store_true',
                    help='Hot start (leave Keithleys ON and current voltage)')

args = parser.parse_args()
print '\nConfiguration file:', args.config
print 'Hotstart:', args.hotstart
print 'No Gui',args.nogui


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
    print 'You want to proceed? (yes/no)',
    hotstart = query(1)
else:
    print '\nDISABLED HOTSTART. All Keitlheys will be reset.\n'
    print 'You want to proceed? (yes/no)',
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
    print 'You have to press ctrl + D to exit the interpreter'


signal.signal(signal.SIGINT, signal_handler)


#######################################
# Prepare GUI
#######################################
# devices = {'HV4':{'name':'TEST','voltage':-200,'current':13e-6,}}
with_gui = not args.nogui
if with_gui:
    root = HVGui(devices)

#######################################
# Main GUI loop
#######################################

# now = time.time()
while myCLI.running:

    if with_gui:
        if root.destroyed:
            print 'ROOT DEstroyed'
            myCLI.do_exit()
            myCLI.do_EOF()
    try:
        if with_gui:
            root.update()
    except:
        myCLI.do_exit()
        myCLI.do_EOF()

        break
    # Make sure enough time has passed before we poll again
    #     while time.time() - now < 1:
    #         time.sleep(.1)
    # now = time.time()

    # Loop over the keithleys, get the voltages and update the display
    string_len = max([len(v.get_device_name()) for k, v in devices.items()])
    for k, v in sorted(devices.iteritems(), key=lambda x: x[0]):

        if not myCLI.running:
            break
        status = v.get_status()
        # v.serial.flushInput()
        if with_gui:
            root.set_status(k, status)
        if status:
            # First try to change the voltage
            # v.ramp()
            # Then update GUI and display
            value = datetime.datetime.fromtimestamp(v.get_update_time())
            voltage = v.get_bias()
            current = v.get_current()
            #             print 'add measurement',k,v.get_update_time(),v.get_current(),v.get_bias(),v.get_device_name()
            if with_gui:
                root.add_measurement(k, v.get_update_time(), v.get_bias(), v.get_current(), v.get_device_name())
                if v.manual:
                    root.set_mode(k, "MANUAL")
                elif v.is_ramping():
                    root.set_mode(k, "RAMPING")
                else:
                    root.set_mode(k, "NORMAL")
                root.set_target_bias(k, v.target_bias)

if with_gui:
    root._quit()
if myCLI.running:
    myCLI.onecmd('exit\n')
    # myCLI.cmdqueue.append('exit\n')
    # print myCLI.cmdqueue,type(myCLI.cmdqueue)
    # print 'Press enter to quit'

# ===================================
# HISTORICAL??
#             if v.manual:
#                 display_string = ' MANUAL'
#             setBias = v.get_target_bias()
#             if v.is_ramping():
#                 display_string += " ramping to " + str(setBias)
# 
#             # Display
#             di_vars[k].set(display_string)

#         else:
#             value = datetime.datetime.fromtimestamp(time.time())
#             display_string = k + ": OFF " + value.strftime('%H:%M:%S')
#             if v.manual:
#                 display_string = ' MANUAL'
#             di_vars[k].set(display_string)

#         v.isBusy = False
#         root.update()
# end of Keithley loop
# End of Main GUI loop
