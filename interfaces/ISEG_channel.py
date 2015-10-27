__author__ = 'bachmair'
# implementation of single channel of ISEG NIM Power supplies
# based on HV_interface class and ISEG class

# ============================
# IMPORTS
# ============================
import ConfigParser
import os
import sys
import inspect
import ISEG

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from HV_interface import HVInterface
import serial
from time import sleep, time

# ============================
# CONSTANTS
# ============================
ON = 1
OFF = 0


# ============================
# MAIN CLASS
# ============================
class ISEG_channel(HVInterface):
    def __init__(self, config, channel, iseg_module = None, hot_start=False):
        self.nchannels = 1
        self.iseg = iseg_module
        self.ch = channel
        self.name = self.iseg.name+'_CH%d'%self.ch
        self.section_name = self.iseg.section_name
        self.model_number = self.iseg.model_number
        self.init_channel(hot_start)


    def init_channel(self,hot_start):
        pass

    def set_output(self, status):
        return self.iseg.set_output(status, self.ch)

    def set_bias(self, voltage):
        return self.set_channel_voltage(voltage)

    def set_channel_voltage(self, voltage):
        return self.iseg.set_channel_voltage(voltage, self.ch)

    def set_emergency_off(self):
        return self.iseg.set_emergency_off(self.ch)

    def set_emergency_clear(self):
        return self.iseg.set_emergency_clear(self.ch)

    def set_channel_voltage_bound(self, voltage_bound):
        return self.iseg.set_channel_voltage_bound(voltage_bound, self.ch)

    def set_channel_current(self, current):
        return self.iseg.set_channel_current(current, self.ch)

    def set_channel_current_bound(self, current_bound):
        return self.iseg.set_channel_current_bound(current_bound, self.ch)

    def clear_channel_events(self):
        return self.iseg.clear_channel_events()

    def set_channel_event_mask(self, mask_word):
        return self.iseg.set_channel_event_mask(mask_word, self.ch)

    def read_current(self):
        return self.iseg.read_current(self.ch)[0]

    def read_voltage(self):
        return self.iseg.read_voltage(self.ch)[0]

    def read_iv(self):
        return self.iseg.read_iv()[self.ch]

    def get_channel_voltage(self):
        return self.iseg.get_channel_voltage(self.ch)[0]

    def get_output_status(self):
        return self.iseg.get_output_status(self.ch)[0]

    def query_set_voltage(self):
        return self.iseg.query_set_voltage(self.ch)[0]

    def query_voltage_limit(self):
        return self.iseg.query_voltage_limit(self.ch)[0]

    def query_voltage_nominal(self):
        return self.iseg.query_voltage_nominal(self.ch)[0]

    def query_voltage_bounds(self):
        return self.iseg.query_voltage_bounds(self.ch)[0]

    def query_channel_on(self):
        return self.iseg.query_channel_on(self.ch)[0]

    def query_emergency_bit(self):
        return self.iseg.query_emergency_bit(self.ch)[0]

    def query_set_current(self):
        return self.iseg.query_set_current(self.ch)[0]

    def query_set_current_limit(self):
        return self.iseg.query_set_current_limit(self.ch)[0]

    def query_set_current_nominal(self):
        return self.iseg.query_set_current_nominal(self.ch)[0]

    def query_set_current_bounds(self):
        return self.iseg.query_set_current_bounds(self.ch)[0]

    def query_voltage_ramp_speed(self):
        return self.iseg.query_channel_voltage_ramp_speed(self.ch)[0]

    def query_current_ramp_speed(self):
        return self.iseg.query_channel_current_ramp_speed(self.ch)[0]

    def get_channel_status(self):
        return self.iseg.get_channel_status(self.ch)


if __name__ == '__main__':
    conf = ConfigParser.ConfigParser()
    conf.read('../config/keithley.cfg')
    iseg = ISEG.ISEG(conf, 7, False)
    channels = {}
    hot_start = False
    for i in range(iseg.get_n_channels()):
        channels[i] = ISEG_channel(conf, channel=i, iseg_module = iseg, hot_start=hot_start)

