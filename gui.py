#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------
#       GUI for the ETH High Voltage Client
# created on June 29th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from PyQt4.QtGui import QMainWindow, QIcon, QApplication, QAction, QFontDialog, QVBoxLayout, QWidget, QHBoxLayout
from PyQt4.QtCore import QTimer
from sys import exit as end
from ConfigParser import ConfigParser
from DeviceReader import get_devices, get_logging_devices, get_dummies
from os.path import dirname, realpath, join
from DeviceBox import DeviceBox
from DataBox import DataBox
from argparse import ArgumentParser
from serial import SerialException
import qdarkstyle
from warnings import filterwarnings, catch_warnings


ON = True
OFF = False


# todo: add auto setting for max/min current
# todo: add plus/min slider slightly overlapping


class Gui(QMainWindow):
    def __init__(self, devices, from_logs=False):
        super(Gui, self).__init__()

        self.Dir = dirname(realpath(__file__))
        self.FromLogs = from_logs

        # Devices
        self.Devices = devices
        self.start_threads(from_logs)
        self.CurrentDevice = self.Devices[0]
        self.CurrentChannel = 0
        self.NDevices = sum(len(device.ActiveChannels) for device in devices)


        self.MainBox = QHBoxLayout()
        self.configure()
        self.MenuBar = MenuBar(self)

        self.DeviceBoxes = self.make_device_boxes()

        self.timer = QTimer()  #updates the plot
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

        self.show()

    def closeEvent(self, QCloseEvent):
        self.MenuBar.close_app()

    def update(self):
        for device_box in self.DeviceBoxes:
            try:
                device_box.update()
            except (ValueError, SerialException) as err:
                print err

    def configure(self):
        self.setGeometry(2000, 300, (800 if self.FromLogs else 400) * ((self.NDevices + 1) / 2), 400)
        self.setWindowTitle('ETH High Voltage Client')
        self.setWindowIcon(QIcon(join(self.Dir, 'Pics', 'icon.svg')))
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(self.MainBox)

    def start_threads(self, from_logs):
        for device in self.Devices:
            device.FromLogs = from_logs
            device.start()

    def make_device_boxes(self):
        boxes = []
        vboxes = [QVBoxLayout() for _ in xrange((self.NDevices + 1) / 2)]
        i = 0
        for device in self.Devices:
            for channel in device.ActiveChannels:
                box = DeviceBox(device, channel) if not self.FromLogs else DataBox(device, channel)
                vboxes[i / 2].addWidget(box)
                boxes.append(box)
                i += 1
        if self.NDevices % 2 == 1:
            box = DeviceBox() if not self.FromLogs else DataBox()
            vboxes[-1].addWidget(box)
            boxes.append(box)
        for box in vboxes:
            self.MainBox.addLayout(box)
        return boxes


class MenuBar(object):
    def __init__(self, gui):
        self.Window = gui
        self.Menus = {}
        self.load()

    def load(self):
        self.add_menu('File')
        self.add_menu_entry('File', 'Exit', 'Ctrl+Q', self.close_app, 'Close the Application')
        self.add_menu_entry('File', 'Font', 'Ctrl+F', self.font_choice, 'Open font dialog')

    def add_menu(self, name):
        self.Window.statusBar()
        main_menu = self.Window.menuBar()
        self.Menus[name] = main_menu.addMenu('&{n}'.format(n=name))

    def add_menu_entry(self, menu, name, shortcut, func, tip=''):
        action = QAction('&{n}'.format(n=name), self.Window)
        action.setShortcut(shortcut)
        action.setStatusTip(tip)
        action.triggered.connect(func)
        self.Menus[menu].addAction(action)

    def font_choice(self):
        font, valid = QFontDialog.getFont()
        if valid:
            self.Window.CheckBoxes.B['Short'].setFont(font)

    def close_app(self):
        print 'Closing application'
        for dev in self.Window.Devices:
            dev.IsKilled = True
        end(2)


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('--config', '-c', help='Config file', default='keithley.cfg')
    parser.add_argument('--restart', '-R', action='store_true', help='restart hv devices (turn all OFF and set voltage to 0)')
    parser.add_argument('--start_time', '-s', nargs='?', help='set start time', default='now')
    parser.add_argument('--from_logs', '-l', action='store_true', help='read data from logs')
    args = parser.parse_args()

    config = ConfigParser()
    config.read(join(dirname(realpath(__file__)), 'config', args.config))

    start_time = None if args.start_time == 'now' else args.start_time

    devices = get_devices(config, not args.restart, print_logs=True) if not args.from_logs else get_logging_devices(config, start_time)
    # devices = get_dummies(config)

    app = QApplication(['5'])
    filterwarnings('ignore')
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyside())
    g = Gui(devices, args.from_logs)
    end(app.exec_())
