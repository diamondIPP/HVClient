#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------
#       GUI for the ETH High Voltage Client
# created on June 29th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from PyQt4.QtGui import QMainWindow, QIcon, QApplication, QAction, QFontDialog, QVBoxLayout, QWidget
from PyQt4.QtCore import QTimer
from sys import exit as end
from ConfigParser import ConfigParser
from DeviceReader import get_devices
from devices.Keithley24XX import Keithley24XX
from devices.ISEG import ISEG
from os.path import dirname, realpath, join
from DeviceBox import DeviceBox


ON = True
OFF = False


# todo: add auto setting for max/min current
# todo: add plus/min slider slightly overlapping


class Gui(QMainWindow):
    def __init__(self, devices):
        super(Gui, self).__init__()

        self.Dir = dirname(realpath(__file__))

        # Devices
        self.Devices = devices
        self.start_threads()
        self.CurrentDevice = self.Devices[0]
        self.CurrentChannel = 0
        self.NDevices = sum(len(device.ActiveChannels) for device in devices)

        self.MainBox = QVBoxLayout()
        self.configure()
        self.MenuBar = MenuBar(self)

        self.DeviceBoxes = self.make_device_boxes()

        self.timer = QTimer()  #updates the plot
        self.timer.timeout.connect(self.update)
        self.timer.start(500)

        self.show()

    def closeEvent(self, QCloseEvent):
        self.MenuBar.close_app()

    def update(self):
        for device_box in self.DeviceBoxes:
            device_box.update()

    def configure(self):
        self.setGeometry(2000, 300, 1000, 100 + self.NDevices * 300)
        self.setWindowTitle('ETH High Voltage Client')
        self.setWindowIcon(QIcon(join(self.Dir, 'Pics', 'icon.svg')))
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(self.MainBox)

    def start_threads(self):
        for device in self.Devices:
            device.start()

    def make_device_boxes(self):
        boxes = []
        for device in self.Devices:
            for channel in device.ActiveChannels:
                boxes.append(DeviceBox(device, channel))
                self.MainBox.addWidget(boxes[-1])
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

    config = ConfigParser()
    config.read(join(dirname(realpath(__file__)), 'config', 'keithley.cfg'))

    # devices = get_devices(config, False)
    devices = [ISEG(config, 2, True)]
    print(devices[0].ActiveChannels)
    # devices = [Keithley24XX(config, 1, True)]
    app = QApplication([5])
    app.setStyle('Macintosh')
    g = Gui(devices)
    end(app.exec_())
