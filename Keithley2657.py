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
        self.max_voltage = 3000
        #self.init_keithley(hot_start)


    def open_tcp_connection(self):
        resource_name = "TCPIP::%s::INSTR"%self.ip_address
        self.inst = self.rm.open_resource(resource_name)
    
    def init_keithley(self,hot_start=False):
        self.reset()
        self.clear_status()
        self.clear_errorqueue()
        self.clear_eventlog()
        self.clear_dataqueue()
        self.identify()
        self.set_measure_filter_count(5)
        self.set_measure_filter_enable(1)
        self.set_measure_filter_type_repeating_average()
        self.set_autozero_auto()
        self.set_voltage_source_function()
        self.set_voltage_measure_autorange(True)
        self.set_bias(-600)
        self.set_measure_range_current(10e-6)
        self.set_current_protection(10e-6)
        self.set_measure_filter_count(10)
        self.set_measure_filter_enable(True)
        self.set_measure_filter_type_repeating_average()
        self.set_measure_speed_normal()
        self.set_display_current()
        self.set_on()

    def __query(self,query):
        return self.inst.query(query).strip('\n')

    def __write(self,value):
        print 'write',value
        retVal =  self.inst.write(value)
        sleep(1)
        return retVal

    def __set_value(self,variable,value):
        self.__write('%s = %s'%(variable,value))

    def __read(self):
        return self.inst.read()

    def __print_string(self,value):
        return 'print(%s)'%value

    def __print(self,value):
        return str(self.__query(self.__print_string(value)))

    def print_float(self,value):
        return self.query_float(self.__print_string(value))

    def print_int(self,value):
        return self.query_int(self.__print_string(value))

    def print_bool(self,value):
        return self.query_bool(self.__print_string(value))

    def print2(self,value):
        return self.__print(value)
    
    def query(self,value):
        return self.__query(value)

    def query_float(self,query):
        return float(self.__query(query))
    
    def query_int(self,query):
        return int(float((self.__query(query))))

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

    def identify(self):
        self.identifier = self.get_identifier()
        self.get_model_name()

    def get_model_name(self):
        retVal = self.__print('localnode.model')
        self.model = int(retVal) if self.is_number(retVal) else retVal
        print 'Connected Keithley Model', self.model
        return self.model

    def get_linefreq(self):
        return self.print_float('localnode.linefreq ')

    def set_linefreq(self, value):
        if not value == 50 or not value == 60:
            raise Exception('Linefrequency must be 50 or 60 Hz while trying to set it to %f Hz'%value)
        self.__write('localnoed.linefreq = %d'%value)
        return self.get_linefreq()



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

    def clear_status(self):
        self.__write('*CLS')

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

    def set_current_protection(self,limit):
        return self.set_source_limit(limit)
        
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
        return self.print_float('smua.measure.i()')
    
    def read_voltage(self):
        return self.print_float('smua.measure.v()')
    
    def read_iv(self):
        retVal = self.__print('smua.measure.iv()')
        retVal = retVal.split('\t')
        return {'current': float(retVal[0]), 'voltage': float(retVal[1])}
    
    def set_output(self,status):
        self.__write('smua.source.output = %d'%status)
        return self.get_output()
    
    def get_output(self):
        retVal =  self.print_bool('smua.source.output')
        return retVal == 0.

    def get_erorqueue_count(self):
        return self.print_int('errorqueue.count')

    def clear_errorqueue(self):
        self.__write('errorqueue.clear()')

    def get_eventlog_count(self):
        return self.print_int('eventlog.count')

    def clear_eventlog(self):
        self.__write('eventlog.clear()')

    def get_dataqueue_count(self):
        self.print_int('dataqueue.count')

    def clear_dataqueue(self):
        self.__write('dataqueue.clear()')

    def get_measure_filter_count(self):
        return self.print_int('smua.measure.filter.count')

    def set_measure_filter_count(self,value):
        self.__set_value('smua.measure.filter.count',value)
        return self.get_measure_filter_count()

    def get_measure_filter_enable(self):
        self.print_bool('smua.measure.filter.enable')

    def set_measure_filter_enable(self,value):
        self.__set_value('smua.measure.filter.enable',value)
        return self.get_measure_filter_enable()

    def get_measure_filter_type(self):
        retVal = self.print_int('smua.measure.filter.type')
        if retVal == 0:
            return 'moving_avg'
        elif retVal == 1:
            return 'repeat_avg'
        elif retVal == 2:
            return 'median'
        else:
            raise Exception('Invaid return for measure filte type: %s'%retVal)

    def set_measure_filter_type_median(self):
        self.__set_value('smua.measure.filter.type','smua.FILTER_MEDIAN')
        return self.get_measure_filter_type()

    def set_measure_filter_type_moving_average(self):
        self.__set_value('smua.measure.filter.type','smua.FILTER_MOVING_AVG')
        return self.get_measure_filter_type()

    def set_measure_filter_type_repeating_average(self):
        self.__set_value('smua.measure.filter.type','smua.FILTER_REPEAT_AVG')
        return self.get_measure_filter_type()

    def get_measure_integration_aperture(self):
        self.print_int('smua.measure.nplc')

    def set_measure_integration_aperture(self,value):
        self.__set_value('smua.measure.nplc',value)
        return self.get_measure_integration_aperture()

    def get_measure_converter(self):
        retVal = self.print_int('smua.measure.adc')
        if retVal == 0:
            return 'adc_integrate'
        elif retVal == 1:
            return 'adc_fast'
        else:
            raise Exception('Cannot extract adc converter from %s'%retVal)

    def set_measure_converter_integration(self):
        self.__set_value('smua.measure.adc','smua.ADC_INTEGRATE')
        return

    def set_measure_converter_fast(self):
        self.__set_value('smua.measure.adc','smua.ADC_FAST')
        return

    def set_measure_speed_fast(self):
        self.set_measure_converter_fast()
        pass

    def set_measure_speed_medium(self):
        self.set_measure_converter_integration()
        self.set_measure_integration_aperture(.1)
        pass

    def set_measure_speed_normal(self):
        self.set_measure_converter_integration()
        self.set_measure_integration_aperture(1)
        pass

    def set_measure_speed_hi_accuracy(self):
        self.set_measure_converter_integration()
        self.set_measure_integration_aperture(10)
        pass

    def set_display_current(self):
        self.__set_value('display.smua.measure.func','display.MEASURE_DCAMPS')
if __name__ == '__main__':
    conf = ConfigParser.ConfigParser()
    conf.read('keithley.cfg')
    k2657 = Keithley2657(conf, 4, False)
