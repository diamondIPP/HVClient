#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------
#       Device Box Class fot the GUI of the ETH High Voltage Client
# created on June 29th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from PyQt4.QtGui import QGroupBox, QGridLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QComboBox, QCheckBox
from PyQt4.QtCore import Qt
from Utils import do, convert_unicode
from LiveMonitor import LiveMonitor, times, units

ON = True
OFF = False
HEIGHT = 20


class DeviceBox(QGroupBox):

    def __init__(self, device, channel):

        super(DeviceBox, self).__init__()
        self.setTitle('CH{c} - {n}'.format(n=device.read_device_name(channel), c=channel))

        self.Device = device
        self.Channel = channel

        format_widget(self, color='red', bold=True, font_size=22)

        # Accessible widgets
        self.BiasField = make_line_edit('0', length=50)
        self.RampField = make_line_edit('{:1.1f}'.format(self.Device.get_ramp_speed()), length=50)
        self.Running = make_check_box()

        # Button
        self.BiasButton = self.create_bias_button()
        self.OnButton = self.create_on_button()

        # Drawing
        self.MaxCurrent = make_spinbox(-1000, 1000, 0, 1)
        self.MinCurrent = make_spinbox(-1000, 1000, 0, 1)
        self.MinVoltage = make_spinbox(-1500, 1500, -1000, 50)
        self.MaxVoltage = make_spinbox(-1500, 1500, 1000, 50)
        self.DisplayTimes = make_combobox(times.keys(), ind=len(times) - 1)
        self.Units = make_combobox(units.keys(), ind=1)

        # Status labels
        self.StatusLabel = make_label('')
        self.VoltageLabel = make_label('')
        self.CurrentLabel = make_label('')
        self.set_status_labels()

        # Canvas
        self.LiveMonitor = LiveMonitor()
        self.make()

    def update(self):
        self.set_status_labels()
        self.LiveMonitor.update(convert_unicode(self.Units.currentText()), int(self.MinCurrent.text()), int(self.MaxCurrent.text()), int(self.MinVoltage.text()), int(self.MaxVoltage.text()),
                                t_displayed=str(self.DisplayTimes.currentText()))
        self.BiasButton.setEnabled(bool(self.Running.isChecked()))
        self.OnButton.setEnabled(bool(self.Running.isChecked()))

    def set_status_labels(self):
        self.set_status_label()
        self.set_voltage_label()
        self.set_current_label()

    def make(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        layout.addWidget(self.OnButton, 2, 0, 1, 2, Qt.AlignCenter)
        layout.addWidget(self.Running, 2, 2, Qt.AlignCenter)

        # status
        layout.addWidget(QLabel('STATUS'), 3, 0, Qt.AlignRight)
        layout.addWidget(self.StatusLabel, 3, 1, 1, 2, Qt.AlignCenter)
        layout.addWidget(QLabel('VOLTAGE'), 4, 0, Qt.AlignRight)
        layout.addWidget(self.VoltageLabel, 4, 1, 1, 2, Qt.AlignCenter)
        layout.addWidget(QLabel('CURRENT'), 5, 0, Qt.AlignRight)
        layout.addWidget(self.CurrentLabel, 5, 1, 1, 2, Qt.AlignCenter)

        # control
        layout.addWidget(self.BiasField, 6, 1, Qt.AlignLeft)
        layout.addWidget(self.BiasButton, 6, 0)
        layout.addWidget(self.RampField, 7, 1, Qt.AlignLeft)
        layout.addWidget(self.create_ramp_button(), 7, 0)

        for widget in self.children():
            if widget == self.StatusLabel:
                continue
            try:
                format_widget(widget, font='ubuntu', color='black', font_size=10, bold=False)
            except AttributeError:  # catch the widgets that can't be formatted by a stylesheet
                pass
            except Exception as err:
                print err, type(err)
                pass
        self.setLayout(layout)

    def set_status_label(self):
        self.StatusLabel.setText('RAMPING' if self.Device.is_ramping(self.Channel) else 'ON' if self.Device.get_status(self.Channel) else 'OFF')
        color = 'orange' if self.Device.is_ramping(self.Channel) else 'green' if self.Device.get_status(self.Channel) else 'red'
        format_widget(self.StatusLabel, color=color, font_size=20, bold=True, font='ubuntu')

    def set_voltage_label(self):
        self.VoltageLabel.setText('{v:4.1f} V'.format(v=self.Device.get_bias(self.Channel)) if self.Device.get_status(self.Channel) else '---')
        format_widget(self.VoltageLabel, color='blue', font_size=20, bold=True, font='ubuntu')

    def set_current_label(self):
        unit = convert_unicode(self.Units.currentText())
        self.CurrentLabel.setText(u'{v:3.2f} {u}'.format(v=self.Device.get_current(self.Channel) / units[unit], u=unit) if self.Device.get_status(self.Channel) else '---')
        format_widget(self.CurrentLabel, color='red', font_size=20, bold=True, font='ubuntu')

    def create_ramp_button(self):
        button = make_button('Set Ramp Speed')

        def f():
            self.Device.set_ramp_speed(float(self.RampField.text()))

        button.clicked.connect(f)
        return button

    def create_bias_button(self):
        button = make_button('Set Bias')

        def f():
            self.Device.set_target_bias(int(self.BiasField.text()), self.Channel)

        button.clicked.connect(f)
        return button

    def create_on_button(self):
        button = make_button('OFF' if self.Device.get_status(self.Channel) else 'ON')

        def change_output():
            self.Device.power_down(self.Channel) if self.Device.get_status(self.Channel) else self.Device.set_output(ON, self.Channel)
            button.setText('ON' if self.Device.get_status(self.Channel) else 'OFF')

        button.clicked.connect(change_output)
        return button


def make_combobox(lst, ind=0):
    combo_box = QComboBox()
    combo_box.addItems(lst)
    combo_box.setCurrentIndex(ind)
    return combo_box


def make_spinbox(low, high, value, step=1):
    spin_box = QSpinBox()
    spin_box.setRange(low, high)
    spin_box.setValue(value)
    spin_box.setSingleStep(step)
    return spin_box


def make_line_edit(txt='', length=None):
    line_edit = QLineEdit()
    line_edit.setText(txt)
    do(line_edit.setMaximumWidth, length)
    return line_edit


def make_button(txt, size=None, height=HEIGHT):
    but = QPushButton()
    but.setText(txt)
    do(but.setFixedWidth, size)
    do(but.setMaximumHeight, height)
    return but


def make_check_box(value=False):
    check_box = QCheckBox()
    check_box.setChecked(value)
    return check_box


def make_label(txt, color=None, bold=False, font=None, font_size=None):
    label = QLabel(txt)
    format_widget(label, color, bold, font_size, font)
    return label


def format_widget(widget, color=None, bold=None, font_size=None, font=None):
    dic = {'color': color, 'font-weight': 'bold' if bold else None, 'font-size': '{}px'.format(font_size) if font_size is not None else None, 'font-family': font}
    widget.setStyleSheet(make_style_sheet(dic))


def make_style_sheet(dic):
    return '; '.join('{key}: {val}'.format(key=key, val=value) for key, value in dic.iteritems() if value is not None)
