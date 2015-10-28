# ============================
# IMPORTS
# ============================
from HV_Device import HVDevice
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
            devices[name] = HVDevice(config, i, hot_start)
        pass
    print '---------------------------------------'
    return devices
