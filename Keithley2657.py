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
    
    def init_keithley(self,hot_start=False):
        self.reset()
        self.set_autozero_auto()
        self.set_voltage_source_function()
        self.set_voltage_measure_autorange(True)
        self.set_bias(1000)
        self.set_current_measure_range(20e-3)
        self.set_source_limit(10e-3)
        self.set_ON()


    def get_identifier(self):
        return self.inst.query('*IDN?')
    
    def set_autozero_off(self):
        self.inst.write('smua.measure.autozero = smua.AUTOZERO_OFF')
        
    def set_autozero_once(self):
        self.inst.write('smua.measure.autozero = smua.AUTOZERO_ONCE')
        
    def set_autozero_auto(self):
        self.inst.write('smua.measure.autozero = smua.AUTOZERO_AUTO')
        
    # Enable current measure autorange.
    def set_current_measure_autorange(self,value):
        if value:
            self.inst.write('smua.measure.autorangei = smua.AUTORANGE_ON')
        else:
            self.inst.write('smua.measure.autorangei = smua.AUTORANGE_OFF')
            
    def get_current_measure_autorange(self):
        return self.inst.query('print(smua.measure.autorangei)')
    
    # Enable voltage measure autorange.
    def set_voltage_measure_autorange(self,value):
        if value:
            self.inst.write('smua.measure.autorangev = smua.AUTORANGE_ON')
        else:
            self.inst.write('smua.measure.autorangev = smua.AUTORANGE_OFF')
    
    def get_voltage_measure_autorange(self):
        return self.inst.query('print(smua.measure.autorangev)')
    
    def reset(self):
        return self.inst.write('smua.reset()')
    
    def set_voltage_source_function(self):
        return self.inst.write('smua.source.func = smua.OUTPUT_DCVOLTS')
    
    def set_bias(self,voltage):
        retVal = self.inst.write('smua.source.levelv = %f'%voltage)
        self.set_voltage = voltage
        return self.get_bias()
    
    def set_source_limit(self,limit):
        retVal = self.inst.write('smua.source.limiti = %3.3E'%limit)
        return self.get_source_limit()
        
    def get_source_limit(self):
        return self.inst.query('smua.source.limiti')
    
    def set_measure_range_current(self,range):
        retVal = self.inst.write('smua.measure.rangei = %5.2E'%range)
        return self.get_measure_range_current()
    
    def get_measure_range_current(self):
        return self.inst.query('smua.measure.rangei')

    def get_bias(self):
        return self.inst.query('print(smua.source.levelv)')    
    
    def read_current(self):
        return self.query('smua.measure.i()')
    
    def read_voltage(self):
        return self.query('smua.measure.v()')
    
    def read_iv(self):
        retVal = self.query('smua.measure.iv()')
        return retVal
    
    def set_output(self,status):
        self.write('smua.source.output = %d'%status)
        return self.get_output(self)
    
    def get_output(self):
        return self.query('print(smua.source.output)')

if __name__ == '__main__':
    conf = ConfigParser.ConfigParser()
    conf.read('keithley.cfg')
    k2657 = Keithley2657(conf, 4, False)
