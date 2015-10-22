# implementation of ISEG NIM Power supplies
# based on HV_interface class

# ============================
# IMPORTS
# ============================
import os,sys,inspect
import ConfigParser
import serial
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
from HV_interface import HVInterface
from time import sleep,time
import math
from HV_interface import HVInterface
import serial
from time import sleep, time
from collections import deque
from string import maketrans

# ============================
# CONSTANTS
# ============================
ON = 1
OFF = 0


# ============================
# MAIN CLASS
# ============================
class ISEG(HVInterface):
    def __init__(self, config, device_no=1, hot_start=False):
        self.Busy = False
        self.commandEndCharacter = '\r\n'
        self.readSleepTime = .1
        self.writeSleepTime = .1
        HVInterface.__init__(self, config, device_no,hot_start)
        self.bOpen = False
        self.read_config(config)
        self.lastVoltage = 0
        self.serial = None
        self.model = self.get_model_name()
        self.identifier = None
        self.answer_time = 0.1
        self.open_serial_port()
        self.init_keithley(hot_start)
        pass

    @staticmethod
    def clear_string(data):
        data = data.translate(None, '\r\n\x00\x13\x11\x10')
        data = data.translate(maketrans(',', ' '))
        return data.strip()

    def open_serial_port(self):
        try:
            self.serial = serial.Serial(
                port=self.serialPortName,
                baudrate=9600,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=.5,
            )
            self.bOpen = True
            print 'Open serial port: \'%s\'' % self.serialPortName
        except:
            print 'Could not open serial Port: \'%s\'' % self.serialPortName
            self.bOpen = False
            pass

    def init_keithley(self, hot_start):
        return
        self.set_source_voltage_dc()
        self.set_1100V_range(True)
        self.set_output_sense_local()
        self.set_integration_time(self.integration_time)
        self.set_averaging_filter(self.n_average_filter)
        self.set_output_data_format()
        self.set_compliance(self.measure_range_current,self.compliance)
        if not hot_start:
            self.set_off()
        pass

    def read_config(self,config):
        self.serialPortName = config.get(self.section_name, 'address')
        pass


    def identify(self):
        self.identifier = self.get_answer_for_query('*IDN?')
        self.get_model_name()

    # ============================
    # ACCESS FUNCTIONS
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


if __name__ == '__main__':
    conf = ConfigParser.ConfigParser()
    conf.read('../config/keithley.cfg')
    iseg = ISEG(conf, 7, False)
