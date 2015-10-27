# ============================
# IMPORTS
# ============================
from HV_Device import HVDevice
from interfaces.ISEG import ISEG
from ConfigParser import NoOptionError
import json


def get_devices(config, hot_start):
    devices = {}
    try:
        device_numbers = json.loads(config.get('Main','devices'))
        print device_numbers
    except NoOptionError, err:
        print err
    print '\nOptions from config file:'
    main = config.sections()[0]
    print main, config.options(main)
    print 'Found %d devices in config file: %s' % (len(device_numbers), device_numbers)
    for i in device_numbers:
        sec = 'HV' + str(i)
        print sec, config.options(sec)
    for i in device_numbers:
        name = 'HV%d' % i
        if config.has_section(name):
            if config.get(name,'model').startswith('NHS'):
                print 'special module with multiple channels'
                module = ISEG(config,i,hot_start)
                for ch in range(module.query_module_channels()):
                    devices[name+'_CH%d'%ch] = HVDevice(config,i,hot_start,module=module,channel=ch)
            else:
                devices[name] = HVDevice(config, i, hot_start)
        pass
    return devices
