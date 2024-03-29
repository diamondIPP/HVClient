__author__ = 'bachmair'

# implementation of Keithley 237
# based on HV_interface class
import configparser
import inspect
import os
import socket
import sys
import pyvisa as visa

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from .Keithley import *
from time import sleep


class Keithley2657(Keithley):
    def __init__(self, device_no, config, hot_start=False, print_logs=False):
        Keithley.__init__(self, device_no, config, hot_start)
        self.bOpen = False
        self.ip_address = self.Config.get_value('ip_address')
        self.rm = visa.ResourceManager('@py')
        self.inst = None
        self.identifier = None
        self.answer_time = 0.1
        self.open_tcp_connection()
        self.max_voltage = 3000
        self.read_config()
        self.init_keithley(hot_start)

    def read_config(self):
        self.compliance = self.Config.get_value('compliance', float, default=1e-6)
        self.measure_range_current = self.Config.get_value('measure_range', float, default=1e-6)

    def check_port(self, port_no):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((self.ip_address, port_no))
        sock.send('CLOSE')
        if result == 0:
            retVal = True
        else:
            retVal = False
        sock.shutdown(1)
        sock.close()
        return retVal

    def close_all_open_connections(self):
        port = 5030
        print('closing all open connections by opening/closing port %d' % port)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.ip_address, port))
        s.send('CLOSE')
        # while(s.read(sock, ...)=0) 
        s.shutdown(1)
        s.close()
        print('CLOSED')

        # import socket

    def open_tcp_connection(self):
        self.close_all_open_connections()
        print('Open TCP connection', self.check_port(1024))
        resource_name = "TCPIP::%s::INSTR" % self.ip_address
        self.inst = self.rm.open_resource(resource_name)
        print('DONE')
        self.clear_readout()

    def clear_readout(self):
        print('clear_readout')
        timeout = self.inst.timeout
        self.inst.timeout = 100
        while True:
            try:
                retVal = self.inst.read()
                print('Reading: ', retVal)
            except:
                print('No more data in cache')
                break
        self.inst.timeout = timeout

    def init_keithley(self, hot_start=False):
        ntries = 0
        while ntries < 10:
            try:
                self.clear_readout()
                self.clear_errorqueue()
                if not hot_start:
                    self.reset()
                    self.set_output(False)
                self.clear_status()
                self.clear_eventlog()
                self.clear_dataqueue()
                self.identify()
                self.set_autozero_auto()
                self.set_voltage_source_function()
                self.set_voltage_measure_autorange(True)
                self.set_measure_range_current(self.measure_range_current)
                self.set_current_protection(self.compliance)
                self.set_measure_filter_count(5)
                self.set_measure_filter_enable(True)
                self.set_measure_filter_type_repeating_average()
                # self.set_measure_speed_normal()
                self.set_measure_speed_hi_accuracy()
                self.set_display_current()
                break
            except Exception as e:
                print('EXCEPTION: ', e)
                self.clear_readout()
            ntries += 1

    def __check_for_errors(self, query):
        return
        words = ['errorqueue', '*CLS', 'clear']
        if any([x in query for x in words]):
            return
        error_count, error_code, msg = self.get_next_error_message()
        while error_count > 0:
            print(self.name, 'Error Message', error_count, error_code, msg)
            sys.stdout.flush()
            raise Exception('Error No %d - %s - %d errors left' % (error_code, msg, error_count))
            error_count, error_code, msg = self.get_next_error_message()

    def __query(self, query):
        retVal = self.inst.query(query).strip('\n')
        self.__check_for_errors(query)
        return retVal

    def __write(self, value):
        retVal = self.inst.write(value)
        self.__check_for_errors(value)
        # sleep(.1)
        return retVal

    def __set_value(self, variable, value):
        if type(value) == bool:
            value = int(value)
        self.__write('%s = %s' % (variable, value))

    def __read(self):
        return self.inst.read()

    def __print_string(self, value):
        return 'print(%s)' % value

    def __print(self, value):
        return str(self.__query(self.__print_string(value)))

    def print_float(self, value):
        return self.query_float(self.__print_string(value))

    def print_int(self, value):
        return self.query_int(self.__print_string(value))

    def print_bool(self, value):
        return self.query_bool(self.__print_string(value))

    def print2(self, value):
        return self.__print(value)

    def query(self, value):
        return self.__query(value)

    def query_float(self, query):
        return float(self.__query(query))

    def query_int(self, query):
        return int(float((self.__query(query))))

    def query_bool(self, query):
        retVal = self.__query(query)
        try:
            return bool(float(retVal))
        except ValueError as e:
            if retVal == 'false':
                return False
            elif retVal == 'true':
                return True
            else:
                raise ValueError(e)

    def write(self, value):
        return self.__write(value)

    def get_next_error_message(self):
        error_count = int(float(self.__print('errorqueue.count')))
        retVal = self.__query('errorcode, message = errorqueue.next() \n print(errorcode, message)')
        retVal = retVal.split('\t')
        try:
            error_code = int(float(retVal[0]))
            error_msg = retVal[1]
        except:
            print('Could not convert \'%s\'' % retVal)
            error_code = -1
            error_msg = retVal
        return error_count, error_code, error_msg

    def identify(self):
        self.identifier = self.get_identifier()
        self.get_model_name()

    def get_model_name(self):
        value = self.__print('localnode.model')
        self.model = int(value) if value.isdigit() else value
        print('Connected Keithley Model', self.model)
        return self.model

    def get_linefreq(self):
        return self.print_float('localnode.linefreq ')

    def set_linefreq(self, value):
        if not value == 50 or not value == 60:
            raise Exception('Linefrequency must be 50 or 60 Hz while trying to set it to %f Hz' % value)
        self.__write('localnoed.linefreq = %d' % value)
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
    def set_current_measure_autorange(self, value):
        if value:
            self.__write('smua.measure.autorangei = smua.AUTORANGE_ON')
        else:
            self.__write('smua.measure.autorangei = smua.AUTORANGE_OFF')

    def get_current_measure_autorange(self):
        return self.inst.query('print(smua.measure.autorangei)')

    # Enable voltage measure autorange.
    def set_voltage_measure_autorange(self, value):
        if value:
            self.__write('smua.measure.autorangev = smua.AUTORANGE_ON')
        else:
            self.__write('smua.measure.autorangev = smua.AUTORANGE_OFF')

    def get_voltage_measure_autorange(self):
        return self.print_float('smua.measure.autorangev')

    def clear_status(self):
        self.__write('*CLS')

    def reset(self):
        print('reset')
        return self.__write('smua.reset()')

    def set_voltage_source_function(self):
        return self.__write('smua.source.func = smua.OUTPUT_DCVOLTS')

    def set_bias(self, voltage, channel=None):
        # print 'set_bias: ',voltage,type(voltage)
        retVal = self.__write('smua.source.levelv = %f' % voltage)
        self.target_voltage = voltage
        sleep(.5)
        return self.get_bias()

    def is_in_compliance(self):
        return self.print_bool('smua.source.compliance')

    # def set_compliance_control(self,value=True):
    #    if value:
    #        self.__set_value('smua.source.compliance','true')
    #    else:
    #        self.__set_value('smua.source.compliance','false')
    #    return self.get_compliance_control()

    def set_source_limit(self, limit):
        retVal = self.__write('smua.source.limiti = %3.3E' % limit)
        # self.set_compliance_control(True)
        return self.get_source_limit()

    def set_current_protection(self, limit):
        return self.set_source_limit(limit)

    def get_source_limit(self):
        return self.print_float('smua.source.limiti')

    def set_measure_range_current(self, range):
        retVal = self.__write('smua.measure.rangei = %5.2E' % range)
        return self.get_measure_range_current()

    def get_measure_range_current(self):
        return self.print_float('smua.measure.rangei')

    def get_bias(self, channel=None):
        return self.print_float('smua.source.levelv')

    def read_current(self):
        return self.print_float('smua.measure.i()')

    def read_voltage(self):
        return self.print_float('smua.measure.v()')

    def read_iv(self):
        retVal = self.__print('smua.measure.iv()')
        compl = self.is_in_compliance()
        retVal = retVal.split('\t')
        voltage = float(retVal[1])
        current = float(retVal[0])
        if compl:
            current = self.read_current()
            voltage = self.read_voltage()
            print(ValueError('In Complicance'))
        if abs(voltage) > 1e10 or abs(current) > 1e10:
            current = self.read_current()
            voltage = self.read_voltage()
            msg = '\x1B[s'
            msg += '\033[91m'
            msg += '\x1B[1A\rInvalid measurement of current or voltage: %s V  / %s ' % (voltage, current)
            msg += '\033[99m' + '\033[0m'
            msg += '\x1B[u\x1B[1D'
            print(msg, end=' ')
            sys.stdout.flush()
        return {'current': current, 'voltage': voltage, 'compliance': compl}

    def set_output(self, status, channel=None):
        self.__write('smua.source.output = %d' % status)
        return self.get_output()

    def get_output(self):
        retVal = self.print_bool('smua.source.output')
        return retVal

    def get_output_status(self, channel=None):
        return self.get_output()

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

    def set_measure_filter_count(self, value):
        self.__set_value('smua.measure.filter.count', value)
        return self.get_measure_filter_count()

    def get_measure_filter_enable(self):
        self.print_bool('smua.measure.filter.enable')

    def set_measure_filter_enable(self, value):
        self.__set_value('smua.measure.filter.enable', value)
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
            raise Exception('Invaid return for measure filte type: %s' % retVal)

    def set_measure_filter_type_median(self):
        self.__set_value('smua.measure.filter.type', 'smua.FILTER_MEDIAN')
        return self.get_measure_filter_type()

    def set_measure_filter_type_moving_average(self):
        self.__set_value('smua.measure.filter.type', 'smua.FILTER_MOVING_AVG')
        return self.get_measure_filter_type()

    def set_measure_filter_type_repeating_average(self):
        self.__set_value('smua.measure.filter.type', 'smua.FILTER_REPEAT_AVG')
        return self.get_measure_filter_type()

    def get_measure_integration_aperture(self):
        self.print_int('smua.measure.nplc')

    def set_measure_integration_aperture(self, value):
        self.__set_value('smua.measure.nplc', value)
        return self.get_measure_integration_aperture()

    def get_measure_converter(self):
        retVal = self.print_int('smua.measure.adc')
        if retVal == 0:
            return 'adc_integrate'
        elif retVal == 1:
            return 'adc_fast'
        else:
            raise Exception('Cannot extract adc converter from %s' % retVal)

    def set_measure_converter_integration(self):
        self.__set_value('smua.measure.adc', 'smua.ADC_INTEGRATE')
        return

    def set_measure_converter_fast(self):
        self.__set_value('smua.measure.adc', 'smua.ADC_FAST')
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
        self.__set_value('display.smua.measure.func', 'display.MEASURE_DCAMPS')

    def set_display_digits(self, value=6):
        if not value in [4, 5, 6]:
            raise ValueError('Invalid no of display digits. %d' % value)
        if value == 4:
            self.__set_value('display.smua.digits', 'display.DIGITS_4_5')
        elif value == 5:
            self.__set_value('display.smua.digits', 'display.DIGITS_5_5')
        elif value == 6:
            self.__set_value('display.smua.digits', 'display.DIGITS_6_5')


if __name__ == '__main__':
    conf = configparser.ConfigParser()
    conf.read(parentdir + '/config/keithley.cfg')
    k2657 = Keithley2657(conf, 6, False)
