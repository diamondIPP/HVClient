from glob import glob
from math import copysign
from os.path import join
from threading import Thread
from time import sleep
from os import SEEK_END

from HVClient.src.logger import Logger
from HVClient.src.utils import *
from HVClient.src.config import Config
from numpy import sign

__author__ = 'Michael Reichmann'


class Device(Thread):
    def __init__(self, device_num, config='main', hot_start=True, print_logs=False, init_logger=True, start_time='now'):
        Thread.__init__(self)

        self.Dir = dirname(dirname(realpath(__file__)))

        # Basic
        self.Config = Config(config, init_logger, 'HV{}'.format(device_num))
        self.HotStart = hot_start
        self.PrintLogs = print_logs

        # Channel stuff
        self.NChannels = self.Config.get_value('number of channels', int, default=1)
        self.ActiveChannels = self.Config.get_active_channels()

        # Info fields
        self.BiasNow = zeros(self.NChannels)
        self.CurrentNow = zeros(self.NChannels)
        self.Status = zeros(self.NChannels, bool)

        # Channel Config Data
        self.RampSpeed = self.Config.get_channel_values('ramping speed')
        self.MaxStep = self.Config.get_channel_values('maximum step', float, default=200)
        self.MaxBias = abs(self.Config.get_channel_values('maximum bias', float, default=200))
        self.TargetBias = self.read_target_bias()
        self.Names = self.Config.get_dut_names()

        self.ModelNumber = self.read_model_number()

        # Status
        self.IsKilled = False
        self.IsBusy = False
        self.IsManual = False
        self.IsPoweringDown = zeros(self.NChannels, bool)
        self.MaxWaitingTime = 20    # seconds

        self.LastVChange = time()
        self.LastUpdate = time()
        self.CanRamp = False  # set in inheriting classes if ramping is available

        self.Logger = self.init_logger(init_logger)
        self.FromLogs = False
        self.StartTime = self.load_start_time(start_time)

        print('---------------------------------------')

    def run(self):
        """Main loop for the thread."""
        while not self.IsKilled:
            sleep(.5 if self.FromLogs else .1)
            if not self.IsManual:
                if not self.FromLogs:
                    self.update_voltage_current()
                    self.write_logs()
                    self.ramp()
                else:
                    self.update()

    def stop(self):
        self.IsKilled = True
        critical('exiting')

    def write_logs(self):
        for channel in self.ActiveChannels:
            self.Logger[channel].write_log(self.get_status(channel), self.get_bias(channel), self.get_current(channel), self.is_ramping(channel), self.get_target_bias(channel), prnt=self.PrintLogs)

    def connect(self):
        warning('"connect" not implemented')

    def hot_start(self):
        if self.HotStart:
            for channel in self.ActiveChannels:
                self.set_status(channel, self.get_output_status(channel))
                self.update_voltage_current()
                voltage = self.get_bias(channel)
                info('Measured voltage: {0:2.1f} V'.format(voltage))
                self.set_bias(voltage, channel)
                self.set_target_bias(voltage, channel)
                self.BiasNow[channel] = voltage

    def update(self):
        data = self.get_last_data()
        for channel in self.ActiveChannels:
            self.BiasNow[channel] = data[channel][1]
            self.CurrentNow[channel] = data[channel][2]
            if data[channel][0]:
                self.LastUpdate = data[channel][0]

    def update_status(self):
        for channel in self.ActiveChannels:
            self.set_status(channel, self.get_output_status(channel))

    # -----------------------------------
    # region INIT
    def init_logger(self, init=True):
        return [Logger(channel, self.Config, on=channel in self.ActiveChannels if init else False) for channel in range(self.NChannels)]

    @staticmethod
    def load_start_time(start_time):
        if start_time == 'now':
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        try:
            t = datetime.strptime(start_time, '%H:%M') if ':' in start_time else datetime.strptime(start_time, '%d.%m.')
            return datetime.now().replace(hour=t.hour, minute=t.minute, second=0, day=t.day, month=t.month, microsecond=0)
        except ValueError:
            critical('Format of date has to be either hh:mm or dd.mm.')

    def read_target_bias(self):
        biases = self.Config.get_channel_values('target bias', float, default=0)
        if not self.validate_voltages(biases):
            critical('End program')
        return biases

    def read_model_number(self):
        if self.Config.get_value('model') is None:
            critical('You have to specify the model in the config file!')
        return self.Config.get_value('model')
    # endregion INIT
    # -----------------------------------
    
    # -----------------------------------
    # region GET
    def get_name(self, channel=0):
        return self.Names[channel]

    def get_current(self, channel=0):
        return self.CurrentNow[channel]

    def get_bias(self, channel=0):
        return self.BiasNow[channel]

    def get_target_bias(self, channel=0):
        return self.TargetBias[channel]

    def get_output_status(self, channel=0):
        warning('get_output_status not implemented')

    def get_output(self):
        return self.get_status()

    def get_status(self, channel=0):
        return self.Status[channel]

    def get_ramp_speed(self, channel=0):
        return self.RampSpeed[channel]

    def get_max_step(self, channel=0):
        return self.MaxStep[channel]

    def get_update_time(self):
        return self.LastUpdate

    def get_data_from_logs(self, channel=0):
        files = sorted(glob(join(self.Logger[channel].LogFileDir, '*')))
        if not files:
            return []
        dates = [datetime.strptime('-'.join(basename(f).strip('.log').split('_')[-6:]), '%Y-%m-%d-%H-%M-%S') for f in files]

        first_file_ind = dates.index(next(d for d in dates if d > self.StartTime)) - 1 if self.StartTime < dates[-1] else -1
        data = []
        for name, d in zip(files[first_file_ind:], dates[first_file_ind:]):
            with open(name) as f:
                for line in f.readlines():
                    info_str = self.make_data(line, d)
                    if info_str[0] and info_str[0] > self.StartTime:
                        data.append(info_str)
        return data

    def get_last_data(self):
        data = {}
        for channel in self.ActiveChannels:
            try:
                filename = self.Logger[channel].get_log_file(prnt=False)
                d = datetime.strptime('-'.join(basename(filename).strip('.log').split('_')[-6:]), '%Y-%m-%d-%H-%M-%S')
                with open(filename, 'rb') as f:
                    f.seek(-50, SEEK_END)
                    info_str = f.readlines()[-1].decode("utf-8")
                    data[channel] = self.make_data(str(info_str), d)
            except IOError:
                data[channel] = [0, 0, 0]
        return data

    def get_id(self):
        return self.Config.get_value('short name', default='')

    def get_idname(self, channel=0):
        return '{}{} - {}'.format(self.get_id(), ', CH{}'.format(channel) if self.NChannels > 1 else '', self.Config.get_dut_names()[channel])

    @staticmethod
    def make_data(string, d):
        data = string.split()
        if isfloat(data[1]):
            t = datetime.strptime(data[0], '%H:%M:%S')
            return [d.replace(hour=t.hour, minute=t.minute, second=t.second), float(data[1]), float(data[2])]
        return [0, 0, 0]
    # endregion GET
    # -----------------------------------

    # -----------------------------------
    # region SET
    def set_name(self, name, channel=0):
        if self.Names != name:
            self.Names = name
            self.Logger.DeviceName = self.Names[channel]
            info('Setting DUT name of {}{} to "{}"'.format(self.Config.Section, ' CH{}'.format(channel) if self.NChannels > 1 else '', self.Names[channel]))

    def set_bias(self, voltage, channel=0):
        warning('set_bias not implemented')

    def set_target_bias(self, target, channel):
        if not self.validate_voltage(target, channel):
            return
        self.TargetBias[channel] = target
        self.LastVChange = time()
        info('Set target bias to {}'.format(target))
        self.Logger[channel].add_entry('SET_BIAS_TO {0:7.1f}'.format(target))

    def set_to_manual(self, status):
        warning('set_to_manual not implemented')

    def set_output(self, status, channel=0):
        warning('set_output not implemented')

    def set_ramp_speed(self, speed, channel=0):
        info('Set ramp speed to {}'.format(speed))
        self.RampSpeed[channel] = speed

    def set_max_step(self, step, channel=0):
        self.MaxStep[channel] = step

    def set_status(self, channel, status):
        self.Status[channel] = status
    # endregion SET
    # -----------------------------------

    # -----------------------------------
    # region MISCELLANEOUS
    def is_ramping(self, channel=0):
        return abs(self.get_bias(channel) - self.get_target_bias(channel)) > .1 if self.get_status(channel) else False

    def all_are_ramping(self):
        return all(self.is_ramping(channel) for channel in self.ActiveChannels)

    def validate_voltage(self, voltage, channel=0):
        if not abs(voltage) < self.MaxBias[channel] + .1:
            warning('Invalid target voltage! {} larger than {}]'.format(voltage, sign(voltage) * self.MaxBias[channel]))
            return False
        return True

    def validate_voltages(self, voltages):
        return all([self.validate_voltage(v, ch) for ch, v in enumerate(voltages)])

    def power_down(self, channel=0):
        self.set_target_bias(0, channel)
        self.IsPoweringDown[channel] = True

    def wait_for_device(self):
        now = time()
        while time() - now < self.MaxWaitingTime and self.IsBusy:
            sleep(.2)

    def read_iv(self):
        warning('read_iv not implemented')
        return []

    def update_voltage_current(self):
        self.wait_for_device()
        self.IsBusy = True
        try:
            self.update_status()
        except Exception as inst:
            warning('Could not update voltage/current- get output status: {} {}'.format(inst, inst.args))
            self.IsBusy = False
            return
        status = any(self.Status)
        if status:
            try:
                iv = self.read_iv()
                self.fill_iv_now(iv)
                self.LastUpdate = time()
            except Exception as inst:
                warning('Could not read valid iv {} {}'.format(type(inst), inst))
        self.IsBusy = False

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
        step_size = copysign(abs(self.RampSpeed[channel] * (time() - self.LastVChange)), delta_v)  # get the voltage step by multiplying speed and update interval
        step_size = self.MaxStep[channel] if abs(step_size) > self.MaxStep[channel] else step_size
        return self.get_target_bias(channel) if abs(delta_v) <= abs(step_size) else self.get_bias(channel) + step_size

    def ramp(self):
        """ Try slowly ramp up the voltage by iteratively increasing the set voltage (if the device has not inherent ramping method) """

        for channel in self.ActiveChannels:
            if self.IsPoweringDown[channel] and abs(self.BiasNow[channel]) < .5:
                self.set_output(OFF, channel)
                self.IsPoweringDown[channel] = False
                info('CH{ch} of {dev} has ramped down and turned off'.format(ch=channel, dev=self.Config.Section))
                return
        if self.CanRamp:
            for channel in self.ActiveChannels:
                self.set_bias(self.get_target_bias(channel), channel)
            return

        for channel in self.ActiveChannels:
            if self.is_ramping(channel):
                self.IsBusy = True
                new_bias = self.calc_ramp_bias(channel)
                self.set_bias(new_bias, channel)
                self.LastVChange = time()
                if new_bias == self.get_target_bias(channel) and not self.IsPoweringDown[channel]:
                    info('{} is done with ramping to {} V'.format(self.Config.Section, self.get_target_bias()))
                self.IsBusy = False
    # endregion MISCELLANEOUS
    # -----------------------------------


if __name__ == '__main__':
    conf = Config('main')
    z = Device(conf.get_active_devices()[0], 'main', False, init_logger=False)
