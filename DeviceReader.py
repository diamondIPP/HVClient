# ============================
# IMPORTS
# ============================
from HV_Device import HVDevice
from ConfigParser import NoOptionError


def get_keithleys(config, hot_start):
    keithleys = {}
    try:
        for sec in config.sections():
            print sec, config.options(sec)
        n_keithleys = config.getint('Main', 'nkeithleys')
    except NoOptionError, err:
        print err
        n_keithleys = 0
    print 'Found %d devices' % n_keithleys
    for i in range(1, n_keithleys + 1):
        name = 'HV%d' % i
        if config.has_section(name):
            keithleys[name] = HVDevice(config, i, hot_start)

        pass
    return keithleys
