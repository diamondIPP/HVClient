__author__ = 'bachmair'
# implementation of Keithley 237
# based on HV_interface class

# ============================
# IMPORTS
# ============================
import ConfigParser
import visa
from HV_interface import HVInterface
from time import sleep,time

# ============================
# CONSTANTS
# ============================
ON = 1
OFF = 0


# ============================
# MAIN CLASS
# ============================
class Keithley2657(HVInterface):
    def __init__(self, config, device_no=1, hot_start=False):
        HVInterface.__init__(self, config, device_no, hot_start)
        self.bOpen = False
        self.ip_address = config.get(self.section_name, 'ip_address')
        self.rm = visa.ResourceManager('@py')
        self.inst = None
        self.identifier = None
        self.answer_time = 0.1
        self.open_tcp_connection()
        self.init_keithley(hot_start)


    def open_tcp_connection(self):
        resource_name = "TCPIP::%s::INSTR"%self.ip_address
        self.inst = self.rm.open_resource(resource_name)

    def self_identifier(self):
        return self.inst.query('*IDN?')


if __name__ == '__main__':
    conf = ConfigParser.ConfigParser()
    conf.read('keithley.cfg')
    k2657 = Keithley2657(conf, 4, False)
