__author__ = 'micha'

# ============================
# IMPORTS
# ============================
from HV_interface import HVInterface
import serial
from time import sleep, time
import ConfigParser
from collections import deque
from string import maketrans
import math


# ============================
# CONSTANTS
# ============================
ON = 1
OFF = 0


# ============================
# MAIN CLASS
# ============================
class Keithley6517B(HVInterface):
    def __init__(self, config, device_no=1, hot_start=False):
        HVInterface.__init__(self, config, device_no)
        self.bOpen = False
        self.bOpenInformed = False
        self.serialPortName = config.get(self.section_name, 'address')
        self.writeSleepTime = 0.1
        self.readSleepTime = 0.2
        self.baudrate = config.getint(self.section_name, 'baudrate')
        self.commandEndCharacter = chr(13) + chr(10)
        self.measurments = deque()
        self.lastVoltage = 0
        self.serial = None
        self.open_serial_port(hot_start)
        self.model = None
        self.identifier = None
        self.max_voltage = None

    def open_serial_port(self, hot_start=False):
        try:
            self.serial = serial.Serial(
                port=self.serialPortName,
                baudrate=57600,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1,
            )
            self.bOpen = True
            print 'Open serial port: \'%s\'' % self.serialPortName
        except serial.SerialException:
            print 'Could not open serial Port: \'%s\'' % self.serialPortName
            self.bOpen = False
            pass

        self.init_keithley(hot_start=hot_start)

    def init_keithley(self, hot_start=False):
        # protection = 500e-6,
        if hot_start:
            sleep(1)
            self.clear_buffer()
            self.identify()
            # self.clearErrorQueue()
            sleep(1)
        else:
            sleep(1)
            self.set_output(False)
            self.reset()
            self.clear_buffer()
            self.identify()
            self.set_zero_check(False)
            self.config_readout()
            self.set_standard_output_format()

    #         self.setStandardOutputForm()
    #         self.setConcurrentMeasurments(True)
    #         self.setDigitalFilterType('REP')
    #         self.setAverageFiltering(True)
    #         self.setAverageFilterCount(3)
    #         self.setCurrentProtection(100e-6)
    #         self.setCurrentMeasurmentSpeed(5)  # was 10 before
    #         # self.setImmidiateVoltage(self.immidiateVoltage)
    #         self.clearErrorQueue()
    #         self.setComplianceAbortLevel('LATE')
    #         # self.setComplianceAbortLevel('NEVER')
    #         sleep(1)

    # ============================
    # DEVICE FUNCTIONS
    def set_output(self, status):
        print_value = 'set Output to '
        data = ':OUTP '
        data += ('ON' if status else 'OFF')
        print_value += ('ON' if status else 'OFF')
        print print_value
        return self.write(data)

    def reset(self):  # ok
        return self.write('*RST')

    def clear_buffer(self):
        if self.bOpen:
            while self.serial.inWaiting():
                self.read()
                sleep(self.readSleepTime)
        else:
            pass
        return self.write(':TRAC:CLEAR')

    def identify(self):
        self.identifier = self.get_answer_for_query('*IDN?')
        self.get_model_name()

    def get_model_name(self):
        if self.identifier == '':
            self.identify()
        else:
            ident_list = self.identifier.split()
            self.model = 9999
            if len(ident_list) > 5:
                if ident_list[3].lower().startswith('model'):
                    self.model = ident_list[4]
            print 'Connected Keithley Model %s' % self.model

    def set_max_voltage(self):
        self.max_voltage = float(1000) if self.model == '6517B' else float(0)

    def set_zero_check(self, status):
        data = ':SYST:ZCH ON' if status else ':SYST:ZCH OFF'
        return self.write(data)

    def set_range_voltage(self, status):
        data = ':SOUR:RANG 1000' if status == 'high' else ':SOUR:RANG 1000'
        return self.write(data)

    # there can only be one value be maesured at a time
    def config_readout(self, readout='current'):
        data = ':CONF:VOLT:DC' if readout.lower() == 'voltage' else ':CONF:CURR:DC'
        return self.write(data)

    # set the format s.t. is return the measurement of the given value and the voltage of the output
    def set_standard_output_format(self):
        return self.write(':FORM:ELEM READ,VSO')

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
    def set_bias(self, voltage):
        self.set_voltage(voltage)

    def set_voltage(self, value):
        if self.max_voltage < math.fabs(value) and self.is_float(value):
            value = math.copysign(self.max_voltage, value)
            print 'set voltage to maximum allowed voltage: %s' % value
        else:
            print 'invalid Voltage: %s' % value
            return -1
        return self.write(':SOUR:VOLT:LEV:IMM:AMPL %s' % value)

    # ============================
    # ACCESS FUNCTIONS
    def read_iv(self):
        answer = self.get_answer_for_query(':READ?', 20)
        try:
            answer = answer.split()
            voltage = float(answer[0])
            current = float(answer[1])
            measurment = [float(x) for x in answer]
            self.measurments.append(measurment)
            return voltage, current
        except:
            raise Exception('Could not perform valid IV Measurement, received "%s"' % answer)

    def get_answer_for_query(self, data, minlength=1):
        self.write(data)
        sleep(self.readSleepTime)
        data = self.read(minlength)
        return self.clear_string(data)

    def write(self, data):
        data += self.commandEndCharacter
        if self.bOpen:
            output = self.serial.write(data)
        else:
            output = True
        sleep(self.writeSleepTime)
        return output == len(data)

    def read(self, min_lenght=0):
        out = ''
        if not self.bOpen:
            if not self.bOpenInformed:
                print 'cannot read since Not serial port is not open'
                self.bOpenInformed = False
            return ''
        ts = time()
        max_time = 300
        k = 0
        while True:
            while self.serial.inWaiting() > 0 and time() - ts < max_time and not out.endswith(self.commandEndCharacter):
                out += self.serial.read(1)
                k += 1
            if out.endswith(self.commandEndCharacter):
                break
            if time() - ts > max_time:
                break
            if 0 < min_lenght <= len(out):
                break
            sleep(self.readSleepTime)
        if time() - ts > max_time:
            print "Tried reading for %s seconds." % (time() - ts), out
            try:
                print ord(out[-2]), ord(out[-1]), ord(self.commandEndCharacter[0]), ord(self.commandEndCharacter[1])
            except IndexError:
                print "Error trying: 'print ord(out[-2]),ord(out[-1])," \
                      "ord(self.commandEndCharacter[0]),ord(self.commandEndCharacter[1]),len(out)'"
            return ''
        # print 'received after %s tries: %s' % (k, out)
        return out

    # ============================
    # HELPER FUNCTIONS
    @staticmethod
    def clear_string(data):
        data = data.translate(None, '\r\n\x00\x13\x11\x10')
        data = data.translate(maketrans(',', ' '))
        return data.strip()

    def valid_voltage(self, value):
        return True if self.is_float(value) and abs(value) <= self.max_voltage else False


if __name__ == '__main__':
    conf = ConfigParser.ConfigParser()
    conf.read('keithley.cfg')
    keithley = Keithley6517B(conf, 2, False)
