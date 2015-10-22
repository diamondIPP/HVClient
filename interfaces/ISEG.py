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
        # self.model = self.get_model_name()
        self.identifier = None
        self.answer_time = 0.1
        self.open_serial_port()
        self.init_keithley(hot_start)
        pass



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
        if hot_start:
            sleep(1)
            self.clear_buffer()
            self.identify()
            # self.set_measurement_speed(2)  # was 10 before
            self.clear_error_queue()
            sleep(1)
        else:
            sleep(.1)
            self.set_output(False)
            self.reset()
            self.clear_buffer()
            self.identify()
            self.set_max_voltage()
            # self.set_standard_output_format(':FORM:ELEM VOLT,CURR,RES,TIME,STAT')
            # self.set_concurrent_measurement(True)
            # self.set_filter_type('REP')
            # self.set_average_filter(True)
            # self.set_average_filter_count(3)
            # self.set_current_protection(100e-6)
            # self.set_measurement_speed(2)  # was 10 before
            self.clear_error_queue()
            # self.set_compliance_abort_level('LATE')
            # self.setComplianceAbortLevel('NEVER')
            sleep(.1)
        return

    def read_config(self,config):
        self.serialPortName = config.get(self.section_name, 'address')
        pass


    def identify(self):
        self.identifier = self.get_answer_for_query('*IDN?')
        self.get_model_name()

    def is_valid_voltage(self,voltage,channel):
        if channel < 0 or channel > 5:
            raise AttributeError('Invalid voltage ')
        # todo - write function
        return True

    def is_valid_voltage_bound(self,voltage,channel):
        # todo - write function
        return True

    def is_valid_current(self,current,channel):
        #todo
        return True

    def is_valid_current_bound(self,current_bound,channel):
        # todo
        return True

    def is_valid_channel_string(self,channel):
        channel = str(channel)
        if channel == 'all':
            return True
        try:
            ch = int(channel)
            if 0<=ch <= 5:
                return True
        except:
            pass
        raise AttributeError('invalid channel no %s'%channel)

    def get_channel_string(self, channel):
        print 'get channel string', channel
        if channel == 'all':
            return '0-5'
        if not type(channel)==list:
            channel = [channel]
        valid_channels =  [0<=ch <= 5 for ch in channel]
        if not all(valid_channels):
            raise AttributeError('Invalid channel in list')
        channel = [str(x) for x in channel]
        return ','.join(channel)


    # ============================
    # DEVICE FUNCTIONS
    def set_output(self, status, channel='all'):
        ch_str = str(channel)
        all_str = 'of channel ' + ch_str
        if channel=='all':
            ch_str = '0-5'
            all_str = 'of all channels'
        print_value = 'set Output {all} to '.format(all=all_str)
        data = ':VOLT '
        data += ('ON' if status else 'OFF')
        data += ',(@{ch})'.format(ch=ch_str)
        print_value += ('ON' if status else 'OFF')
        print print_value
        return self.write(data)

    def set_channel_voltage(self,voltage,channel=-1):
        self.is_valid_channel_string(channel)
        self.is_valid_voltage(voltage,channel)
        data = ':VOLT %.3f (@%d)'%(voltage,channel)
        print 'set Voltage of channel %d to %.3f V'%(channel,voltage)
        return self.write(data)

    def set_emergency_off(self,channel='all'):
        self.is_valid_channel_string(channel)
        print 'Emergency off for channel(s) %s'%channel
        data = ':VOLT EMCY OFF(@ch%s)'%channel
        return self.write(data)

    def set_emergency_clear(self,channel='all'):
        self.is_valid_channel_string(channel)
        print 'Emergency clear for channel(s) %s'%channel
        data = ':VOLT EMCY CLR(@ch%s)'%channel
        return self.write(data)

    def set_channel_voltage_bound(self,voltage_bound,channel=-1):
        self.is_valid_channel_string(channel)
        self.is_valid_voltage_bound(voltage_bound,channel)
        data = ':VOLT:BOU %.3f (@%s)'%(voltage_bound,channel)
        return self.write(data)

    def set_channel_current(self,current,channel=-1):
        self.is_valid_channel_string(channel)
        self.is_valid_current(current,channel)
        data = ':CURR %.3f (@%d)'%(current,channel)
        print 'set Current of channel %d to %.3f V'%(channel,current)
        return self.write(data)

    def set_channel_current_bound(self,current_bound,channel=-1):
        self.is_valid_channel_string(channel)
        self.is_valid_current_bound(current_bound,channel)
        data = ':CURR:BOU %.3e (@%s)'%(current_bound,channel)
        print 'set current bound of %d to %.3e A'%(channel,current_bound)
        return self.write(data)

    def clear_channel_events(self,channel=-1):
        self.is_valid_channel_string(channel)
        data = ':EV:CLEAR (@%s)'%channel
        print 'Clear channel events @ch'%channel
        return self.write(data)

    def set_channel_event_mask(self,mask_word,channel=-1):
        self.is_valid_channel_string(channel)
        self.is_valid_channel_mask(mask_word)
        print 'set channel event mask for ch %s to "%s"'%(channel,bin(mask_word))
        data = ':EV:MASK %s'%mask_word
        return self.write(data)
    # todo :CONFIGURE:TRIP
    # todo :CONFIGURE:INH

    def configure_ramp_speed(self,speed,ramp_type):
        if len(ramp_type) > 4:
            ramp_type = ramp_type[:4]
        ramp_type = ramp_type.upper()
        if not ramp_type in ['VOLT','CURR']:
            raise AttributeError('Invalid Type of ramp speed')
        if not 0< speed <= 100:
            AttributeError('Invalid speed for ramp speed')
        data = ':CONF:RAMP:%s %.1f'%(ramp_type,speed)
        print 'Set %s ramp speed to %.1f %/s'%(ramp_type,speed)
        return self.write(data)

    def configure_ramp_speed_voltage(self,speed):
        self.configure_ramp_speed(speed,'VOLT')

    def configure_ramp_speed_current(self,speed):
        self.configure_ramp_speed(speed,'CURR')

    def configure_average(self,filterSteps):
        valid_steps = [1,16,64,256,512,1024]
        if not filterSteps in valid_steps:
            raise AttributeError('FilterSteps must be in %s'%valid_steps)
        data = ':CONF:AVER %d'%filterSteps
        print 'Set Average Filter Steps to %d'%filterSteps
        return self.write(data)

    def get_average_filter_steps(self):
        return int(self.get_answer_for_query(':CONF:AVER?'))

    def set_kill_function(self,value):
        value = bool(value)
        data = ':CONF:KILL %s'
        if value:
            retval = 'ENABLE'
        else:
            retval = 'DISABLE'
        print '%s kill function'%retval.lower()
        return self.write(data%retval)

    def is_kill_function_active(self):
        retval = self.get_answer_for_query(':CONF:KILL?')
        return bool(retval)

    #todo :CONF:EV:CLEAR
    #todo :CONF:EV <WORD>
    #todo :CONF:EV:MASK
    #todo :CONF:EV:CHANMASK

    def read_current(self,channel=-1):
        ch = self.get_channel_string(channel)
        retVal = (self.get_answer_for_query(':MEAS:CURR? (@%s)'%ch)).split()
        retVal = [k[:-1] for k in retVal]
        return retVal

    def read_voltage(self,channel=-1):
        ch = self.get_channel_string(channel)
        retVal = (self.get_answer_for_query(':MEAS:CURR? (@%s)'%ch)).split()
        retVal = [k[:-1] for k in retVal]
        return retVal

    def reset(self):
        self.write('*RST')
        self.serial.readall()
        return self.serial.inWaiting()

    def clear_error_queue(self):
        self.write('*CLS')
        self.serial.readall()
        return self.serial.inWaiting()

    def clear_buffer(self):
        if self.bOpen:
            while self.serial.inWaiting():
                self.read()
                sleep(self.readSleepTime)
        else:
            pass
        return self.serial.inWaiting()

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
        # if not self.serial.inWaiting():
        #     print 'there is nothing in the queue'
        #     return
        out = ''
        if not self.bOpen:
            if not self.bOpenInformed:
                print 'cannot read since Not serial port is not open'
                self.bOpenInformed = False
            return ''
        ts = time()
        max_time = 300
        k = 0
        clear_first = False
        while True:
            while self.serial.inWaiting() > 0 and time() - ts < max_time and not out.endswith(self.commandEndCharacter):
                out += self.serial.read(1)
                k += 1
            if out == '':
                break
            if out.endswith(self.commandEndCharacter):
                if out.startswith('*') or out.startswith(':'):
                    out = ''
                    continue
                else:
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
    # GET-FUNCTIONS
    def get_model_name(self):
        self.model = 9999
        if self.identifier == '':
            self.identify()
        else:
            ident_list = self.identifier.split()
            if len(ident_list) > 5:
                mod = ident_list[3] + ident_list[4]
                self.model = int(mod) if self.is_number(mod) else mod
            print 'Connected iseg model', self.model
        self.set_max_voltage()

    # ============================
    # SET-FUNCTIONS
    def set_max_voltage(self):
        self.max_voltage = 3000



if __name__ == '__main__':
    conf = ConfigParser.ConfigParser()
    conf.read('../config/keithley.cfg')
    i = ISEG(conf, 7, False)
