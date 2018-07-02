from termcolor import colored
from interfaces.Keithley24XX import Keithley24XX
from interfaces.Keithley23X import Keithley23X
from interfaces.Keithley6517B import Keithley6517B
from interfaces.Keithley2657 import Keithley2657
from interfaces.ISEG import ISEG
from threading import Thread
from ConfigParser import ConfigParser, NoOptionError
from time import time, sleep, strftime
from math import copysign
import sys
import logging
import os
import json
from Utils import log_warning, log_info

__author__ = 'Michael Reichmann'

ON = True
OFF = False


# ============================
# MAIN CLASS
# ============================
class Device(Thread):
    def __init__(self, config, device_num, hot_start):
        Thread.__init__(self)

        # Basic
        self.isKilled = False
        self.Config = config
        self.SectionName = 'HV{}'.format(device_num)

        # Info fields
        self.bias_now = {}
        self.current_now = {}
        self.status = {}

        # channel stuff
        self.max_channels = self.read_n_channels()
        self.channels = self.__get_channels()
        self.ch_str = ['CH' + str(x) for x in self.channels]
        self.n_channels = len(self.channels)
        self.has_channels = True if self.max_channels > 1 else False
        self.ch_config = self.__get_channel_config()
        self.channel_names = {}
        self.read_channel_names()
        self.init_bias_now()
        self.init_current_now()

        # config data
        self.__ramp_speed = float(config.get(self.SectionName, 'ramp'))
        self.__max_step = config.getint(self.SectionName, 'max_step') if not self.has_channels else None
        self.target_bias = {}
        self.min_bias = {}
        self.max_bias = {}
        self.__read_config()

        self.model_number = self.__get_model_number()
        self.__device_name = self.read_device_name()

        self.interface = None
        self.init_interface(config, device_num, hot_start)

        self.isBusy = False
        self.maxTime = 20

        # evaluate hot start
        if hot_start:
            for chan, ch_num in zip(self.ch_str, self.channels):
                if self.has_channels:
                    self.status[chan] = self.interface.get_output_status(chan)[0]
                else:
                    self.status[chan] = self.interface.get_output_status()
                self.update_voltage_current()
                voltage = self.get_bias(chan)
                print 'Measured voltage: {0:6.2f} V'.format(voltage)
                if self.has_channels:
                    self.interface.set_bias(voltage, ch_num)
                else:
                    self.interface.set_bias(voltage)
                # self.immidiateVoltage = voltage
                self.target_bias[chan] = voltage
                self.bias_now[chan] = voltage
        else:
            self.init_bias_now()
            self.init_status()

        # last time the actual voltage was changed
        self.last_v_change = time()
        self.powering_down = {}
        self.init_power_status()
        self.last_update = time()
        self.manual = False

        # make sure bias is consistent
        for chan in self.channels:
            ch_str = 'CH' + str(chan)
            assert self.max_bias[ch_str] >= self.min_bias[ch_str], 'Invalid config file (maxBias < minBias)'
            assert self.target_bias[ch_str] >= self.min_bias[ch_str] - .1, 'Invalid config file (bias < minBias)'
            assert self.target_bias[ch_str] <= self.max_bias[ch_str] + .1, 'Invalid config file (bias > maxBias)'

        # logging
        self.logger = {}
        self.fh = None
        self.setup_logger()
        self.last_day = strftime('%d')
        self.last_status = self.status
        self.last_ramp = False

        print '---------------------------------------'

    # ============================
    # region INIT DEVICE INTERFACE
    def init_interface(self, config, device_num, hot_start):
        # if statements for model name
        try:
            print 'Instantiation:', self.SectionName, self.Config.get(self.SectionName, 'name')
        except NoOptionError:
            print 'Instantiation:', self.SectionName
        model = self.model_number
        self.isBusy = True
        if model == 2400 or model == 2410:
            self.interface = Keithley24XX(config, device_num, hot_start)
        elif model == (237 or 236 or 238):
            self.interface = Keithley23X(config, device_num, hot_start)
        elif model == '6517B' or model == 6517:
            self.interface = Keithley6517B(config, device_num, hot_start)
        elif model == '2657A' or model == 2657:
            self.interface = Keithley2657(config, device_num, hot_start)
        elif model == 'NHS-6220x':
            self.interface = ISEG(config, device_num, hot_start)
        else:
            print "unknown model number: could not instantiate any device", '--> exiting program'
            sys.exit(-2)
        self.isBusy = False

    def get_device_name(self, chan='CH0'):
        if self.has_channels:
            return self.channel_names[chan]
        else:
            return self.__device_name

    def set_device_name(self, device_name):
        if self.__device_name != device_name:
            self.__device_name = device_name
            self.create_new_log_file()
            print 'Setting device name of %s to "%s"' % (self.SectionName, self.__device_name)

    def read_device_name(self):
        try:
            return self.Config.get('Names', self.SectionName)
        except NoOptionError, err:
            print err, 'setting name to UNKNOWN'
            return 'UNKNOWN'

    def __read_config(self):
        for chan in self.ch_str:
            sec = (chan if self.max_channels > 1 else self.SectionName)
            try:
                self.target_bias[chan] = float(self.ch_config.get(sec, 'bias'))
                self.min_bias[chan] = float(self.ch_config.get(sec, 'min_bias'))
                self.max_bias[chan] = float(self.ch_config.get(sec, 'max_bias'))
            except NoOptionError, err:
                print err, '--> exiting program'
                sys.exit(-1)

    def __get_model_number(self):
        model_number = None
        try:
            model_number = self.Config.get(self.SectionName, 'model')
            model_number = int(model_number)
        except NoOptionError, err:
            print err, '--> exiting program'
            sys.exit(-1)
        except ValueError:
            pass
        return model_number

    def read_n_channels(self):
        try:
            return self.Config.getint(self.SectionName, 'nChannels')
        except NoOptionError:
            return 1

    def init_bias_now(self):
        for chan in self.ch_str:
            self.bias_now[chan] = 0

    def init_current_now(self):
        for chan in self.ch_str:
            self.current_now[chan] = 0

    def init_status(self):
        for chan in self.ch_str:
            self.status[chan] = 0

    def init_power_status(self):
        for chan in self.ch_str:
            self.powering_down[chan] = False

    def read_channel_names(self):
        if self.has_channels:
            for chan in self.ch_str:
                self.channel_names[chan] = self.ch_config.get('Names', chan)
        else:
            self.channel_names = None
    # endregion

    # ============================
    # region LOGGING CONTROL
    def setup_logger(self):
        ch_str = ['_CH' + str(x) for x in self.channels]
        for chan, cha in zip(ch_str, self.ch_str):
            name = self.SectionName + chan
            self.logger[cha] = logging.getLogger(name)
            # self.fh[chan] = None
            self.configure_log(chan)

    def configure_log(self, chan='_CH0'):
        logfile_dir = self.Config.get('Main', 'testbeam_name') + '/'
        logfile_sub_dir = self.interface.name + chan + '/'
        # print logfile_sub_dir,'CHAN: "%s"'%chan
        # check if dir exists
        dirs = os.path.dirname(logfile_dir)
        try:
            os.stat(dirs)
        except OSError:
            os.mkdir(dirs)
        dirs = os.path.dirname(logfile_dir + logfile_sub_dir)
        try:
            os.stat(dirs)
        except OSError:
            os.mkdir(dirs)

        logfile_name = self.interface.get_device_name(1) + strftime('_%Y_%m_%d_%H_%M_%S.log')
        logfile_dest = logfile_dir + logfile_sub_dir + logfile_name
        print "LOGFILE:", logfile_dest
        if self.fh:
            self.logger[chan[1:]].removeHandler(self.fh)
        self.fh = logging.FileHandler(logfile_dest)
        self.fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(message)s', '%H:%M:%S')
        self.fh.setFormatter(formatter)

        self.logger[chan[1:]].addHandler(self.fh)

    def create_new_log_file(self):
        ch_str = ['_CH' + str(x) for x in self.channels]
        for chan in ch_str:
            self.logger[chan[1:]].removeHandler(self.fh)
            self.configure_log(chan)

    # make new logfile when the day changes
    def log_control(self):
        day = strftime('%d')
        if day != self.last_day:
            print 'a new day just begun...'
            self.create_new_log_file()
            self.last_day = day
            sleep(0.1)

    def add_log_entry(self, log_entry, chan=''):
        if not self.logger[chan]:
            self.configure_log()
        self.logger[chan].warning(log_entry + '\t%s' % self.__device_name)

    def write_log(self):
        for chan in self.ch_str:
            # ch_num = int(chan[-1])
            # write when device is turned ON or OFF
            if self.get_last_status()[chan] != self.get_status(chan):
                print 'writing log on/off'
                self.add_log_entry('DEVICE_ON', chan) if self.get_status(chan) else self.add_log_entry('DEVICE_OFF', chan)
            self.last_status = self.status
            # write when ramping starts
            if self.get_last_ramp() != self.is_ramping(chan) and self.get_status(chan):
                if self.is_ramping(chan):
                    log = 'START_RAMPING_AT' + '{0:7.1f}'.format(self.get_bias(chan))
                    self.add_log_entry(log, chan)
                    log = 'TARGET_BIAS' + '{0:7.1f}'.format(self.get_target_bias(chan))
                    self.add_log_entry(log, chan)
            # only write measurements when device is ON
            if self.get_status(chan):
                voltage = self.get_bias(chan)
                current = self.get_current(chan)
                string = "{0:10.3e} {1:10.3e}".format(voltage, current)
                self.add_log_entry(string, chan)
            # write when ramping stops
            if self.get_last_ramp() != self.is_ramping(chan) and self.get_status(chan):
                if not self.is_ramping(chan):
                    log = 'FINISH_RAMPING_AT' + '{0:7.1f}'.format(self.get_bias(chan))
                    self.add_log_entry(log, chan)
            self.last_ramp = self.is_ramping(chan)

    # endregion

    # ============================
    # MAIN LOOP FOR THREAD (overwriting thread run)
    def run(self):
        while not self.isKilled:
            self.log_control()
            sleep(.1)
            if not self.manual:
                self.update_voltage_current()
                self.write_log()
                self.ramp()
                if self.is_ramping('all'):
                    self.update_voltage_current()
                    sleep(.1)

    # ============================
    # region GET-FUNCTIONS
    def get_current(self, chan='CH0'):
        return self.current_now[chan]

    def get_bias(self, chan='CH0'):
        return self.bias_now[chan]

    def get_target_bias(self, chan='CH0'):
        return self.target_bias[chan]

    def get_output(self):
        return self.get_status()

    def get_status(self, chan='CH0'):
        return self.status[chan]

    def get_ramp_speed(self):
        return self.__ramp_speed

    def get_max_step(self):
        return self.__max_step

    def read_status(self):
        if self.has_channels:
            for chan, chan_num in zip(self.ch_str, self.channels):
                self.status[chan] = self.interface.get_output_status(chan_num)[0]
        else:
            self.status['CH0'] = self.interface.get_output_status()

    def get_last_status(self):
        return self.last_status

    def get_update_time(self):
        return self.last_update

    def get_last_ramp(self):
        return self.last_ramp

    def __get_channels(self):
        try:
            return json.loads(self.Config.get(self.SectionName, 'active_channels'))
        except NoOptionError:
            return [0]

    def __get_channel_config(self):
        if self.max_channels > 1:
            ch_conf_file = 'config/' + self.Config.get(self.SectionName, 'config_file')
            ch_config = ConfigParser()
            ch_config.read(ch_conf_file)
            return ch_config
        else:
            return self.Config
    # endregion

    # ============================
    # region SET-FUNCTIONS
    def set_target_bias(self, target, chan):
        if not self.validate_voltage(target, chan):
            return
        self.target_bias[chan] = target
        self.last_v_change = time()
        log_info('Set target bias to {}'.format(target))
        log = 'SET_BIAS_TO' + '{0:7.1f}'.format(target)
        self.add_log_entry(log, chan)

    def set_to_manual(self, status):
        self.target_bias = self.interface.set_to_manual(status)
        self.manual = status

    def set_output(self, status):
        return self.interface.set_output(status)

    def set_ramp_speed(self, speed):
        log_info('Set ramp speed to {}'.format(speed))
        self.__ramp_speed = speed

    def set_max_step(self, step):
        self.__max_step = step

    def set_status(self, channel, status):
        self.status[channel] = status
    # endregion

    # ============================
    # MISCELLANEOUS FUNCTIONS
    def is_ramping(self, chan='CH0'):
        ret_val = None

        if chan == 'all':
            for channel in self.ch_str:
                try:
                    ret_val = (abs(self.bias_now[channel] - self.target_bias[channel]) > 0.5 if self.get_status(channel) else False)
                    if ret_val:
                        return True
                except ValueError:
                    ret_val = False
            return ret_val
        else:
            try:
                return abs(self.bias_now[chan] - self.target_bias[chan]) > 0.5 if self.get_status(chan) else False
            except ValueError:
                return False

    def validate_voltage(self, voltage, channel):
        if not self.min_bias[channel] - .1 < voltage < self.max_bias[channel] + .1:
            log_warning('Invalid target voltage! {v} not in [{b}, {e}]'.format(v=voltage, b=self.min_bias[channel], e=self.max_bias[channel]))
            return False
        return True

    def power_down(self, chan='CH0'):
        self.set_target_bias(0, chan)
        self.powering_down[chan] = True

    def wait_for_device(self):
        now = time()
        while time() - now < self.maxTime and self.isBusy:
            sleep(.2)

    def read_iv(self):
        iv = self.interface.read_iv()
        return iv

    def update_voltage_current(self):
        verb = False
        if verb:
            print 'update_voltage_current'
        self.wait_for_device()
        self.isBusy = True
        try:
            self.read_status()
        except Exception as inst:
            print 'Could not update voltage/current- get output status:', inst, inst.args
            self.isBusy = False
            return
        if verb:
            print '\tstatus', self.status,
        status = True if True in self.status.itervalues() else False
        if status:
            try:
                iv = self.read_iv()
                self.fill_iv_now(iv)
                self.last_update = time()
                # todo fix for channelmode
                # if verb:
                #     print '\tiv: ', iv,
                #     print '\tbias_now', self.bias_now[],
                #     print '\tcurrent_now', self.current_now
                #     print '\treadIV', iv, self.target_bias
            except Exception as inst:
                print 'Could not read valid iv', type(inst), inst
        self.isBusy = False
        if verb:
            print '\tDONE'

    def fill_iv_now(self, vec):
        if self.has_channels:
            for chan, chan_num in zip(self.ch_str, self.channels):
                self.bias_now[chan] = vec[chan_num]['voltage']
                self.current_now[chan] = vec[chan_num]['current']
        else:
            self.bias_now['CH0'] = vec['voltage']
            self.current_now['CH0'] = vec['current']

    def get_bias_now(self, chan='CH0'):
        return self.bias_now[chan]

    def get_current_now(self):
        return self.current_now

    def get_last_update(self):
        return self.last_update

    def get_new_bias(self, chan='CH0'):
        new_bias = 0
        change = False
        delta_v = self.target_bias[chan] - self.interface.target_voltage

        # print 'target: %f \t bias: %f ==> %f V'%(self.target_bias,self.bias_now,delta_v)
        t_now = time()
        delta_t = t_now - self.last_v_change
        step_size = abs(self.__ramp_speed * delta_t)
        # print 'step_size: %f \t %f - %f = %f \t %f'%(step_size,t_now,self.last_v_change,delta_t,self.ramp_speed),

        # Limit the maximal voltage step size
        if step_size > self.__max_step:
            step_size = self.__max_step
        # print step_size

        # print 'delta U ',delta_v,step_size
        if abs(delta_v) > 0.1:
            if abs(delta_v) <= step_size:
                new_bias = self.target_bias[chan]
            else:
                new_bias = self.bias_now[chan] + copysign(step_size, delta_v)
            change = True
        return change, new_bias

    # def check_fast_ramp(self, old_ramp, old_step):
    #     if self.is_ramping('all'):
    #         if not self.interface.started_ramping:
    #             old_ramp = self.get_ramp_speed()
    #             old_step = self.get_max_step()
    #             self.interface.started_ramping = True

    def ramp(self, channel='CH0'):
        # Try to update voltage (we remember the measurement from the last loop)
        # (the step we can make in voltage is the ramp-speed times
        # how many seconds passed since last change)

        for chan in self.ch_str:
            if self.powering_down[chan] and abs(self.bias_now[chan]) < .1:
                if self.has_channels:
                    self.interface.set_output(0, chan)
                else:
                    self.interface.set_output(0)
                self.powering_down[chan] = False
                print '{ch} of {dev} has ramped down and turned off'.format(ch=chan, dev=self.interface.name)
                # End of ramp
                return
        if self.interface.can_ramp:
            for chan, i in zip(self.ch_str, self.channels):
                self.interface.set_voltage(self.target_bias[chan], i)
            return
        if self.status[channel] == OFF:
            change, new_bias = self.get_new_bias()
            self.interface.set_voltage(new_bias)
            return
        tries = 0
        last_bias = self.bias_now[channel]
        while abs(self.interface.target_voltage - self.bias_now[channel]) > 1:
            print self.interface.target_voltage, self.bias_now[channel]
            msg = 'Did not reach the current set voltage on the power supply:\n'
            msg += '\tset_voltage:\t  {0:6.2f} V\n'.format(self.interface.target_voltage)
            msg += '\tmeasured_voltage: {0:6.2f} V'.format(self.bias_now[channel])
            if not self.interface.can_ramp:
                print msg, '\033[99m'
                print "\033[99m" + ' ' + '\033[0m'
            if not self.interface.can_ramp:
                print colored('\nWARNING:', 'yellow'),
                print colored(msg, 'red')
            sleep(1)
            self.update_voltage_current()
            if abs(self.bias_now[channel] - last_bias) < .1:
                tries += 1
            else:
                last_bias = self.bias_now[channel]

            if tries > 10:
                raise ValueError(msg)

        change, new_bias = self.get_new_bias()
        newtime = time()
        # print step_size
        # if tries:
        # self.mimic_cmd()
        # print 'delta U ',delta_v,step_size
        if change:
            # print 'new bias: ',new_bias
            self.isBusy = True
            self.interface.set_voltage(new_bias)
            if new_bias == self.target_bias and not self.powering_down:
                print '\n%s is done with ramping to %d' % (self.interface.name, self.target_bias[channel])
                self.mimic_cmd()
            self.last_v_change = newtime
            self.isBusy = False
        # if self.powering_down and abs(self.bias_now) < .1:
        #     self.interface.set_output(0)
        #     self.powering_down = False
        #     print '\n%s has ramped down and turned off' % self.interface.name
        #     self.mimic_cmd()
        #     # End of ramp
        for chan in self.ch_str:
            if self.powering_down[chan] and abs(self.bias_now[chan]) < .1:
                if self.has_channels:
                    self.interface.set_output(0, chan)
                else:
                    self.interface.set_output(0)
                self.powering_down[chan] = False
                print '%s has ramped down and turned off' % self.interface.name
                # End of ramp

    @staticmethod
    def mimic_cmd():
        print 'HV Cmd =>>> ',
        sys.stdout.flush()


# ============================
# MAIN
# ============================
if __name__ == '__main__':
    conf = ConfigParser()
    conf.read('config/keithley.cfg')
    device_no = 7
    y = Device(conf, device_no, False)

    # keithley1 = HVDevice(conf, 6, False)
    # #keithley2 = HVDevice(conf, 2, False)
    # keithley1.logger.warning("HALLO")
    # #keithley2.logger.warning("HALLO")
