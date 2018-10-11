#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------
#       Class to handle the logging for the High Voltage Client
# created on June 3rd, 2018 by Michael Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------


from logging import getLogger, FileHandler, INFO, Formatter
from os.path import join, realpath, dirname
from Utils import ensure_dir, log_info
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
        
        # Info fields
        self.LastStatus = None
        self.WasRamping = False
        self.Day = strftime('%d')

        if on:
            self.configure()

    def configure(self):
        logging_dir = join(self.Dir, self.Config.get('Main', 'testbeam_name'))
        log_file_dir = join(logging_dir, '{}_CH{}'.format(self.DeviceName, self.Channel))
        # check if directories exist and create them if not
        ensure_dir(logging_dir)
        ensure_dir(log_file_dir)

        file_name = '{hv}_{dev}_{mod}_{t}.log'.format(hv=self.Name, dev=self.DeviceName, mod=self.ModelName, t=strftime('%Y_%m_%d_%H_%M_%S'))
        file_path = join(log_file_dir, file_name)
        log_info('Creating LOGFILE: {}'.format(file_path))
        self.Logger.removeHandler(self.FileHandler)
        self.FileHandler = FileHandler(file_path)
        self.FileHandler.setLevel(INFO)
        self.FileHandler.setFormatter(Formatter('%(asctime)s %(message)s', '%H:%M:%S'))
        self.Logger.addHandler(self.FileHandler)

    def create_new_log_file(self):
        self.configure()

    def add_entry(self, txt, prnt=False):
        if prnt:
            log_info('{}\t{}\tCH{}'.format(txt, self.DeviceName, self.Channel))
        self.Logger.warning('{}\t{}'.format(txt, self.DeviceName))

    def write_log(self, status, bias, current, is_ramping, target_bias, prnt=False):
        if strftime('%d') != self.Day:
            self.create_new_log_file()
        if status != self.LastStatus and self.LastStatus is not None:
            log_info('writing log on/off')
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
    l = Logger('HV1', 0, conf)