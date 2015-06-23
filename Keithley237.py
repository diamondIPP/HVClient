# implementation of Keithley 237
# based on HV_interface class

# ============================
# IMPORTS
# ============================
import ConfigParser
import serial
from HV_interface import HVInterface

# ============================
# CONSTANTS
# ============================
ON = 1
OFF = 0


# ============================
# MAIN CLASS
# ============================
class Keithley237(HVInterface):
    def __init__(self, config, device_no=1, hot_start=False):
        HVInterface.__init__(self, config, device_no, hot_start)
        self.bOpen = False
        self.serialPortName = config.get(self.section_name, 'address')
        self.gbip = config.getint(self.section_name, 'gbip')
        self.lastVoltage = 0
        self.serial = None
        self.model = 237
        self.identifier = None
        self.open_serial_port(hot_start)
        pass

    def open_serial_port(self,hot_start):
         try:
            self.serial = serial.Serial(
                                        port=self.serialPortName,
                                        baudrate=57600,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        bytesize=serial.EIGHTBITS,
                                        timeout=1,
            )
            self.bOpen=True
            print 'Open serial port: \'%s\''%self.serialPortName
         except:
            print 'Could not open serial Port: \'%s\''%self.serialPortName
            self.bOpen=False
            pass
         self.__write('++addr %d'%self.gbip)
         retVal = self.__write('++addr ')
         print 'Set GBIP Address to %d'%self.gbip

    def write(self,message):
        return self.__write(message)

    def __write(self,message):
        if not message.startswith('++') and (not message.endswith('\r\n')):
            message += '\r\n'
        retVal = self.serial.write(message)
        retMsg = []
        while self.serial.inWaiting():
            retMsg.append(self.serial.readline())
        return retVal,retMsg

    def set_display(self,msg):
        msg = str(msg).upper()
        return self.__write('D1,%sX'%msg)

    def set_output(self, status):
        pass

    def set_bias(self, voltage):
        pass

    def get_output(self):
        pass

    def read_current(self):
        pass

    def read_voltage(self):
        pass

    def get_model_name(self):
        pass


if __name__ == '__main__':
    conf = ConfigParser.ConfigParser()
    conf.read('keithley.cfg')
    k237 = Keithley237(conf, 2, False)
