import keithleyDevice
import ConfigParser


def get_keithleys(config, hotStart):
    keithleys = {}
    try:
        for sec in config.sections():
            print sec,config.options(sec)
        nKeithleys = config.getint('Main','nkeithleys')
    except:
        print 'cannot find option'
        nKeithleys = 0
    print 'Found %d Keithleys'%nKeithleys
    for i in range(1,nKeithleys+1):
        name = 'Keithley%d'%i
        if config.has_section(name):
            keithleys[name] = keithleyDevice.keithleyDevice(name,
                                                            config, 
                                                            hotStart)

        pass
    return keithleys
