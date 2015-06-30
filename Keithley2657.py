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
        #self.init_keithley(hot_start)


    def open_tcp_connection(self):
        resource_name = "TCPIP::%s::INSTR"%self.ip_address
        self.inst = self.rm.open_resource(resource_name)
    
    def init_keithley(self,hot_start=False):
        self.reset()
        self.set_autozero_auto()
        self.set_voltage_source_function()
        self.set_voltage_measure_autorange(True)
        self.set_bias(1000)
        self.set_measure_range_current(20e-3)
        self.set_source_limit(10e-3)
        self.set_on()

    def __query(self,query):
        return self.inst.query(query).strip('\n')

    def __write(self,value):
        print 'write',value
        retVal =  self.inst.write(value)
        sleep(1)
        return retVal

    def __read(self):
        return self.inst.read()

    def __print_string(self,value):
        return 'print(%s)'%value

    def __print(self,value):
        return self.__query(self.__print_string(value))

    def print_float(self,value):
        return self.query_float(self.__print_string(value))

    def print_float(self,value):
        return self.query_float(self.__print_string(value))

    def print_bool(self,value):
        return self.query_bool(self.__print_string(value))

    def print2(self,value):
        return self.__print(value)
    
    def query(self,value):
        return self.__query(value)

    def query_float(self,query):
        return float(self.__query(query))
    
    def query_int(self,query):
        return int(float((self.__query(query)))

    def query_bool(self,query):
        return bool(float(self.__query(query)))

    def write(self,value):
        return self.__write(value)

    def get_next_error_message(self):
        error_count = int(float(self.__print('errorqueue.count')))
        retVal = self.__query('errorcode, message = errorqueue.next() \n print(errorcode, message)')
        retVal=retVal.split('\t')
        error_code = int(float(retVal[0]))
        error_msg = retVal[1]
        return error_count,error_code,error_msg

    

    def get_identifier(self):
        return self.__query('*IDN?')
    
    def set_autozero_off(self):
        self.__write('smua.measure.autozero = smua.AUTOZERO_OFF')
        
    def set_autozero_once(self):
        self.__write('smua.measure.autozero = smua.AUTOZERO_ONCE')
        
    def set_autozero_auto(self):
        self.__write('smua.measure.autozero = smua.AUTOZERO_AUTO')
        
    # Enable current measure autorange.
    def set_current_measure_autorange(self,value):
        if value:
            self.__write('smua.measure.autorangei = smua.AUTORANGE_ON')
        else:
            self.__write('smua.measure.autorangei = smua.AUTORANGE_OFF')
            
    def get_current_measure_autorange(self):
        return self.inst.query('print(smua.measure.autorangei)')
    
    # Enable voltage measure autorange.
    def set_voltage_measure_autorange(self,value):
        if value:
            self.__write('smua.measure.autorangev = smua.AUTORANGE_ON')
        else:
            self.__write('smua.measure.autorangev = smua.AUTORANGE_OFF')
    
    def get_voltage_measure_autorange(self):
        return self.print_float('smua.measure.autorangev')
    
    def reset(self):
        print 'reset'
        return self.__write('smua.reset()')
    
    def set_voltage_source_function(self):
        return self.__write('smua.source.func = smua.OUTPUT_DCVOLTS')
    
    def set_bias(self,voltage):
        retVal = self.__write('smua.source.levelv = %f'%voltage)
        self.set_voltage = voltage
        return self.get_bias()
    
    def set_source_limit(self,limit):
        retVal = self.__write('smua.source.limiti = %3.3E'%limit)
        return self.get_source_limit()
        
    def get_source_limit(self):
        return self.print_float('smua.source.limiti')
    
    def set_measure_range_current(self,range):
        retVal = self.__write('smua.measure.rangei = %5.2E'%range)
        return self.get_measure_range_current()
    
    def get_measure_range_current(self):
        return self.print_float('smua.measure.rangei')

    def get_bias(self):
        return self.print_float('smua.source.levelv')
    
    def read_current(self):
        return self.query_float('smua.measure.i()')
    
    def read_voltage(self):
        return self.query_float('smua.measure.v()')
    
    def read_iv(self):
        retVal = self.query('smua.measure.iv()')
        return retVal
    
    def set_output(self,status):
        self.__write('smua.source.output = %d'%status)
        return self.get_output()
    
    def get_output(self):
        retVal =  self.print_bool('smua.source.output')
        return retVal == 0.

if __name__ == '__main__':
    conf = ConfigParser.ConfigParser()
    conf.read('keithley.cfg')
    k2657 = Keithley2657(conf, 4, False)