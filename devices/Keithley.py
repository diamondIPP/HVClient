__author__ = 'micha'

import inspect
import os
import sys
from collections import deque
import serial
from .device import *


currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


class Keithley(Device):
    def __init__(self, device_no, config, hot_start=False):

        Device.__init__(self, device_no, config, hot_start)

        # Serial
        self.bOpen = False
        self.bOpenInformed = False
        self.SerialPortName = self.Config.get_value('address')
        self.baudrate = self.Config.get_value('baudrate', int)
        self.serial = None
        self.commandEndCharacter = chr(13) + chr(10)

        self.writeSleepTime = 0.1
        self.readSleepTime = 0.2
        self.measurements = deque()
        self.last_voltage = 0
        self.identifier = None
        self.Model = None
        self.MaxVoltage = None
        self.manual = False
        self.open_serial_port()

    def connect(self):
        self.open_serial_port()

    def open_serial_port(self):
        try:
            self.serial = serial.Serial(port=self.SerialPortName, baudrate=57600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1, )
            self.bOpen = True
            info('Open serial port: {}'.format(self.SerialPortName))
        except serial.SerialException:
            warning('Could not open serial port: {}'.format(self.SerialPortName))
            self.bOpen = False

    def port_is_open(self):
        if not self.bOpen:
            return False
        return self.serial.isOpen()

    def is_tripped(self, statusword):
        bit = 0x08
        if int(statusword) & bit == bit:
            warning('keithley is tripped')
            self.clear_error_queue()
            self.clear_buffer()
            sleep(1)
            return True
        return False

    # ============================
    # DEVICE FUNCTIONS
    def set_output(self, status, channel=0):
        out = 'ON' if status else 'OFF'
        info('Set output to {}'.format(out))
        data = ':OUTP {}'.format(out)
        return self.write(data)

    def reset(self):
        return self.write('*RST')

    def clear_error_queue(self):
        return self.write('*CLS')

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

    # ============================
    # SET-FUNCTIONS
    def set_bias(self, voltage, channel=0):
        warning('set_bias not implemented')

    def set_immediate_voltage(self, voltage):
        voltage = self.validate_voltage(voltage)
        data = ('SOUR:VOLT:LEV:IMM:AMPL ' if self.Model == '6517B' else 'SOUR:VOLT:IMM:AMPL ')
        data += voltage
        return self.write(data)

    def set_max_voltage(self):
        if self.Model == '6517B':
            self.MaxVoltage = 1000
        else:
            self.MaxVoltage = 0
            raise ValueError('could not find the model name --> setting max voltage to zero')

    # set the format s.t. it returns the measurement of the given value and the voltage of the output
    def set_standard_output_format(self, data):
        return self.write(data)

    def set_measurement_speed(self, value):
        if not 0.01 <= value <= 10:
            raise Exception('Current NPLC not valid: %s' % value)
        return self.write(':SENS:CURR:NPLC %s' % value)

    def set_to_manual(self, status):
        self.write(':SYST:{}'.format('LOCAL' if status else 'REM'))

    def set_filter_type(self, filter_type):
        pass

    def set_average_filter(self, status):
        pass

    def set_average_filter_count(self, count):
        pass

    # ============================
    # GET-FUNCTIONS
    def get_model_name(self):
        self.Model = 9999
        if self.identifier == '':
            self.identify()
        else:
            ident_list = self.identifier.split()
            if len(ident_list) > 5:
                if ident_list[3].lower().startswith('model'):
                    mod = ident_list[4]
                    self.Model = int(mod) if isint(mod) else mod
            info(colored('Connected to Keithley Model {}'.format(self.Model), 'green'))
        self.set_max_voltage()

    def get_output_status(self, channel=0):
        answer = self.get_answer_for_query(':OUTP?')
        while len(answer) > 1 and not isint(answer):
            answer = self.get_answer_for_query(':OUTP?')
        if len(answer) > 0 and not answer == '':
            if answer.isdigit():
                return int(answer)
        else:
            return -1

    def get_output(self):
        return self.get_output_status()

    def get_serial_port(self):  # OK, but extend to compare with self.serial.port
        if self.serial.port == self.SerialPortName:
            return self.SerialPortName
        else:
            raise Exception('serial ports do not match!')

    def get_trigger_count(self):
        data = self.get_answer_for_query(':TRIG:COUN?')
        if data == '':
            return -1
        return data if 0 <= int(data) <= 2500 else -1

    # ============================
    # ACCESS FUNCTIONS
    def get_answer_for_query(self, data, minlength=1):
        self.write(data)
        sleep(self.readSleepTime)
        data = self.read(minlength)
        return clear_string(data)

    def write(self, data):
        data += self.commandEndCharacter
        if self.bOpen:
            output = self.serial.write(str.encode(data))
        else:
            output = True
        sleep(self.writeSleepTime)
        return output == len(data)

    def read(self, min_lenght=0):
        out = ''
        if not self.bOpen:
            if not self.bOpenInformed:
                print('cannot read since Not serial port is not open')
                self.bOpenInformed = False
            return ''
        ts = time()
        max_time = 300
        k = 0
        while True:
            while self.serial.inWaiting() > 0 and time() - ts < max_time and not out.endswith(self.commandEndCharacter):
                out += self.serial.read(1).decode()
                k += 1
            if out.endswith(self.commandEndCharacter):
                break
            if time() - ts > max_time:
                break
            if 0 < min_lenght <= len(out):
                break
            sleep(self.readSleepTime)
        if time() - ts > max_time:
            print(("Tried reading for %s seconds." % (time() - ts), out))
            try:
                print((ord(out[-2]), ord(out[-1]), ord(self.commandEndCharacter[0]), ord(self.commandEndCharacter[1])))
            except IndexError:
                print("Error trying: 'print ord(out[-2]),ord(out[-1]),"
                      "ord(self.commandEndCharacter[0]),ord(self.commandEndCharacter[1]),len(out)'")
            return ''
        # print 'received after %s tries: %s' % (k, out)
        return out

    # ============================
    # READ FUNCTIONS
    def read_current(self):
        if len(self.measurements) == 0:
            return 0
        return self.measurements[-1][2]
        pass

    def read_voltage(self):
        if len(self.measurements) == 0:
            return 0
        return self.measurements[-1][1]
        pass

    def read_iv(self):
        answer = self.get_answer_for_query(':READ?', 20)
        try:
            answer = answer.split()
            voltage = float(answer[0])
            current = float(answer[1])
            if self.Model == '6517B':
                [voltage, current] = [current, voltage]

            rest = answer[2:] if len(answer) > 2 else None
            measurement = [float(x) for x in answer]
            self.measurements.append(measurement)
            return [{'current': current, 'voltage': voltage, 'rest': rest}]
        except Exception as err:
            print(err)
            raise Exception('Could not perform valid IV Measurement, received "%s"' % answer)

    # ============================
    # HELPER FUNCTIONS

    def convert_data(self, timestamp, data):
        try:
            if type(data) == str:
                new_data = data.split(' ')
            elif type(data) == list:
                new_data = data
            else:
                raise Exception('convertData: unvalid type!')
            if len(new_data) % 5 != 0:
                print('Something is wrong with the string, length=%s  \'%s\'' % (len(new_data), data))
                return -1
            # if len(new_data) > 5:
            #     retVal = self.convert_data(timestamp, new_data[:5])
            #     retVal = self.convert_data(timestamp, new_data[5:])
            measurement = [float(x) for x in new_data]
            measurement.insert(0, timestamp)
            self.measurements.append(measurement)
            # self.last_voltage = measurement[0]
            tripped = self.is_tripped(measurement[5])
            print('%d: Measured at %8.2f V: %8.2e A, %s   ==>Length of Queue: %s' % (
                measurement[0], measurement[1], measurement[2], tripped, len(self.measurements)))  # , self.nTrigs)
            if tripped:
                return False
            else:
                return True
        except Exception:
            raise


if __name__ == '__main__':
    keithley = Keithley(load_config('config/keithley.cfg'), 1)
