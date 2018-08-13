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

device_dic = {'2400': Keithley24XX,
              '2410': Keithley24XX,
              '236': Keithley23X,
              '237': Keithley23X,
              '238': Keithley23X,
              '6517B': Keithley6517B,
              '2657A': Keithley2657,
              'NHS-6220n': ISEG,
              'NHS-6220x': ISEG}


def get_devices(config, hot_start):
    print '\n=============CONFIGURATION============='
    device_nrs = loads(config.get('Main', 'devices'))
    print 'Loading HV devices: {}'.format(device_nrs)
    print '======================================='
    print '\n=============INSTANTIATION============='
    return [init_device(config, nr, hot_start) for nr in device_nrs]


def init_device(config, device_nr, hot_start):
    section = 'HV{}'.format(device_nr)
    model = config.get(section, 'model')
    print 'Instatiating {}'.format(model)
    device = device_dic[model](config, device_nr, hot_start)
    print 'successfully instantiated {} with model number {}'.format(device.DeviceName, device.Model)
    print 'active channels: {}'.format(device.ActiveChannels)
    return device
