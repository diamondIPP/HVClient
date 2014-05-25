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
    di_labels[name] = Tkinter.Label(root, textvariable = tmp)

# add the labels to the output window
for k in sorted(di_labels.keys()):
    di_labels[k].pack()


#######################################
# Main GUI loop
#######################################

now = time.time()
while myCLI.running:
    
    # Make sure enough time has passed before we poll again
    while time.time()-now < 1:
        time.sleep(.05)
    now = time.time()

    # Loop over the keithleys, get the voltages and update the display
    for k,v in sorted(keithleys.iteritems(), key = lambda x:x[0]):
        v.wait_for_device()
        v.isBusy=True
        status = v.getOutputStatus()
        #v.serial.flushInput()

        if status:

            # Maybe update voltage (we remember the measurement from the last loop)
            # (the step we can make in voltage is the ramp-speed times 
            # how many seconds passed since last change)
            deltaU = v.bias - v.lastBias
            Ustep = abs(v.ramp * (time.time() - v.lastUChange))
            if abs(deltaU) > 0.1:
                if abs(deltaU) <= Ustep:
                    v.setVoltage( v.bias )
                    v.lastUChange = time.time()
                else:
                    v.setVoltage( v.lastBias + math.copysign( Ustep, deltaU ))
                    v.lastUChange = time.time()
                
            # Then updaye U/I and display
            value = datetime.datetime.fromtimestamp(time.time())
            [voltage, current] = [float(x) for x in v.readIV().split(" ")][:2]            

            # Build display string
            display_string = k
            display_string+= ": U: {0:7.1f} V      I: {1:10.2e} A    ".format(voltage, current)
            display_string+= value.strftime('%H:%M:%S')
            
            if abs( v.bias - voltage) > 0.1:
                display_string += " ramping"
            
            di_vars[k].set( display_string)  
            
            v.lastBias = voltage

        else:
            di_vars[k].set( k+": OFF")
        v.isBusy=False
        root.update()
    # end of Keithley loop        
# End of Main GUI loop
