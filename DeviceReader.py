# ============================
# IMPORTS
# ============================
from HV_Device import HVDevice
from ConfigParser import NoOptionError


def get_devices(config, hot_start):
    devices = {}
    try:
        n_devices = config.getint('Main', 'n_devices')
    except NoOptionError, err:
        print err
        n_devices = 0
    print '\nOptions from config file:'
    main = config.sections()[0]
    print main, config.options(main)
    print 'Found %d devices in config file' % n_devices
    for i in range(1, n_devices + 1):
        sec = 'HV' + str(i)
        print sec, config.options(sec)
    for i in range(1, n_devices + 1):
        name = 'HV%d' % i
        if config.has_section(name):
            devices[name] = HVDevice(config, i, hot_start)
        pass
    return devices
