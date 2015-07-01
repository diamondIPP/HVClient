__author__ = 'micha'

# ============================
# IMPORTS
# ============================
from KeithleyHead import KeithleyHead
from time import sleep
import ConfigParser


# ============================
# CONSTANTS
# ============================
ON = 1
OFF = 0


# ============================
# MAIN CLASS
# ============================
class Keithley6517B(KeithleyHead):
    def __init__(self, config, device_no=1, hot_start=False):
        KeithleyHead.__init__(self, config, device_no)
        self.measure_value = 'CURR'
        self.init_keithley(hot_start)

    def init_keithley(self, hot_start=False):
        if hot_start:
            sleep(0.2)
            self.clear_buffer()
            self.identify()
            self.clear_error_queue()
            sleep(0.2)
        else:
            sleep(0.2)
            self.set_output(False)
            self.reset()
            self.clear_buffer()
            self.identify()
            self.set_max_voltage()
            self.set_zero_check(False)
            self.set_standard_output_format(':FORM:ELEM VSO,READ')
            self.set_filter_type('ADV')
            self.set_average_filter(True)
            self.set_filter_count(3)
            self.set_measurement_speed(5)
            self.clear_error_queue()
            sleep(0.2)
            self.config_readout()
            sleep(0.2)

    # ============================
    # DEVICE FUNCTIONS
    def set_zero_check(self, status):
        data = ':SYST:ZCH ON' if status else ':SYST:ZCH OFF'
        return self.write(data)

    # there can only be one value be maesured at a time
    def config_readout(self, readout='current'):
        self.measure_value = 'VOLT' if readout.lower() == 'voltage' else 'CURR'
        data = ':CONF:VOLT:DC' if readout.lower() == 'voltage' else ':CONF:CURR:DC'
        return self.write(data)

    def set_filter_type(self, filter_type):
        if filter_type not in ['SCAL', 'ADV']:
            raise Exception('invalid filterType: %s' % filter_type)
        data = ':SENS:' + self.measure_value + ':DC:AVER:TYPE ' + filter_type
        return self.write(data)

    def set_average_filter(self, status=True):
        data = ':SENS:' + self.measure_value + ':DC:AVER:STAT '
        data += ('ON' if status else 'OFF')
        return self.write(data)

    def set_filter_count(self, count):
        if not 1 <= count <= 100:
            raise ValueError('Average Filter Count not in valid range: %s' % count)
        data = ':SENS:' + self.measure_value + ':DC:AVER:COUN ' + str(count)
        return self.write(data)

    def enable_display(self, status, window=1):
        data = ':DISP:WIND%d:TEXT:STAT ' % window
        data += (str(ON) if status else str(OFF))
        return self.write(data)

    def display(self, msg, window=1):
        self.enable_display(1, window)
        data = ':DISP:WIND%d:TEXT:DATA ' % window
        data += '\'' + msg + '\''
        return self.write(data)

    # ============================
    # SET-FUNCTIONS
    def set_voltage(self, voltage):
        voltage = self.validate_voltage(voltage)
        self.set_range_voltage('low') if voltage <= 100 else self.set_range_voltage('high')
        data = ':SOUR:VOLT ' + str(voltage)
        return self.write(data)

    def set_range_voltage(self, status):
        data = ':SOUR:VOLT:RANG 1000' if status == 'high' else ':SOUR:VOLT:RANG 100'
        return self.write(data)

    # ============================
    # GET-FUNCTIONS
    def get_voltage_range(self):
        return int(self.get_answer_for_query(':SOUR:VOLT:RANG?'))

    def get_filter_type(self):
        data = ':SENS:' + self.measure_value + ':DC:AVER:TYPE?'
        return self.get_answer_for_query(data)

    def get_filter_count(self):
        data = ':SENS:' + self.measure_value + ':DC:AVER:COUN?'
        return self.get_answer_for_query(data)


if __name__ == '__main__':
    conf = ConfigParser.ConfigParser()
    conf.read('../config/keithley.cfg')
    keithley = Keithley6517B(conf, 2, False)
