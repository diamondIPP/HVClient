#!/usr/bin/env python
# --------------------------------------------------------
#       Device for testing
# created on September 17th 2020 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from copy import deepcopy
from numpy import ones, array
from numpy.random import rand, normal, randint
from .device import *


class Dummy(Device):

    N = 0

    def __init__(self, config, device_no=1, hot_start=False, init_logger=False):

        Device.__init__(self, config, device_no, hot_start, init_logger)

        # Basics
        self.Config = config

        self.Model = self.get_model_name()

        # Info
        self.Busy = False
        self.last_write = ''
        self.LastMeasurement = -1
        self.LastCurrents = []
        self.LastVoltages = []
        self.LastStatusUpdate = -1
        self.LastStatus = ['On' if hot_start else 'Off'] * self.NChannels
        self.lastVoltage = 0
        self.CanRamp = False
        self.Output = ones(self.NChannels, 'bool')

        self.BiasNow = array([0 if ch not in self.ActiveChannels else round_down_to(self.MinBias[ch] * rand(), 10) for ch in range(self.NChannels)])
        self.TargetBias = deepcopy(self.BiasNow)
        self.SeedCurrent = randint(10, 80, self.NChannels) * 1e-9
        self.hot_start()

    # --------------------------------------
    # region SET METHODS
    def set_output(self, status, channel=None):
        self.Output[channel] = status

    def set_bias(self, voltage, channel=None):
        self.BiasNow[channel] = voltage

    def set_current(self, current, channel):
        self.CurrentNow[channel] = current

    def read_current(self):
        return normal(self.SeedCurrent, 5e-9)

    def read_voltage(self):
        return self.BiasNow

    def read_iv(self):
        now = time()
        sleep(1)
        if now - self.LastMeasurement > .5:
            self.LastCurrents = self.read_current()
            self.LastVoltages = self.read_voltage()
            self.LastMeasurement = now
        return [{'voltage': v, 'current': c} for v, c in zip(self.LastVoltages, self.LastCurrents)]
    # endregion SET METHODS
    # --------------------------------------

    # --------------------------------------
    # region GET METHODS
    @staticmethod
    def get_model_name():
        info(colored('Init dummy device {}'.format(Dummy.N), 'green'))
        Dummy.N += 1
        return 'Dummy{}'.format(Dummy.N - 1)

    def get_channel_voltage(self, ch):
        return self.BiasNow[ch]

    def get_output_status(self, channel=None):
        return self.Output[channel]

    def get_all_channel_status(self):
        return self.LastStatus


if __name__ == '__main__':

    conf = load_config('config/keithley', 'cfg')
    d = Dummy(conf, loads(conf.get('Main', 'devices'))[0], True)
    d.update_status()
    # d.start()
