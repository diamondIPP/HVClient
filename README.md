# ETH High Voltage Client

Client to control and read out several HV supply units


##Installation:

needs packages:

 - tkinter:
Ubuntu: sudo apt-get install python-tk idle python-pmw python-imaging
- visa: 
Ubuntu: sudo easy_install pyvisa
- termcolor, serial, matplotlib:
sudo pip install termcolor serial matplotlib
- copy 88-keithley.rules to /etc/udev/rules-d/
- enter: sudo reload udev

## Running

 - ./gui.py starts the control panel always in hotstart if the device is on
 - ./gui.py -l (-s) starts the current viewer with start time -s (formats: hh:mm or dd.mm.) 

