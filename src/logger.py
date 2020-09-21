#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------
#       Class to handle the logging for the High Voltage Client
# created on June 3rd, 2018 by Michael Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------


from logging import getLogger, FileHandler, INFO, Formatter
from os.path import join, realpath, dirname, basename
from src.utils import ensure_dir, info, load_config, message
from time import strftime
from glob import glob
from datetime import datetime


class Logger:

    TimeFormat = '%Y_%m_%d_%H_%M_%S'

    def __init__(self, channel, config, on=True):

        self.Dir = dirname(dirname(realpath(__file__)))
        self.Config = config

        self.Name = config.Section
        self.Channel = channel
        self.Logger = getLogger('{}_CH{}'.format(self.Name, channel))
        self.FileHandler = None

        # Config
        self.DeviceName = config.get_value('name')
        self.ModelName = config.get_value('model')
        self.DUTName = self.get_dut_name()

        # Directories
        self.LoggingDir = join(self.Dir, 'data', config.get('Data', 'directory'))
        self.LogFileDir = join(self.LoggingDir, '{}_CH{}'.format(self.DeviceName, self.Channel))

        # Info fields
        self.LastStatus = None
        self.WasRamping = False
        self.Day = strftime('%d')

        if on:
            self.configure()

    def configure(self):
        # check if directories exist and create them if not
        ensure_dir(self.LoggingDir)
        ensure_dir(self.LogFileDir)
        self.Logger.removeHandler(self.FileHandler)
        self.FileHandler = FileHandler(self.get_log_file())
        self.FileHandler.setLevel(INFO)
        self.FileHandler.setFormatter(Formatter('%(asctime)s %(message)s', '%H:%M:%S'))
        self.Logger.addHandler(self.FileHandler)

    def get_dut_name(self):
        return self.Config.get_strings('dut name')[self.Channel]

    def get_log_file(self, prnt=True):
        """Check if there is already an existing log file for this day, otherwise create a new one."""
        last_file = max(glob(join(self.LogFileDir, '*.log')), default='')
        if last_file and datetime.strptime(basename(last_file).split(self.ModelName)[-1].strip('.log_'), self.TimeFormat).day == int(self.Day):
            message('Reading old LOGFILE: {}'.format(last_file), prnt=prnt)
            return last_file
        file_path = join(self.LogFileDir, '{hv}_{dev}_{mod}_{t}.log'.format(hv=self.Name, dev=self.DeviceName, mod=self.ModelName, t=strftime(self.TimeFormat)))
        message('Creating new LOGFILE: {}'.format(file_path), prnt=prnt)
        return file_path

    def create_new_log_file(self):
        self.configure()

    def add_entry(self, txt, prnt=False):
        if prnt:
            info('{}\t{}\tCH{}'.format(txt, self.DeviceName, self.Channel))
        self.Logger.warning('{}\t{}'.format(txt, self.get_dut_name()))

    def write_log(self, status, bias, current, is_ramping, target_bias, prnt=False):
        if strftime('%d') != self.Day:
            self.create_new_log_file()
        if status != self.LastStatus and self.LastStatus is not None:
            info('writing log on/off')
            self.add_entry('DEVICE_{}'.format('ON' if status else 'OFF'), prnt=prnt)
        self.LastStatus = status
        # only write measurements when device is ON
        if not status:
            return
        self.add_entry('{v:10.3e} {c:10.3e}'.format(v=bias, c=current), prnt=prnt)
        # write when ramping starts
        if is_ramping and not self.WasRamping:
            self.add_entry('START_RAMPING_AT {0:7.1f}'.format(bias), prnt=prnt)
            self.add_entry('TARGET_BIAS' + '{0:7.1f}'.format(target_bias), prnt=prnt)
        # write when ramping stops
        if self.WasRamping and not is_ramping:
            self.add_entry('FINISH_RAMPING_AT {0:7.1f}'.format(bias), prnt=prnt)
        self.WasRamping = is_ramping
        self.Day = strftime('%d')


if __name__ == '__main__':
    from json import loads
    conf = load_config('config/keithley', 'cfg')
    dev = 'HV{}'.format(loads(conf.get('Main', 'devices'))[0])
    ch = loads(conf.get(dev, 'active_channels'))[0]
    z = Logger(dev, ch, conf)
