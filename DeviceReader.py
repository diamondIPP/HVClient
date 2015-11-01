# ============================
# IMPORTS
# ============================
from HV_Device import HVDevice
from interfaces.ISEG import ISEG
from ConfigParser import NoOptionError
import json


def get_devices(config, hot_start):
    devices = {}
    device_numbers = []
    print '\n=============CONFIGURATION============='
    try:
        device_numbers = json.loads(config.get('Main', 'devices'))
        print 'Device numbers:', device_numbers
    except NoOptionError, err:
        print err
    print 'Options from config file:'
    main = config.sections()[0]
    print main, config.options(main)
    print 'Found %d devices in config file' % (len(device_numbers))
    for i in device_numbers:
        sec = 'HV' + str(i)
        print sec, config.options(sec)
    print '======================================='
    for i in device_numbers:
        name = 'HV%d' % i
        if config.has_section(name):
            if config.get(name,'model').startswith('NHS'):
                print 'special module with multiple channels'
                module = ISEG(config,i,hot_start)
                for ch in module.get_list_of_active_channels():
                    devices[name+'_CH%d'%ch] = HVDevice(config,i,hot_start,module=module,channel=ch)
            else:
                devices[name] = HVDevice(config, i, hot_start)
        pass
    print '---------------------------------------'
    return devices
