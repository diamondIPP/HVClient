#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------
#       Tool to select to correct devices
# created on Aug 13th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

import signal
from argparse import ArgumentParser
from devices.device import *
from devices.dummy import Dummy
from devices.ISEG import ISEG
from devices.Keithley23X import Keithley23X
from devices.Keithley24XX import Keithley24XX
from devices.Keithley2657 import Keithley2657
from devices.Keithley6517B import Keithley6517B
from src.config import Config

device_dic = {'2400': Keithley24XX,
              '2410': Keithley24XX,
              '236': Keithley23X,
              '237': Keithley23X,
              '238': Keithley23X,
              '6517B': Keithley6517B,
              '2657A': Keithley2657,
              'NHS-6220n': ISEG,
              'NHS-6220x': ISEG}


def get_devices(config, hot_start, print_logs=False):
    print('\n=============CONFIGURATION=============')
    c = Config(config)
    device_nrs = c.get_active_devices()
    print('Loading HV devices: {}'.format(device_nrs))
    print('=======================================')
    print('\n=============INSTANTIATION=============')
    return [init_device(nr, config, hot_start, print_logs) for nr in device_nrs]


def get_logging_devices(config, start_time):
    c = Config(config)
    return [Device(nr, config, hot_start=True, init_logger=False, start_time=start_time) for nr in c.get_active_devices()]


def get_dummies(config):
    c = Config(config)
    return [Dummy(nr, config, hot_start=True, init_logger=False) for nr in c.get_active_devices()]


def init_device(config, device_nr, hot_start, print_logs=False):
    section = 'HV{}'.format(device_nr)
    model = config.get(section, 'model')
    print('Instantiating {}'.format(model))
    device = device_dic[model](device_nr, config.MainFile, hot_start, print_logs)
    print('successfully instantiated {} with model number {}'.format(device.Names, device.Model))
    print('active channels: {}'.format(device.ActiveChannels))
    return device


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('--config', '-c', help='Config file', default='main')
    parser.add_argument('--restart', '-R', action='store_true', help='restart hv devices (turn all OFF and set voltage to 0)')
    args = parser.parse_args()

    devices = get_devices(args.config, not args.restart, print_logs=True)

    for dev in devices:
        dev.start()

    def signal_handler(signal, frame):
        print('Received SIGINT bla')
        for d in devices:
            d.IsKilled = True

    signal.signal(signal.SIGINT, signal_handler)
