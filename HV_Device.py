__author__ = 'testbeam'
import HV_interface
from keithley24XX_interface import *
# for *_interface do import bla
class HV_Device(Thread):
    def __init__(self,config,device_no,hot_start):
        self.interface = None
        self.init_interface(config,device_no,hot_start)

    def init_interface(self,config,device_no,hot_start):
        #if statements for model name
        self.interface = Keithley24XX(config,device_no,hot_start)
