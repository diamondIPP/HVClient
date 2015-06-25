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
        if self.bOpen:
             self.__write('++addr %d'%self.gbip)
             retVal = self.__write('++addr ')
             print 'Set GBIP Address to %d'%self.gbip
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
        return self.__write(message)[1][0]

    def __write(self, message):
        if not message.startswith('++') and (not message.endswith('\r\n')):
            message += '\r\n'
        if not self.bOpen:
            return -1,[]
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
        retVal =  Keithley23X.extract_model_no_and_revision(retVal)
        self.model = retVal[0]
        return retVal

    def get_error_status_word(self):
        retVal =  self.__execute('U1')
        return Keithley23X.extract_error_status_word(retVal)

    def get_stored_ascii_string(self):
        retVal = self.__execute('U2')
        return Keithley23X.extract_stored_ascii_string(retVal)

    def get_machine_status_word(self):
        retVal =  self.__execute('U3')
        print retVal
        return self.extract_machine_status_word(retVal)

    def get_measurement_parameters(self):
        retVal = self.__execute('U4')
        return self.extract_measurement_parameters(retVal)

    def get_compliance_value(self):
        retVal = self.__execute('U5')
        return self.extract_compliance_value(retVal)

    def get_suppression_value(self):
        retVal = self.__execute('U6')
        return self.extract_suppression_value(retVal)

    def get_calibrate_status_word(self):
        retVal = self.__execute('U7')
        return self.extract_calibration_status_word(retVal)

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
    def extract_model_no_and_revision(value):
        value = value.strip()
        try:
            model = int(value[:3])
            return model,value[3:]
        except Exception as e:
            raise Exception('Cannot extract model no and revision from \'%s\, %s'%(value,e))
    
    @staticmethod
    def extract_error_status_word(value):
        value = value.strip()
        if not value.startswith('ERS'):
            raise Exception('Cannot find suitable identifier \'ERS\'')
        # bits:
        # bit 26:Trigger Overrun
        # bit 25IDDC
        # bit 24:IDDCO
        # bit 23:Interlock Present
        # bit 22:Illegal Measure Range
        # bit 21:Illegal Source Range
        # bit 20:Invalid Sweep Mix
        # bit 19:Log Cannot Cross Zero
        # bit 18:Autoranging Source with Pulse Sweep
        # bit 17:In Calibration
        # bit 16:In Standby
        # bit 15:Unit isa236
        # bit 14:IOU DPRAM Failed
        # bit 13:IOU EEROM Failed
        # bit 12:IOU Cal Checksum Error
        # bit 11:DPRAM Lockup
        # bit 10:DPRAM Link Error
        # bit  9:Cal ADC Zero Error
        # bit  8:Cal ADC Gain Error
        # bit  7:Cal SRC Zero Error
        # bit  6:Cal SRC Gain Error
        # bit  5:Cal Common Mode Error
        # bit  4:Cal Compliance Error
        # bit  3:Cal Value Error
        # bit  2:Cal Constants Error
        # bit  1:Cal Invalid Error
        value = value[3:]
        error_status_word = int(value,base=2)
        return value

    @staticmethod
    def extract_stored_ascii_string(value):
        value = value.strip()
        if not value.startswith('DSP'):
            raise Exception('Cannot find suitable identifier \'DSP\'')
        value = value[3:]
        return value
    
    @staticmethod
    def extract_machine_status_word(value):
        # example: M ST G 0 1, 0, 0 K 0 M 0 0 0, 0 N 0 R 1 T 4, 0, 0, 0 V 1 Y 0 <TERM + EOI>
        print value
        if type(value)==list:
            value = value[0]
        print value
        value = value.strip()
        if not value.startswith('MST'):
            raise Exception('Cannot find suitable identifier \'MST\'')
        value = value[3:]
        retVal = {}
        retVal['output_data_format'] = K23X.extract_output_data_format(value[:7])
        value = value[7:]
        retVal['eoi_and_bus_hold_off'] = K23X.extract_eoi_and_bus_hold_off(value[:2])
        value = value[2:]
        retVal['srq_mask_and_compliance_select'] = K23X.extract_srq_mask_and_compliance_select(value[:6])
        value = value[6:]
        retVal['operate'] = K23X.extract_operate(value[:2])
        value = value[2:]
        retVal['trigger_control'] = K23X.extract_trigger_control(value[:2])
        value = value[2:]
        retVal['trigger_configuration'] = K23X.extract_trigger_configuration(value[:8])
        value = value[8:]
        retVal['v1100_range_control'] = K23X.extract_v1100_range_control(value[:2])
        value = value[2:]
        retVal['terminator'] = K23X.extract_terminator(value[:2])
        return retVal
    
    @staticmethod
    def extract_output_data_format(value):
        #example: G 0 1, 0, 0
        #G - Output Data Format
        # Items (sum of bits)
        # 00 =No items
        # 01 = Source value
        # 02 = Delay value
        # 04 = Measure value
        # 08 = Time value
        # Format
        # o =ASCII, prefix and suffix
        # 1 = ASCII, prefix no suffix
        # 2 =ASCII, no prefix or suffix
        # 3 =HP binary
        # 4 = IBM binary
        # Lines
        # o = One line from de buffer
        # 1 = One line from sweep buffer
        # 2 = All lines from sweep buffer
        if not value.startwith('G'):
            raise Exception ("Cannot extract output data format, string doesn't start with \'G\', \'%s\'"%value)
        retVal={}
        value = value[1:]
        retVal['output_items'] = int(value[:2])
        value = value[3:]
        retVal['output_format'] = int(value[0])
        value = value[2:]
        retVal['output_lines'] = int (value)
        return retVal
    
    @staticmethod
    def extract_eoi_and_bus_hold_off(value):
        # example: K 0
        # K - EOI and Bus Hold-off
        # O = Enable EOI and hold-off
        # 1 = Disable EOI, enable hold-off
        # 2 = Enable EOI, disable hold-off
        # 3 = Disable EOI and hold-off
        if not value.startwith('K'):
            raise Exception ("Cannot extract eoi and bus hold off, string doesn't start with \'K\', \'%s\'"%value)
        value = value[1:]
        retVal = {}
        if value == 0:
            retVal['eoi'] = True
            retVal['bus_hold_off'] = True
        elif value == 1:
            retVal['eoi'] = False
            retVal['bus_hold_off'] = True
        elif value == 2:
            retVal['eoi'] = True
            retVal['bus_hold_off'] = False
        elif value == 3:
            retVal['eoi'] = False
            retVal['bus_hold_off'] = False
        return retVal
    
    @staticmethod
    def extract_srq_mask_and_compliance_select(value):
        #example: M 0 0 0, 0
        # M - SRQ Mask and Compliance
        # Select
        # Mask (sum of bits)
        # 000 = Mask cleared
        # 001 = Warning
        # 002 = Sweep done
        # 004 = Trigger out
        # 008 = Reading done
        # 016 = Ready for trigger
        # 032 =Error
        # 128 = Compliance
        # Compliance
        # O =Delay, measure, or idle compliance
        # 1 = Measurement compliance
        if not value.startwith('M'):
            raise Exception ("Cannot extract srq mask and compliance select, string doesn't start with \'M\', \'%s\'"%value)
        value = value[1:]
        retVal = {}
        retVal['srq_mask'] = int(value[:3])
        value = value[4:]
        retVal['compliance_select'] = bool(value)
        return retVal
    
    @staticmethod
    def extract_operate(value):
        # example: N 0
        # N-Operate
        # O =Standby
        # 1 =Operate
        if not value.startwith('N'):
            raise Exception ("Cannot extract operate, string doesn't start with \'N\', \'%s\'"%value)
        retVal = {'operate': bool(value[1])}
        return retVal
    
    @staticmethod
    def extract_trigger_control(value):
        # example: R1
        # R - Trigger Control
        # O = Disable triggering
        # 1 = Enable triggering
        if not value.startwith('R'):
            raise Exception ("Cannot extract trigger control, string doesn't start with \'R\', \'%s\'"%value)
        retVal = {'trigger_control': bool(value[1])}
        return retVal
    
    @staticmethod
    def extract_trigger_configuration(value):
        # example: T 4, 0, 0, 0
        # T - Trigger Configuration
        # Origin
        # 0 = IEEEX
        # 1 =IEEE GET
        # 2 =IEEE talk
        # 3 = External (TRIGGER IN pulse)
        # 4 = Immediate trigger only
        # Trigger In
        # 0 = Continuous
        # 1 = ·SRC DL Y MSR
        # 2 = SRC·DL Y MSR
        # 3 = ·SRC·DL Y MSR
        # 4 = SRC DL Y·MSR
        # 5 = ·SRC DL Y•MSR
        # 6 = SRC·DL Y•MSR
        # 7 = ·SRC·DLY·MSR
        # 8 = ·Single Pulse
        # Trigger Out
        # 0 = None
        # 1 = SRC•DL Y MSR
        # 2 = SRC DL Y·MSR
        # 3 = SRC•DL Y·MSR
        # 4 = SRC DL Y MSR•
        # 5 = SRC•DLY MSR•
        # 6 = SRC DL Y·MSR•
        # 7 = SRC•DL Y•MSR·
        # 8 = Pulse End·
        # Sweep End• Trigger Out
        # 0 = Disabled
        # 1 = Enabled
        if not value.startwith('T'):
            raise Exception ("Cannot extract trigger control, string doesn't start with \'T\', \'%s\'"%value)
        value = value[1:]
        retVal = {}
        retVal['trigger_origin'] = int(value[0])
        retVal['trigger_in'] = int(value[2])
        retVal['triggger_out'] = int(value[4])
        retVal['trigger_sweep_end_out'] = int(value[6])
        return value
    
    @staticmethod
    def extract_v1100_range_control(value):
        # example: V 1 
        # V - 11OOV Range Control
        # O = 11OOV Range Disabled
        # 1 = 11OOV Range Enabled (237 only)
        if not value.startwith('R'):
            raise Exception ("Cannot extract v1100 range, string doesn't start with \'R\', \'%s\'"%value)
        retVal = {'v1100_range': bool(value[1])}
        return retVal
    
    @staticmethod
    def extract_terminator(value):
        if not value.startwith('Y'):
            raise Exception ("Cannot extract terminator, string doesn't start with \'Y\', \'%s\'"%value)
        value = int(value[1])
        if value == 0:
            return {'terminator': '\cr\lf'}
        elif value == 1:
            return {'terminator': '\lf\cr'}
        elif value == 2:
            return {'terminator': '\cr'}
        elif value == 3:
            return {'terminator': ''}
        return value
    
    @staticmethod
    def extract_calibration_status_word(value):
        value = value.strip()
        if not value.startswith('CSP'):
            raise Exception('Cannot find suitable identifier \'CSP\'')
        value = value[3:]
        retVal = {}
        retVal['calibration_step_in_progress'] = int(value[:2])
        value = value[3:]
        retVal['cal_lock_switch'] = bool(value[0])
        value = value[2:]
        retVal['unit_calibrated'] = bool(value[0]) 
        return retVal

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

    @staticmethod
    def extract_sweep_measure_size(value):
        value = value.strip()
        if not value.startswith('SMS'):
            raise Exception('Cannot find correct Identifier \'SMS\'')
        value = value[3:]
        n_measured = int(value)
        return n_measured

    @staticmethod
    def extract_first_sweep_point_in_compliance(value):
        value = value.strip()
        if value == '':
            return []
        #todo
        return value

    @staticmethod
    def extract_suppression_value(value):
        value = value.strip()
        if not value.startswith('ISP') and not value.startswith('VSP'):
            raise Exception('Cannot find Identifier \'ISP\'/\'VSP\'')
        value = value[3:]
        suppression_value = float(value)
        return suppression_value

    @staticmethod
    def extract_compliance_value(value):
        value = value.strip()
        if not value.startswith('ICP') and not value.startswith('VCP'):
            raise Exception('Cannot find Identifier \'ICP\'/\'VCP\'')
        value = value[3:]
        compliance_value = float(value)
        return compliance_value

    @staticmethod
    def extract_defined_sweep_size(value):
        value = value.strip()
        if not value.startswith('DSS'):
            raise Exception('Cannot find Identigier \'DSS\'')
        value = value[3:]
        sweep_size = int(value)
        return sweep_size

    @staticmethod
    def extract_warning_status_word(value):
        value = value.strip()
        if not value.startswith('WRS'):
            raise Exception('Cannot find Identifier \'WRS\'')
        value = value[3:]
        warning = int(value,base=2)
        # bit 10: uncalibrated
        # bit  9: Temporary Cal
        # bit  8: Value Out of Range
        # bit  7: Sweep Buffer Filled
        # bit  6: No Sweep Points, Must Create Sweep Points
        # bit  5: Pulse Times Not Met
        # bit  4: Not In Remote
        # bit  3: Measure Range Changed Due to 1 kV/1 OOmA or 11 OV/1 A Range Select
        # bit  2: Measurement Overflow (OFLO)/Sweep Aborted
        # bit  1: Pending Trigger
        return warning

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
