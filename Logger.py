#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------
#       Class to handle the logging for the High Voltage Client
# created on June 3rd, 2018 by Michael Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------


from logging import getLogger, FileHandler, INFO, Formatter
from os.path import join, realpath, dirname
from utils import ensure_dir, info
from ConfigParser import ConfigParser
from time import strftime


class Logger:

    def __init__(self, name, channel, config, on=True):

        self.Dir = dirname(realpath(__file__))

        self.Name = name
        self.Channel = channel
        self.Logger = getLogger('{}_CH{}'.format(name, channel))
        self.FileHandler = None

        # Config
        self.Config = config
        self.DeviceName = self.Config.get(self.Name, 'name')
        self.ModelName = self.Config.get(self.Name, 'model')

        # Directories
        self.LoggingDir = join(self.Dir, self.Config.get('Main', 'testbeam_name'))
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

        file_name = '{hv}_{dev}_{mod}_{t}.log'.format(hv=self.Name, dev=self.DeviceName, mod=self.ModelName, t=strftime('%Y_%m_%d_%H_%M_%S'))
        file_path = join(self.LogFileDir, file_name)
        info('Creating LOGFILE: {}'.format(file_path))
        self.Logger.removeHandler(self.FileHandler)
        self.FileHandler = FileHandler(file_path)
        self.FileHandler.setLevel(INFO)
        self.FileHandler.setFormatter(Formatter('%(asctime)s %(message)s', '%H:%M:%S'))
        self.Logger.addHandler(self.FileHandler)

    def create_new_log_file(self):
        self.configure()

    def add_entry(self, txt, prnt=False):
        if prnt:
            info('{}\t{}\tCH{}'.format(txt, self.DeviceName, self.Channel))
        self.Logger.warning('{}\t{}'.format(txt, self.DeviceName))

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
    conf = ConfigParser()
    conf.read('config/keithley.cfg')
    logger = Logger('HV1', 0, conf)
