from termcolor import colored
from interfaces.Keithley24XX import Keithley24XX
from interfaces.Keithley23X import Keithley23X
from interfaces.Keithley6517B import Keithley6517B
from interfaces.Keithley2657 import Keithley2657
from interfaces.ISEG import ISEG
from threading import Thread
from ConfigParser import ConfigParser, NoOptionError
from time import time, sleep
from math import copysign
import sys
from Logger import Logger
from Utils import log_warning, log_info, isint, log_critical
from json import loads
from os.path import dirname, realpath, join

__author__ = 'Michael Reichmann'

ON = True
OFF = False


# ============================
# MAIN CLASS
# ============================
class Device(Thread):
    def __init__(self, config, device_num, hot_start):
        Thread.__init__(self)

        self.Dir = dirname(realpath(__file__))

        # Basic
        self.Config = config
        self.SectionName = 'HV{}'.format(device_num)

        # Channel stuff
        self.NChannels = self.read_n_channels()
        self.HasChannels = self.NChannels > 1
        self.ActiveChannels = self.read_active_channels()
        self.ChannelConfig = self.read_channel_config()
        self.ChannelNames = self.read_channel_names()

        # Info fields
        self.BiasNow = [0] * self.NChannels
        self.CurrentNow = [0] * self.NChannels
        self.Status = [0] * self.NChannels

        # Config data
        self.RampSpeed = config.getfloat(self.SectionName, 'ramp')
        self.MaxStep = config.getint(self.SectionName, 'max_step') if config.has_option(self.SectionName, 'max_step') else None
        self.MinBias = self.read_min_bias()
        self.MaxBias = self.read_max_bias()
        self.TargetBias = self.read_target_bias()

        self.ModelNumber = self.get_model_number()
        self.DeviceName = self.read_device_name()

        self.interface = None
        self.init_interface(config, device_num, hot_start)

        # Status
        self.IsKilled = False
        self.IsBusy = False
        self.IsManual = False
        self.IsPoweringDown = [False] * self.NChannels
        self.MaxWaitingTime = 20    # seconds

        # evaluate hot start
        if hot_start:
            for channel in self.ActiveChannels:
                ch_str = 'CH{}'.format(channel)
                if self.HasChannels:
                    self.Status[channel] = self.interface.get_output_status(ch_str)[0]
                else:
                    self.Status[channel] = self.interface.get_output_status()
                self.update_voltage_current()
                voltage = self.get_bias(channel)
                print 'Measured voltage: {0:6.2f} V'.format(voltage)
                if self.HasChannels:
                    self.interface.set_bias(voltage, ch_str)
                else:
                    self.interface.set_bias(voltage)
                # self.immidiateVoltage = voltage
                self.TargetBias[channel] = voltage
                self.BiasNow[channel] = voltage

        # last time the actual voltage was changed
        self.LastVChange = time()
        self.LastUpdate = time()

        self.Logger = self.init_logger()

        print '---------------------------------------'

    # ============================
    # MAIN LOOP FOR THREAD (overwriting thread run)
    def run(self):
        while not self.IsKilled:
            sleep(.1)
            if not self.IsManual:
                self.update_voltage_current()
                self.write_logs()
                self.ramp()
                if self.is_ramping('all'):
                    self.update_voltage_current()
                    sleep(.1)
                    
    def write_logs(self):
        for channel in self.ActiveChannels:
            self.Logger[channel].write_log(self.get_status(channel), self.get_bias(channel), self.get_current(channel), self.is_ramping(channel), self.get_target_bias(channel))

    # ============================
    # region INIT DEVICE INTERFACE
    def init_interface(self, config, device_num, hot_start):
        # if statements for model name
        try:
            print 'Instantiation:', self.SectionName, self.Config.get(self.SectionName, 'name')
        except NoOptionError:
            print 'Instantiation:', self.SectionName
        model = self.ModelNumber
        self.IsBusy = True
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
        self.IsBusy = False
        
    def init_logger(self):
        return [Logger(self.SectionName, channel, self.Config) for channel in self.ActiveChannels]

    def get_device_name(self, chan=0):
        return self.ChannelNames[chan] if self.HasChannels else self.DeviceName

    def set_device_name(self, device_name, channel):
        if self.DeviceName != device_name:
            self.DeviceName = device_name
            self.Logger[channel].create_new_log_file()
            log_info('Setting device name of {} to "{}"'.format(self.SectionName, self.DeviceName))

    def read_device_name(self):
        if self.Config.has_option('Names', self.SectionName):
            return self.Config.get('Names', self.SectionName)
        log_warning('Setting device name to "UNKNOWN"')
        return 'UNKNOWN'

    def read_target_bias(self):
        biases = []
        for i in xrange(self.NChannels):
            bias = self.ChannelConfig.getfloat('CH{}'.format(i), 'bias')
            if not self.validate_voltage(bias, i):
                log_critical('End program')
            biases.append(bias)
        return biases

    def read_min_bias(self):
        return [self.ChannelConfig.getfloat('CH{}'.format(i), 'min_bias') for i in xrange(self.NChannels)]

    def read_max_bias(self):
        return [self.ChannelConfig.getfloat('CH{}'.format(i), 'max_bias') for i in xrange(self.NChannels)]

    def get_model_number(self):
        if not self.Config.has_option(self.SectionName, 'model'):
            log_critical('You have to specify the model in the config file!')
        model_number = self.Config.get(self.SectionName, 'model')
        return int(model_number) if isint(model_number) else model_number

    def read_n_channels(self):
        return self.Config.getint(self.SectionName, 'n_channels') if self.Config.has_option(self.SectionName, 'n_channels') else 1

    def read_active_channels(self):
        return loads(self.Config.get(self.SectionName, 'active_channels')) if self.HasChannels else [0]

    def read_channel_config(self):
        if not self.HasChannels:
            config = ConfigParser()
            config.add_section('CH0')
            for option in self.Config.options(self.SectionName):
                config.set('CH0', option, self.Config.get(self.SectionName, option))
            return config
        config = ConfigParser()
        config.read(join(self.Dir, 'config', self.Config.get(self.SectionName, 'config_file')))
        return config

    def read_channel_names(self):
        if self.HasChannels:
            return [self.ChannelConfig.get('Names', 'CH{}'.format(i)) for i in xrange(self.NChannels)]
    # endregion
    
    # ============================
    # region GET-FUNCTIONS
    def get_current(self, channel=0):
        return self.CurrentNow[channel]

    def get_bias(self, channel=0):
        return self.BiasNow[channel]

    def get_target_bias(self, channel=0):
        return self.TargetBias[channel]

    def get_output(self):
        return self.get_status()

    def get_status(self, channel=0):
        return self.Status[channel]

    def get_ramp_speed(self):
        return self.RampSpeed

    def get_max_step(self):
        return self.MaxStep

    def read_status(self):
        if self.HasChannels:
            for chan, chan_num in zip(self.ch_str, self.ActiveChannels):
                self.Status[chan] = self.interface.get_output_status(chan_num)[0]
        else:
            self.Status['CH0'] = self.interface.get_output_status()

    def get_update_time(self):
        return self.LastUpdate
    # endregion

    # ============================
    # region SET-FUNCTIONS
    def set_target_bias(self, target, chan):
        if not self.validate_voltage(target, chan):
            return
        self.TargetBias[chan] = target
        self.LastVChange = time()
        log_info('Set target bias to {}'.format(target))
        log = 'SET_BIAS_TO' + '{0:7.1f}'.format(target)
        self.add_log_entry(log, chan)

    def set_to_manual(self, status):
        self.TargetBias = self.interface.set_to_manual(status)
        self.IsManual = status

    def set_output(self, status):
        return self.interface.set_output(status)

    def set_ramp_speed(self, speed):
        log_info('Set ramp speed to {}'.format(speed))
        self.RampSpeed = speed

    def set_max_step(self, step):
        self.MaxStep = step

    def set_status(self, channel, status):
        self.Status[channel] = status
    # endregion

    # ============================
    # MISCELLANEOUS FUNCTIONS
    def is_ramping(self, chan='CH0'):
        ret_val = None

        if chan == 'all':
            for channel in self.ch_str:
                try:
                    ret_val = (abs(self.BiasNow[channel] - self.TargetBias[channel]) > 0.5 if self.get_status(channel) else False)
                    if ret_val:
                        return True
                except ValueError:
                    ret_val = False
            return ret_val
        else:
            try:
                return abs(self.BiasNow[chan] - self.TargetBias[chan]) > 0.5 if self.get_status(chan) else False
            except ValueError:
                return False

    def validate_voltage(self, voltage, channel=0):
        if not self.MinBias[channel] - .1 < voltage < self.MaxBias[channel] + .1:
            log_warning('Invalid target voltage! {v} not in [{b}, {e}]'.format(v=voltage, b=self.MinBias[channel], e=self.MaxBias[channel]))
            return False
        return True

    def power_down(self, chan='CH0'):
        self.set_target_bias(0, chan)
        self.IsPoweringDown[chan] = True

    def wait_for_device(self):
        now = time()
        while time() - now < self.MaxWaitingTime and self.IsBusy:
            sleep(.2)

    def read_iv(self):
        iv = self.interface.read_iv()
        return iv

    def update_voltage_current(self):
        verb = False
        if verb:
            print 'update_voltage_current'
        self.wait_for_device()
        self.IsBusy = True
        try:
            self.read_status()
        except Exception as inst:
            print 'Could not update voltage/current- get output status:', inst, inst.args
            self.IsBusy = False
            return
        if verb:
            print '\tstatus', self.Status,
        status = True if True in self.Status.itervalues() else False
        if status:
            try:
                iv = self.read_iv()
                self.fill_iv_now(iv)
                self.LastUpdate = time()
                # todo fix for channelmode
                # if verb:
                #     print '\tiv: ', iv,
                #     print '\tbias_now', self.bias_now[],
                #     print '\tcurrent_now', self.current_now
                #     print '\treadIV', iv, self.target_bias
            except Exception as inst:
                print 'Could not read valid iv', type(inst), inst
        self.IsBusy = False
        if verb:
            print '\tDONE'

    def fill_iv_now(self, vec):
        if self.HasChannels:
            for chan, chan_num in zip(self.ch_str, self.ActiveChannels):
                self.BiasNow[chan] = vec[chan_num]['voltage']
                self.CurrentNow[chan] = vec[chan_num]['current']
        else:
            self.BiasNow['CH0'] = vec['voltage']
            self.CurrentNow['CH0'] = vec['current']

    def get_bias_now(self, chan='CH0'):
        return self.BiasNow[chan]

    def get_current_now(self):
        return self.CurrentNow

    def get_last_update(self):
        return self.LastUpdate

    def get_new_bias(self, chan='CH0'):
        new_bias = 0
        change = False
        delta_v = self.TargetBias[chan] - self.interface.target_voltage

        # print 'target: %f \t bias: %f ==> %f V'%(self.target_bias,self.bias_now,delta_v)
        t_now = time()
        delta_t = t_now - self.LastVChange
        step_size = abs(self.RampSpeed * delta_t)
        # print 'step_size: %f \t %f - %f = %f \t %f'%(step_size,t_now,self.last_v_change,delta_t,self.ramp_speed),

        # Limit the maximal voltage step size
        if step_size > self.MaxStep:
            step_size = self.MaxStep
        # print step_size

        # print 'delta U ',delta_v,step_size
        if abs(delta_v) > 0.1:
            if abs(delta_v) <= step_size:
                new_bias = self.TargetBias[chan]
            else:
                new_bias = self.BiasNow[chan] + copysign(step_size, delta_v)
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
            if self.IsPoweringDown[chan] and abs(self.BiasNow[chan]) < .1:
                if self.HasChannels:
                    self.interface.set_output(0, chan)
                else:
                    self.interface.set_output(0)
                self.IsPoweringDown[chan] = False
                print '{ch} of {dev} has ramped down and turned off'.format(ch=chan, dev=self.interface.name)
                # End of ramp
                return
        if self.interface.can_ramp:
            for chan, i in zip(self.ch_str, self.ActiveChannels):
                self.interface.set_voltage(self.TargetBias[chan], i)
            return
        if self.Status[channel] == OFF:
            change, new_bias = self.get_new_bias()
            self.interface.set_voltage(new_bias)
            return
        tries = 0
        last_bias = self.BiasNow[channel]
        while abs(self.interface.target_voltage - self.BiasNow[channel]) > 1:
            print self.interface.target_voltage, self.BiasNow[channel]
            msg = 'Did not reach the current set voltage on the power supply:\n'
            msg += '\tset_voltage:\t  {0:6.2f} V\n'.format(self.interface.target_voltage)
            msg += '\tmeasured_voltage: {0:6.2f} V'.format(self.BiasNow[channel])
            if not self.interface.can_ramp:
                print msg, '\033[99m'
                print "\033[99m" + ' ' + '\033[0m'
            if not self.interface.can_ramp:
                print colored('\nWARNING:', 'yellow'),
                print colored(msg, 'red')
            sleep(1)
            self.update_voltage_current()
            if abs(self.BiasNow[channel] - last_bias) < .1:
                tries += 1
            else:
                last_bias = self.BiasNow[channel]

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
            self.IsBusy = True
            self.interface.set_voltage(new_bias)
            if new_bias == self.TargetBias and not self.IsPoweringDown:
                print '\n%s is done with ramping to %d' % (self.interface.name, self.TargetBias[channel])
                self.mimic_cmd()
            self.LastVChange = newtime
            self.IsBusy = False
        # if self.powering_down and abs(self.bias_now) < .1:
        #     self.interface.set_output(0)
        #     self.powering_down = False
        #     print '\n%s has ramped down and turned off' % self.interface.name
        #     self.mimic_cmd()
        #     # End of ramp
        for chan in self.ch_str:
            if self.IsPoweringDown[chan] and abs(self.BiasNow[chan]) < .1:
                if self.HasChannels:
                    self.interface.set_output(0, chan)
                else:
                    self.interface.set_output(0)
                self.IsPoweringDown[chan] = False
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
