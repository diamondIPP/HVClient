# implementation of Keithley 237
# based on HV_interface class

# ============================
# IMPORTS
# ============================
import ConfigParser
import serial
from HV_interface import HVInterface
from time import sleep

# ============================
# CONSTANTS
# ============================
ON = 1
OFF = 0


# ============================
# MAIN CLASS
# ============================
class Keithley23X(HVInterface):
    def __init__(self, config, device_no=1, hot_start=False):
        HVInterface.__init__(self, config, device_no)
        self.bOpen = False
        self.serialPortName = config.get(self.section_name, 'address')
        self.gbip = config.getint(self.section_name, 'gbip')
        self.lastVoltage = 0
        self.serial = None
        self.model = 237
        self.identifier = None
        self.answer_time = 0.1
        self.open_serial_port(hot_start)
        pass

    def open_serial_port(self, hot_start):
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
        self.__write('++addr %d' % self.gbip)
        retVal = self.__write('++addr ')
        print 'Set GBIP Address to %d' % self.gbip
        self.init_keithley(hot_start)

    def init_keithley(self, hot_start):
        self.set_source_voltage_dc()
        self.set_1100V_range(True)
        pass

    def set_source_voltage_dc(self):
        return self.__execute('F0,0')

    def set_source_voltage_sweep(self):
        return self.__execute('F0,1')

    def set_source_current_dc(self):
        return self.__execute('F1,0')

    def set_source_current_sweep(self):
        return self.__execute('F1,1')

    def set_1100V_range(self, val=True):
        if val:
            return self.__execute('V1')
        else:
            return self.__execute('V0')

    def set_display(self, msg, mode=1):
        msg = str(msg).upper()
        return self.__execute('D%d,%s' % (mode, msg))

    def write(self, message):
        return self.__write(message)

    def __execute(self, message):
        message = message.strip('\r\n')
        if not message.endswith('X'):
            message+='X'
        return self.__write(message)[1]

    def __write(self, message):
        if not message.startswith('++') and (not message.endswith('\r\n')):
            message += '\r\n'
        retVal = self.serial.write(message)
        sleep(self.answer_time)
        retMsg = []
        while self.serial.inWaiting():
            retMsg.append(self.serial.readline().strip('\r\n'))
        return retVal,retMsg

    def set_output(self, status):
        pass

    def set_bias(self, voltage):
        if not -1100 < voltage < 1100:
            raise Exception('Range of Keithley 237 is from -1100.0 V to 1100.0 V')
        self.set_voltage = voltage
        return self.__execute('B%1.3E,0,0' % voltage)

    def get_model_no_and_revision(self):
        retVal = self.__execute('U0')
        return self.extract_model_no_and_revision(retVal)

    def get_error_status_word(self):
        return self.__execute('U1')

    def get_stored_ascii_string(self):
        return self.__execute('U2')

    def get_machine_status_word(self):
        retVal =  self.__execute('U3')
        return extract_machine_status_word(retVal)

    def get_measurement_parameters(self):
        retVal = self.__execute('U4')
        return self.extract_measurement_parameters(retVal)

    def get_compliance_value(self):
        retVal = self.__execute('U5')
        return self.extract_compliance_value(retVal)

    def get_surpression_value(self):
        retVal = self.__execute('U6')
        return self.extract_surpression_value(retVal)

    def get_calibrate_status_word(self):
        return self.__execute('U7')

    def get_defined_sweep_size(self):
        retVal = self.__execute('U8')
        return self.extract_defined_sweep_size()

    def get_warning_status_word(self):
        return self.__execute('U9')

    def get_first_sweep_point_in_compliance(self):
        retVal = self.__execute('U10')
        return self.extract_first_sweep_point_in_compliance(retVal)

    def get_sweep_measure_size(self):
        retVal = self.__execute('U11')
        return self.extract_sweep_measure_size(retVal)

    #returns model no and revision number
    @staticmethod
    def extract_model_no_and_revision(self,value):
        value = value.strip()
        return int(value[:3]),value[3:]

    @staticmethod
    def convert_integration_time(value):
        if 0 > value > 3:
            raise Exception('Invalid Value for conversion, allowed values are 0 - 3')
        if value == 0:
            return 416e-6,4
        elif value == 1:
            return 4e-3,5
        elif value == 2:
            return 16.67e-3,5
        elif value == 3:
            return 20e-3,5
        raise Exception()
    @staticmethod
    def extract_measurement_parameters(value):
        retVal = {}
        print value
        if not value.startswith('IMP'):
            raise Exception('Invalid input, input has to start with identifier \'IMP\'')
        value = value[3:]
        print value
        if not value.startswith('L,'):
            raise Exception('Invalid String cannot find compliance/measurement range, starting with \'L\'')
        retVal['measurement_range'] = int(value[2:4])
        value = value[4:]
        print value
        if not value.startswith('F'):
            raise Exception('Invalid String, cannot find source and function, starting with \'F\'')
        retVal['source_function'] = value[1:4]
        value = value[4:]
        print value
        if not value.startswith('O'):
            raise Exception('Invalid String, cannot find output sense, starting with \'O\'')
        retVal['output_sense'] = int(value[1])
        value = value[2:]
        print value
        if not value.startswith('P'):
            raise Exception('Invalid String, cannot find Filter, starting with \'P\'')
        ret = int(value[1])
        if ret != 0:
            ret = 2**ret
        retVal['filter'] = ret
        value = value[2:]
        print value
        if not value.startswith('S'):
            raise Exception('Invalid String, cannot find Integration Time, starting with \'S\'')
        retVal['integration_time'] = Keithley23X.convert_integration_time(int(value[1]))
        value = value[2:]
        print value
        if not value.startswith('W'):
            raise Exception('Invalid String, cannot find Default Delay, starting with \'W\'')
        retVal['default_delay'] = bool(value[1])
        value = value[2:]
        print value
        if not value.startswith('Z'):
            raise Exception('Invalid String, cannot find Suppression, starting with \'Z\'')
        retVal['suppression'] =  bool(value[1])
        return retVal




    def extract_sweep_measure_size(self,value):
        return value

    def extract_first_sweep_point_in_compliance(self, value):
        return value

    def extract_surpression_value(self, value):
        return value

    def extract_compliance_value(self, value):
        return value

    def extract_defined_sweep_size(self, value):
        return value

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
    k237 = Keithley23X(conf, 2, False)
