#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------
#       Tool to select to correct devices
# created on Aug 13th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from json import loads
from devices.ISEG import ISEG
from devices.Keithley24XX import Keithley24XX
from devices.Keithley23X import Keithley23X
from devices.Keithley2657 import Keithley2657
from devices.Keithley6517B import Keithley6517B
from argparse import ArgumentParser
from ConfigParser import ConfigParser
from os.path import dirname, realpath, join
import signal
from devices.Device import Device

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
    print '\n=============CONFIGURATION============='
    device_nrs = loads(config.get('Main', 'devices'))
    print 'Loading HV devices: {}'.format(device_nrs)
    print '======================================='
    print '\n=============INSTANTIATION============='
    return [init_device(config, nr, hot_start, print_logs) for nr in device_nrs]


def get_log_dirs(config):
    dev_list = [Device(config, nr, hot_start=True, init_logger=False) for nr in loads(config.get('Main', 'devices'))]
    return [device.Logger[ch].LogFileDir for device in dev_list for ch in device.ActiveChannels]


def init_device(config, device_nr, hot_start, print_logs=False):
    section = 'HV{}'.format(device_nr)
    model = config.get(section, 'model')
    print 'Instantiating {}'.format(model)
    device = device_dic[model](config, device_nr, hot_start, print_logs)
    print 'successfully instantiated {} with model number {}'.format(device.DeviceName, device.Model)
    print 'active channels: {}'.format(device.ActiveChannels)
    return device


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('--config', '-c', help='Config file', default='keithley.cfg')
    parser.add_argument('--restart', '-R', action='store_true', help='restart hv devices (turn all OFF and set voltage to 0)')
    args = parser.parse_args()

    conf = ConfigParser()
    conf.read(join(dirname(realpath(__file__)), 'config', args.config))

    devices = get_devices(conf, not args.restart, print_logs=True)

    for dev in devices:
        dev.start()

    def signal_handler(signal, frame):
        print 'Received SIGINT bla'
        for dev in devices:
            dev.IsKilled = True

    signal.signal(signal.SIGINT, signal_handler)
