# implementation of Keithley 237
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
class Keithley23X(HVInterface):
    def __init__(self, config, device_no=1, hot_start=False):
        self.Busy = False
        HVInterface.__init__(self, config, device_no,hot_start)
        self.bOpen = False
        self.serialPortName = config.get(self.section_name, 'address')
        self.gbip = config.getint(self.section_name, 'gbip')
        self.lastVoltage = 0
        self.serial = None
        self.model = 237
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
        self.set_integration_time(2)
        self.set_averaging_filter(2)
        self.set_output_data_format()
        self.set_compliance(100e-9,100e-9)
        if not hot_start:
            self.set_off()
        pass

    def set_compliance(self,level,measurement_range):
        ranges = {0:0,#auto
                  1:1e-9,
                  2:10e-9,
                  3:100e-9,
                  4:1e-6,
                  5:10e-6,
                  6:100e-6,
                  7:1e-3,
                  8:10e-3,
                  9:100e-3,
                  10:1
                  }
        if measurement_range not in ranges.values():
            measurement_range = 0
            print 'set measurement_range to AUTO'
        try:
            measurement_range = ranges.keys()[ranges.values().index(measurement_range)]
        except:
            measurement_range = 0
            print 'set measurement_range to AUTO'
        # if ranges[measurement_range]  < level:
        #     print 'cannot set level to a higher value than the measurement range'
        self.__execute('L%5E,%d'%(level,measurement_range))

    
    def set_output_sense_local(self):
        return self.__execute('O0')

    def set_output_sense_remote(self):
        return self.__execute('O1')
    
    def set_averaging_filter_exponent(self,n):
        if 0 > n > 5:
             raise Exception('averaging Filter can only be between 0 - 5')
        print 'setting filter to %d readings'%(2**n)
        return self.__execute('P%d'%n)
    
    def set_averaging_filter(self,n):
        if n  == 0:
            exponent = 0
        else:
            exponent =  math.log(n)/math.log(2)
        n = int(exponent)
        if not exponent == int(exponent) or exponent > 5: 
            raise Exception('averaging Filter can only be a factor of 2**X, X in 0 ..5')
        return self.set_averaging_filter_exponent(n)
    
    def set_integration_time(self,n):
        if 0 > n > 3:
            raise Exception('integration time must be in 0-3: 0 [416mus], 1 [4ms], 2 [16.67ms], 3 [20ms]')
    
    def set_output_data_format(self,items=15,format=0,lines=0):
        self.__execute('G%d,%d,%d'%(items,format,lines))
    
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
        retVal = self.__write(message)
        try:
             return retVal[1][-1]
        except Exception, e:
            print retVal
            raise e
        return self.__write(message)[1][-1]

    def __write(self, message,max_time=10):
        time0 = time()
        while self.Busy:
            if time()-time0 > 10:
                raise StandardError('Cannot write - device is busy')
            sleep (.1)
        self.Busy = True
        if not message.startswith('++') and (not message.endswith('\r\n')):
            message += '\r\n'
        if not self.bOpen:
            self.Busy = False
            return -1,[]
        retVal = self.serial.write(message)
        time0 = time()
        while not self.serial.inWaiting():
            time1 = time()
            if time1-time0 > max_time:
                break
            pass
        # print 'DELTA T: ', time1-time0
        sleep(.1)
        retMsg = []
        exception_counter = 0
        while self.serial.inWaiting() and exception_counter < 10:
            try:
                retMsg.append(self.serial.readline().strip('\r\n'))
            except serial.SerialException, e:
                print 'Serial Exception! ',e
                exception_counter += 1
            except Exception,e:
                self.Busy =  False
                raise e
        self.Busy = False
        return retVal,retMsg

    def set_output(self, status):
        if status == True or status == 1:
            return self.__execute('N1')
        else:
            return self.__execute('N0')
        pass

    def set_bias(self, voltage):
        if not -1100 < voltage < 1100:
            raise Exception('Range of Keithley 237 is from -1100.0 V to 1100.0 V')
        self.target_voltage = voltage
        execute_string = 'B%1.3E,0,0' % voltage
        # print 'set bias to %d V'%voltage,execute_string
        return self.__execute(execute_string)

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
        # print retVal
        try:
            return self.extract_machine_status_word(retVal)
        except Exception as e:
            print "Couldn't convert machine status word '%s', exception: %s"%(retVal,e)
            raise Exception("Couldn't convert '%s', exception: %s"%(retVal,e))

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
    
    @staticmethod
    def extract_data(value):
        # NS DC V +1.2345 E+OO, D +12.345 E+OO, NM DC I +1.23456 E+OO, T +123.456 E+OO, B 0000 CRLF
        value = value.split(',')
        retVal = {}
        for entry in value:
            if entry.startswith('NS') or  entry.startswith('OS'):
                retVal.update(Keithley23X.extract_source_data(entry))
            elif entry.startswith('D'):
                retVal.update(Keithley23X.extract_delay(entry))
            elif entry.startswith('NM') or  entry.startswith('OM'):
                retVal.update(Keithley23X.extract_measure_data(entry))
            elif entry.startswith('T'):
                retVal.update(Keithley23X.extract_time_stamp(entry))
            elif entry.startswith('B'):
                retVal.update(Keithley23X.extract_buffer_location(entry))
            else:
                raise Exception('Cannot extract data from \'%s\''%entry) 
        return retVal
#         source_prefix = value[:4]
    
    @staticmethod
    def extract_source_data(entry):
        retVal = {}
        retVal['source_prefix']= entry[:2]
        retVal['source_function'] = entry[2:4]
        retVal['measure_type'] = entry[4]
        retVal['source_value'] = float(entry[5:])
        return retVal
    
    @staticmethod
    def extract_delay(entry):
        return {'delay_value':entry}
        
    @staticmethod
    def extract_measure_data(entry):
        retVal = {}
        retVal['measure_prefix']= entry[:2]
        retVal['measure_function'] = entry[2:4]
        retVal['measure_type'] = entry[4]
        retVal['measure_value'] = float(entry[5:])
        return retVal
        
    @staticmethod
    def extract_time_stamp(entry):
        timestamp = float(entry[1:])
        return {'timestamp_value':timestamp}
        
    @staticmethod
    def extract_buffer_location(entry):
        buffer = int(entry[1:])
        return {'buffer_location':buffer}
    
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
    def extract_machine_status_word(rawvalue):
        # example: MSTG01,0,0K0M000,0N0R1T4,0,0,0V1Y0 <TERM + EOI>
        value = rawvalue
        if type(value)==list:
            value = value[0]
        value = value.strip()
        if not value.startswith('MST'):
            raise Exception('Cannot find suitable identifier \'MST\'')
        try:
            value = value[3:]
            retVal = {}
            retVal.update(Keithley23X.extract_output_data_format(value[:7]))
            value = value[7:]
            retVal.update(Keithley23X.extract_eoi_and_bus_hold_off(value[:2]))
            value = value[2:]
            retVal.update(Keithley23X.extract_srq_mask_and_compliance_select(value[:6]))
            value = value[6:]
            retVal.update(Keithley23X.extract_operate(value[:2]))
            value = value[2:]
            retVal.update(Keithley23X.extract_trigger_control(value[:2]))
            value = value[2:]
            retVal.update(Keithley23X.extract_trigger_configuration(value[:8]))
            value = value[8:]
            retVal.update(Keithley23X.extract_v1100_range_control(value[:2]))
            value = value[2:]
            retVal.update(Keithley23X.extract_terminator(value[:2]))
        except Exception,e:
            print 'error while converting \'%s\''%rawvalue
            raise e

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
        if not value.startswith('G'):
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
        if not value.startswith('K'):
            raise Exception ("Cannot extract eoi and bus hold off, string doesn't start with \'K\', \'%s\'"%value)
        value = int(value[1:])
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
        if len(retVal) == 0:
            raise Exception("Couldn't convert eoi and bus hold off correctly, K%d"%value)
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
        if not value.startswith('M'):
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
        if not value.startswith('N'):
            raise Exception ("Cannot extract operate, string doesn't start with \'N\', \'%s\'"%value)
        retVal = {'operate': int(value[1])==1}
        return retVal
    
    @staticmethod
    def extract_trigger_control(value):
        # example: R1
        # R - Trigger Control
        # O = Disable triggering
        # 1 = Enable triggering
        if not value.startswith('R'):
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
        # 1 = SRC DL Y MSR
        # 2 = SRC DL Y MSR
        # 3 = SRC DL Y MSR
        # 4 = SRC DL Y MSR
        # 5 = *SRC DL Y MSR
        # 6 = SRC DL Y MSR
        # 7 = *SRC DLY MSR
        # 8 = *Single Pulse
        # Trigger Out
        # 0 = None
        # 1 = SRC*DL Y MSR
        # 2 = SRC DL Y*MSR
        # 3 = SRC*DL Y*MSR
        # 4 = SRC DL Y MSR*
        # 5 = SRC*DLY MSR*
        # 6 = SRC DL Y*MSR*
        # 7 = SRC*DL Y*MSR*
        # 8 = Pulse End*
        # Sweep End* Trigger Out
        # 0 = Disabled
        # 1 = Enabled
        if not value.startswith('T'):
            raise Exception ("Cannot extract trigger control, string doesn't start with \'T\', \'%s\'"%value)
        value = value[1:]
        retVal = {}
        retVal['trigger_origin'] = int(value[0])
        retVal['trigger_in'] = int(value[2])
        retVal['triggger_out'] = int(value[4])
        retVal['trigger_sweep_end_out'] = int(value[6])
        return retVal
    
    @staticmethod
    def extract_v1100_range_control(value):
        # example: V 1 
        # V - 11OOV Range Control
        # O = 11OOV Range Disabled
        # 1 = 11OOV Range Enabled (237 only)
        if not value.startswith('V'):
            raise Exception ("Cannot extract v1100 range, string doesn't start with \'V\', \'%s\'"%value)
        retVal = {'v1100_range': bool(value[1])}
        return retVal
    
    @staticmethod
    def extract_terminator(value):
        if not value.startswith('Y'):
            raise Exception ("Cannot extract terminator, string doesn't start with \'Y\', \'%s\'"%value)
        value = int(value[1])
        if value == 0:
            return {'terminator': '\r\n'}
        elif value == 1:
            return {'terminator': '\n\r'}
        elif value == 2:
            return {'terminator': '\r'}
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
        retVal = self.get_machine_status_word()
        if not retVal.has_key('operate'):
            raise IndexError('Cannot find operate in machine status word: %s'%retVal)
        return retVal['operate']

    def get_output_status(self):
        return self.get_output()

    def read_iv(self):
        retVal =  self.__execute('H0')
        converted = self.extract_data(retVal)
        current = converted['measure_value']
        voltage = converted['source_value']
        return {'current':current, 'voltage':voltage}
    
    def read_current(self):
        return self.read_iv()['current']

    def read_voltage(self):
        return self.read_iv()['voltage']
        pass

    def get_model_name(self):
        pass


if __name__ == '__main__':
    conf = ConfigParser.ConfigParser()
    conf.read('../config/keithley.cfg')
    k237 = Keithley23X(conf, 3, False)
