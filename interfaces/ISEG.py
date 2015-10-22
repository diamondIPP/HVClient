# implementation of ISEG NIM Power supplies
# based on HV_interface class

# ============================
# IMPORTS
# ============================
import ConfigParser
import serial
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
from HV_interface import HVInterface
from time import sleep,time
import math

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

    def open_serial_port(self):
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
        except:
            print 'Could not open serial Port: \'%s\'' % self.serialPortName
            self.bOpen = False
            pass
        self.set_gbip_address()

    def set_gbip_address(self):
        if self.bOpen:
             self.serial.write('++addr %d'%self.gbip)
             retVal = self.__write('++addr ',1)
             print 'Set GBIP Address to %d'%self.gbip

    def init_keithley(self, hot_start):
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
        self.gbip = config.getint(self.section_name, 'gbip')
        self.integration_time = 3
        if config.has_option(self.section_name,'integration_time'):
            self.integration_time = config.getint(  self.section_name,'integration_time')
        self.n_average_filter = 32
        if config.has_option(self.section_name,'n_average_filter'):
            self.n_average_filter = config.getint(  self.section_name,'n_average_filter')
        self.compliance = 1e-6
        if self.config.has_option(self.section_name,'compliance'):
            self.compliance = float(self.config.get(self.section_name,'compliance'))
        self.measure_range_current = 1e-6
        if self.config.has_option(self.section_name,'measure_range'):
            self.measure_range_current = float(self.config.get(self.section_name,'measure_range'))
        pass


if __name__ == '__main__':
    conf = ConfigParser.ConfigParser()
    conf.read('../config/keithley.cfg')
    k237 = ISEG(conf, 7, False)
