from threading import Thread
from ConfigParser import ConfigParser
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
    def __init__(self, config, device_num, hot_start, print_logs=False, init_logger=True):
        Thread.__init__(self)

        self.Dir = dirname(dirname(realpath(__file__)))

        # Basic
        self.Config = config
        self.SectionName = 'HV{}'.format(device_num)
        self.HotStart = hot_start
        self.PrintLogs = print_logs

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

        # Status
        self.IsKilled = False
        self.IsBusy = False
        self.IsManual = False
        self.IsPoweringDown = [False] * self.NChannels
        self.MaxWaitingTime = 20    # seconds

        self.LastVChange = time()
        self.LastUpdate = time()
        self.CanRamp = False  # set in inheriting classes if ramping is available

        self.Logger = self.init_logger(init_logger)

        print '---------------------------------------'

    # ============================
    # MAIN LOOP FOR THREAD (overwriting thread run)
    def run(self):
        i = 0
        while not self.IsKilled:
            sleep(.1)
            if not self.IsManual:
                # print i
                self.update_voltage_current()
                self.write_logs()
                self.ramp()
                i += 1

    def stop(self):
        self.IsKilled = True
        log_critical('exiting')

    def write_logs(self):
        for channel in self.ActiveChannels:
            self.Logger[channel].write_log(self.get_status(channel), self.get_bias(channel), self.get_current(channel), self.is_ramping(channel), self.get_target_bias(channel), prnt=self.PrintLogs)

    def connect(self):
        log_warning('"connect" not implemented')

    def hot_start(self):
        if self.HotStart:
            for channel in self.ActiveChannels:
                self.set_status(channel, self.get_output_status(channel))
                self.update_voltage_current()
                voltage = self.get_bias(channel)
                log_info('Measured voltage: {0:2.1f} V'.format(voltage))
                self.set_bias(voltage, channel)
                self.set_target_bias(voltage, channel)
                self.BiasNow[channel] = voltage

    # ============================
    # region INIT
        
    def init_logger(self, init=True):
        return [Logger(self.SectionName, channel, self.Config, on=channel in self.ActiveChannels if init else False) for channel in xrange(self.NChannels)]

    def get_device_name(self, chan=0):
        return self.ChannelNames[chan] if self.HasChannels else self.DeviceName

    def set_device_name(self, device_name, channel):
        if self.DeviceName != device_name:
            self.DeviceName = device_name
            self.Logger[channel].create_new_log_file()
            log_info('Setting device name of {} to "{}"'.format(self.SectionName, self.DeviceName))

    def read_device_name(self, channel=0):
        if self.HasChannels:
            return self.ChannelConfig.get('Names', 'CH{}'.format(channel))
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

    def get_output_status(self, channel=0):
        log_warning('get_output_status not implemented')
        return False

    def get_output(self):
        return self.get_status()

    def get_status(self, channel=0):
        return self.Status[channel]

    def get_ramp_speed(self):
        return self.RampSpeed

    def get_max_step(self):
        return self.MaxStep

    def update_status(self):
        for channel in self.ActiveChannels:
            self.set_status(channel, self.get_output_status(channel))

    def get_update_time(self):
        return self.LastUpdate
    # endregion

    # ============================
    # region SET-FUNCTIONS
    def set_bias(self, voltage, channel=0):
        log_warning('set_bias not implemented')

    def set_target_bias(self, target, channel):
        if not self.validate_voltage(target, channel):
            return
        self.TargetBias[channel] = target
        self.LastVChange = time()
        log_info('Set target bias to {}'.format(target))
        self.Logger[self.ActiveChannels.index(channel)].add_entry('SET_BIAS_TO {0:7.1f}'.format(target))

    def set_to_manual(self, status):
        log_warning('set_to_manual not implemented')

    def set_output(self, status, channel=0):
        log_warning('set_output not implemented')

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
    def is_ramping(self, channel=0):
        return abs(self.get_bias(channel) - self.get_target_bias(channel)) > .1 if self.get_status(channel) else False

    def all_are_ramping(self):
        return all(self.is_ramping(channel) for channel in self.ActiveChannels)

    def validate_voltage(self, voltage, channel=0):
        if not self.MinBias[channel] - .1 < voltage < self.MaxBias[channel] + .1:
            log_warning('Invalid target voltage! {v} not in [{b}, {e}]'.format(v=voltage, b=self.MinBias[channel], e=self.MaxBias[channel]))
            return False
        return True

    def power_down(self, channel=0):
        self.set_target_bias(0, channel)
        self.IsPoweringDown[channel] = True

    def wait_for_device(self):
        now = time()
        while time() - now < self.MaxWaitingTime and self.IsBusy:
            sleep(.2)

    def read_iv(self):
        log_warning('read_iv not implemented')
        return []

    def update_voltage_current(self):
        verb = False
        if verb:
            print 'update_voltage_current'
        self.wait_for_device()
        self.IsBusy = True
        try:
            self.update_status()
        except Exception as inst:
            print 'Could not update voltage/current- get output status:', inst, inst.args
            self.IsBusy = False
            return
        if verb:
            print '\tstatus', self.Status,
        status = any(self.Status)
        if status:
            try:
                iv = self.read_iv()
                self.fill_iv_now(iv)
                self.LastUpdate = time()
            except Exception as inst:
                print 'Could not read valid iv', type(inst), inst
        self.IsBusy = False
        if verb:
            print '\tDONE'

    def fill_iv_now(self, data):
        for channel in self.ActiveChannels:
            self.BiasNow[channel] = data[channel]['voltage']
            self.CurrentNow[channel] = data[channel]['current']

    def get_bias_now(self, channel=0):
        return self.BiasNow[channel]

    def get_current_now(self, channel=0):
        return self.CurrentNow[channel]

    def get_last_update(self):
        return self.LastUpdate

    def calc_ramp_bias(self, channel=0):
        """ Calculate the next step of the voltage if there is no inherit ramping method. """
        delta_v = self.get_target_bias(channel) - self.get_bias(channel)
        step_size = copysign(abs(self.RampSpeed * (time() - self.LastVChange)), delta_v)  # get the voltage step by multiplying speed and update interval
        step_size = self.MaxStep if abs(step_size) > self.MaxStep else step_size
        return self.get_target_bias(channel) if abs(delta_v) <= step_size else self.get_bias(channel) + step_size

    def ramp(self):
        """ Try slowly ramp up the voltage by iteratively increasing the set voltage (if the device has not inherent ramping method) """

        for channel in self.ActiveChannels:
            if self.IsPoweringDown[channel] and abs(self.BiasNow[channel]) < .5:
                self.set_output(OFF, channel)
                self.IsPoweringDown[channel] = False
                log_info('CH{ch} of {dev} has ramped down and turned off'.format(ch=channel, dev=self.SectionName))
                return
        if self.CanRamp:
            for channel in self.ActiveChannels:
                self.set_bias(self.get_target_bias(channel), channel)
            return

        # TODO: Shouldn't this be also threaded if there would be a device with several channels and no ramping method?
        for channel in self.ActiveChannels:
            if self.is_ramping(channel):
                self.IsBusy = True
                new_bias = self.calc_ramp_bias(channel)
                self.set_bias(new_bias)
                self.LastVChange = time()
                if new_bias == self.get_target_bias(channel) and not self.IsPoweringDown[channel]:
                    log_info('{} is done with ramping to {} V'.format(self.SectionName, self.get_target_bias()))
                self.IsBusy = False

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
