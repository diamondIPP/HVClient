#!/usr/bin/env python
# --------------------------------------------------------
#       GUI for the ETH High Voltage Client
# created on June 29th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from PyQt4.QtGui import QMainWindow, QIcon, QApplication, QStyleFactory, QAction, QFontDialog, QGroupBox, QGridLayout, QLabel, QLineEdit, QTextEdit, QCheckBox, QVBoxLayout, \
    QPushButton, QFont
from PyQt4.QtCore import SIGNAL, Qt
from sys import exit as end
from ConfigParser import ConfigParser
from DeviceReader import get_devices
from functools import partial

ON = True
OFF = False


class Gui(QMainWindow):
    def __init__(self, devices):
        super(Gui, self).__init__()

        self.Devices = devices
        devices.values()[0].start()
        self.NDevices = len(devices)
        self.configure()
        self.MenuBar = MenuBar(self)
        self.IsUpdating = True

        self.make_device_box(devices.keys()[0], devices.values()[0], 'CH0')

        self.show()

    def configure(self):
        self.setGeometry(500, 300, 1000, 100 + self.NDevices * 300)
        self.setWindowTitle('ETH High Voltage Client')
        self.setWindowIcon(QIcon('Pics/icon.svg'))
        QApplication.setStyle(QStyleFactory.create('Plastique'))

    def make_device_box(self, name, device, channel):
        box = QGroupBox(device.read_device_name(), self)
        f = QFont()
        f.setBold(True)
        f.setPointSize(20)
        box.setFont(f)
        layout = QGridLayout(box)
        layout.setContentsMargins(4, 4, 4, 4)

        bias_field = make_line_edit('0')
        bias_button = create_bias_button(bias_field, device, channel)

        layout.addWidget(create_on_button(device, channel), 1, 0, 1, 2, Qt.AlignCenter)
        layout.addWidget(bias_field, 2, 1)
        layout.addWidget(bias_button, 2, 0)
        layout.addWidget(QLabel('Displayed Hours'), 3, 0)
        layout.addWidget(QLabel('Max Current'), 4, 0)
        layout.addWidget(QLabel('Min Current'), 5, 0)
        layout.addWidget(QLabel('Current Unit'), 6, 0)
        layout.addWidget(self.create_break_button(), 7, 0, 1, 2, Qt.AlignCenter)
        smallEditor = QTextEdit()
        smallEditor.setPlainText('Here should be a plot ...')
        layout.addWidget(smallEditor, 0, 2, 8, 1)
        layout.setColumnStretch(1, 10)
        layout.setColumnStretch(2, 50)
        for widget in box.children():
            try:
                widget.setFont(QFont('arial', 15))
            except:
                pass
        box.setLayout(layout)
        self.setCentralWidget(box)

    def create_break_button(self):
        button = make_button('Break Update')

        def f():
            button.setText('{} Update'.format('Continue' if self.IsUpdating else 'Break'))
            self.IsUpdating = not self.IsUpdating

        button.clicked.connect(f)
        return button


def create_bias_button(obj, device, channel):
    button = make_button('Set Bias')

    def f():
        device.set_target_bias(int(obj.text()), channel)

    button.clicked.connect(f)
    return button


def create_on_button(device, channel):
    button = make_button('OFF' if device.get_status(channel) else 'ON')

    def change_output():
        device.power_down(channel) if device.get_status(channel) else device.interface.set_output('ON', channel)
        button.setText('ON' if device.get_status(channel) else 'OFF')

    button.clicked.connect(change_output)
    return button


def make_line_edit(txt=''):
    line_edit = QLineEdit()
    line_edit.setText('0')
    return line_edit


def make_button(txt, size=200):
    but = QPushButton()
    but.setText(txt)
    but.setFixedWidth(size)
    return but


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
        for dev in self.Window.Devices.itervalues():
            dev.isKilled = True
        end(2)


if __name__ == '__main__':
    config = ConfigParser()
    config.read('config/keithley.cfg')
    devices = get_devices(config, True)

    app = QApplication([5])
    g = Gui(devices)
    end(app.exec_())
