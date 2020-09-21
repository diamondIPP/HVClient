#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------
#       GUI for the ETH High Voltage Client
# created on June 29th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from argparse import ArgumentParser
from os.path import join
from sys import exit as end
from warnings import filterwarnings
from numpy import ceil, where

import qdarkstyle
from PyQt5.QtCore import QTimer, QPoint, Qt
from PyQt5.QtGui import QIcon, QFont, QCursor
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, QFontDialog, QVBoxLayout, QWidget, QHBoxLayout, QInputDialog, QLabel, QDialog, QGridLayout
from serial import SerialException

from src.display_box import DisplayBox
from src.hv_box import HVBox
from src.device_reader import get_devices, get_logging_devices, get_dummies
from src.utils import *
from src.live_monitor import LiveMonitor
from src.config import Config

from src.device_box import make_line_edit, make_button, make_check_box


# todo: add auto setting for max/min current
# todo: add plus/min slider slightly overlapping


class Gui(QMainWindow):

    BUTTON_HEIGHT = 50

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
        self.MenuBar = MenuBar(self, from_logs)

        self.DeviceBoxes = self.make_device_boxes()

        self.timer = QTimer()  # updates the plot
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
                print(err)

    def configure(self):
        h = min(self.NDevices, 3) * 250 + 50
        w = (800 if self.FromLogs else 350) * ceil(self.NDevices / 3)
        self.setGeometry(2000, 300, w, h)
        self.setWindowTitle('ETH High Voltage Client')
        self.setWindowIcon(QIcon(join(dirname(self.Dir), 'figures', '{}.svg'.format('display' if self.FromLogs else 'hv'))))
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(self.MainBox)

    def start_threads(self, from_logs):
        for device in self.Devices:
            device.FromLogs = from_logs
            device.start()

    def make_device_boxes(self):
        boxes = []
        vboxes = [QVBoxLayout() for _ in range(ceil(self.NDevices / 3).astype('u2'))]
        i = 0
        for device in self.Devices:
            for channel in device.ActiveChannels:
                box = HVBox(device, channel) if not self.FromLogs else DisplayBox(device, channel)
                vboxes[i // 3].addWidget(box)
                boxes.append(box)
                i += 1
        while i % 3 != 0 and i > 3:
            box = HVBox() if not self.FromLogs else DisplayBox()
            vboxes[-1].addWidget(box)
            boxes.append(box)
            i += 1
        for box in vboxes:
            self.MainBox.addLayout(box)
        return boxes

    def reset_titles(self):
        for box in self.DeviceBoxes:
            if box.Device is not None:
                box.set_title()

    @staticmethod
    def query_devices(config):
        config = Config(config)
        labels = ['{} - {}'.format(key, value) for key, value in config.get_sections().items()]
        values = query_list('Choose Active Devices', labels, [i in config.get_active_devices() for i in range(len(labels))], checks=True)
        if values is not None:
            config.set_active_devices(str(list(where(array(values))[0])))

    @staticmethod
    def query_channels(config):
        config = Config(config)
        sections = ['HV{}'.format(i) for i in config.get_active_devices() if config.get_value('number of channels', int, 'HV{}'.format(i), 1) > 1]
        if not len(sections):
            return
        values = query_list('Channel Numbers', sections, [config.get_active_channels(sec) for sec in sections])
        if values is not None:
            for section, value in zip(sections, values):
                config.set_active_channels(section, value)

    def set_device_names(self):
        labels = ['{} - {}'.format(key, value) for key, value in self.Devices[0].Config.get_sections(active=True).items()]
        values = query_list('Device Names', labels, [dev.get_id() for dev in self.Devices])
        if values is not None:
            for dev, value in zip(self.Devices, values):
                dev.Config.set_id(value)
            self.reset_titles()

    def set_dut_names(self):
        names = ['{} - CH{}'.format(dev.get_id(), ch) for dev in self.Devices for ch in dev.ActiveChannels]
        values = query_list('DUT Names', names, [name for dev in self.Devices for name in dev.Config.get_dut_names(active=True)])
        if values is not None:
            i = 0
            for dev in self.Devices:
                for ch in dev.ActiveChannels:
                    dev.Config.set_dut_name(values[i], ch)
                    i += 1
            self.reset_titles()


def query(title, label, init_value='', pos: QPoint = None):
    q = QInputDialog()
    q.setWindowTitle(title)
    q.setLabelText(label)
    q.setTextValue(str(init_value))
    q.move(choose(pos, QCursor.pos()))
    if q.exec() == QDialog.Accepted:
        return q.textValue()


def query_list(title, label_names, init_values=None, pos: QPoint = None, checks=False):
    q = QDialog()

    def done():
        q.done(QDialog.Accepted)
    q.setWindowTitle(title)
    layout = QGridLayout()
    layout.setContentsMargins(4, 4, 4, 4)
    widgets = []
    for i, (name, init_value) in enumerate(zip(label_names, choose(init_values, [''] * len(label_names)))):
        layout.addWidget(QLabel(name), i, 0, Qt.AlignRight)
        widgets.append(make_line_edit(str(init_value)) if not checks else make_check_box(bool(init_value), size=40))
        layout.addWidget(widgets[i], i, 1, Qt.AlignLeft)
    layout.addWidget(make_button('Done', done), len(label_names) + 1, 1)
    q.setLayout(layout)
    q.move(choose(pos, QCursor.pos()))
    if q.exec() == QDialog.Accepted:
        return [widget.isChecked() if checks else widget.text() for widget in widgets]


class MenuBar(object):
    def __init__(self, gui, display=False):
        self.Window = gui
        self.Menus = {}
        self.Display = display
        self.load()

    def load(self):
        self.add_menu('File')
        self.add_menu_entry('File', 'Exit', 'Ctrl+Q', self.close_app, 'Close the Application')
        self.add_menu_entry('File', 'Font', 'Ctrl+F', self.font_choice, 'Open font dialog')
        if self.Display:
            self.add_menu('Settings')
            self.add_menu_entry('Settings', 'Marker Size', 'Ctrl+M', self.set_ms, 'Open marker size dialog')
            self.add_menu_entry('Settings', 'Line Width', 'Ctrl+L', self.set_lw, 'Open line width dialog')
        self.add_menu('Config')
        self.add_menu_entry('Config', 'Set Device Names', 'Ctrl+N', self.Window.set_device_names, 'Change the names of the HV devices')
        self.add_menu_entry('Config', 'Set DUT Names', 'Ctrl+D', self.Window.set_dut_names, 'Change the names of DUTs')

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
        font, valid = QFontDialog.getFont(self.Window)
        if valid:
            for box in self.Window.DeviceBoxes:
                header_font = QFont(font)
                header_font.setPointSize(font.pointSize() * 1.4)
                box.setFont(header_font)
                box.set_fonts(font)
            LiveMonitor.FD = {'family': font.family(), 'size': font.pointSize() * 1.4}

    def close_app(self):
        info('Closing application')
        for dev in self.Window.Devices:
            dev.IsKilled = True
        end(2)

    def set_ms(self):
        value, valid = QInputDialog.getInt(self.Window, 'Marker Size', 'Marker Size:')
        if valid:
            LiveMonitor.MS = value

    def set_lw(self):
        value, valid = QInputDialog.getInt(self.Window, 'Line Width', 'Line Width:')
        if valid:
            LiveMonitor.LW = value


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('--config', '-c', help='Config file', default='keithley.cfg')
    parser.add_argument('--restart', '-R', action='store_true', help='restart hv devices (turn all OFF and set voltage to 0)')
    parser.add_argument('--start_time', '-s', nargs='?', help='set start time', default='now')
    parser.add_argument('--from_logs', '-l', action='store_true', help='read data from logs')
    parser.add_argument('--test', '-t', action='store_true', help='start test environment')
    args = parser.parse_args()

    if args.test:
        device_list = get_dummies(args.config)
    else:
        device_list = get_devices(args.config, not args.restart, print_logs=True) if not args.from_logs else get_logging_devices(args.config, args.start_time)

    app = QApplication(['5'])
    filterwarnings('ignore')
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    g = Gui(device_list, args.from_logs)
    end(app.exec_())
