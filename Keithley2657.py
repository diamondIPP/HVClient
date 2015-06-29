__author__ = 'bachmair'
# implementation of Keithley 237
# based on HV_interface class

# ============================
# IMPORTS
# ============================
import ConfigParser
import serial
from HV_interface import HVInterface
from time import sleep,time

# ============================
# CONSTANTS
# ============================
ON = 1
OFF = 0


# ============================
# MAIN CLASS
# ============================
class Keithley2657(HVInterface):
    def __init__(self, config, device_no=1, hot_start=False):
        HVInterface.__init__(self, config, device_no, hot_start)


    def open_tcp_connection(self):
        pass