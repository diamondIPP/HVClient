#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------
#       Device Box Class fot the GUI of the ETH High Voltage Client
# created on June 29th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtCore import Qt
from .live_monitor import times, units
from HVClient.src.device_box import *
from HVClient.src.utils import ON


class HVBox(DeviceBox):

    HEIGHT = 20

    def __init__(self, device=None, channel=None):

        super().__init__(device, channel)
        if device is None:
            return

        # Accessible widgets
        self.BiasField = make_line_edit('0', length=50)
        self.RampField = make_line_edit('{:1.1f}'.format(self.Device.get_ramp_speed()), length=50)
        self.Running = make_check_box()

        # Button
        self.BiasButton = make_button('Set Bias', self.set_bias)
        self.OnButton = make_button('OFF' if self.Device.get_status(self.Channel) else 'ON', self.set_output, size=50, height=DeviceBox.HEIGHT * 2)
        self.RampButton = make_button('Set Ramp Speed', self.set_ramp_speed)

        # Drawing
        self.MaxCurrent = make_spinbox(-1000, 1000, 0, 1)
        self.MinCurrent = make_spinbox(-1000, 1000, 0, 1)
        self.MinVoltage = make_spinbox(-1500, 1500, -1000, 50)
        self.MaxVoltage = make_spinbox(-1500, 1500, 1000, 50)
        self.DisplayTimes = make_combobox(times.keys(), ind=len(times) - 1)
        self.Unit = 'nA'

        # Status labels
        self.StatusLabel = make_label('')
        self.VoltageLabel = make_label('')
        self.CurrentLabel = make_label('')
        self.set_status_labels()

        self.make()

    def update(self):
        if self.Device is None:
            return
        self.set_status_labels()
        self.LiveMonitor.update(self.Unit, int(self.MinCurrent.text()), int(self.MaxCurrent.text()), int(self.MinVoltage.text()), int(self.MaxVoltage.text()),
                                t_displayed=str(self.DisplayTimes.currentText()))
        self.BiasButton.setEnabled(bool(self.Running.isChecked()))
        self.OnButton.setEnabled(bool(self.Running.isChecked()))
        self.RampButton.setEnabled(bool(self.Running.isChecked()))

    def set_bias(self):
        self.Device.set_target_bias(int(self.BiasField.text()), self.Channel)

    def set_output(self):
        self.Device.power_down(self.Channel) if self.Device.get_status(self.Channel) else self.Device.set_output(ON, self.Channel)
        self.OnButton.setText('ON' if self.Device.get_status(self.Channel) else 'OFF')

    def set_ramp_speed(self):
        self.Device.set_ramp_speed(float(self.RampField.text()))

    def set_status_labels(self):
        self.set_status_label()
        self.set_voltage_label()
        self.set_current_label()

    def make_placeholder(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(make_label('', font_size=140), 0, 0)
        self.setLayout(layout)

    def make(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # layout.addWidget(make_label(''), 0, 0)
        layout.addWidget(make_label('Unlock'), 0, 2, Qt.AlignCenter)
        layout.addWidget(self.Running, 0, 2, Qt.AlignRight)

        # status
        stat_labels = [make_label(txt) for txt in ['STATUS', 'VOLTAGE', 'CURRENT']]
        for i, (label, status) in enumerate(zip(stat_labels, [self.StatusLabel, self.VoltageLabel, self.CurrentLabel])):
            layout.addWidget(label, 1, i, Qt.AlignCenter)
            layout.addWidget(status, 2, i, Qt.AlignCenter)

        # spacer
        layout.addWidget(make_label(''), 3, 0)

        # control
        layout.addWidget(self.OnButton, 4, 0, 2, 1, Qt.AlignCenter)
        layout.addWidget(self.BiasButton, 4, 1, Qt.AlignCenter)
        layout.addWidget(self.RampButton, 4, 2, Qt.AlignCenter)
        layout.addWidget(self.BiasField, 5, 1, Qt.AlignCenter)
        layout.addWidget(self.RampField, 5, 2, Qt.AlignCenter)

        for widget in self.children():
            if widget == self.StatusLabel:
                continue
            try:
                format_widget(widget, font='ubuntu', color='grey', font_size=DeviceBox.FONTSIZE, bold=False)
            except AttributeError:  # catch the widgets that can't be formatted by a stylesheet
                pass
            except Exception as err:
                print(err, type(err))
                pass
        for label in stat_labels:
            format_widget(label, bg_col='darkCyan', font='ubuntu', color='black', font_size=DeviceBox.FONTSIZE)
        format_widget(self.OnButton, font='ubuntu', color='black', font_size=DeviceBox.FONTSIZE * 1.05, bold=True)
        self.setLayout(layout)

    def set_status_label(self):
        self.StatusLabel.setText('RAMPING' if self.Device.is_ramping(self.Channel) else 'ON' if self.Device.get_status(self.Channel) else 'OFF')
        color = 'orange' if self.Device.is_ramping(self.Channel) else 'green' if self.Device.get_status(self.Channel) else 'red'
        format_widget(self.StatusLabel, color=color, font_size=DeviceBox.FONTSIZE * 2, bold=True, font='ubuntu')

    def set_voltage_label(self):
        self.VoltageLabel.setText('{v:4.0f} V'.format(v=self.Device.get_bias(self.Channel)) if self.Device.get_status(self.Channel) else '---')
        format_widget(self.VoltageLabel, color='darkCyan', font_size=DeviceBox.FONTSIZE * 2, bold=True, font='ubuntu')

    def set_current_label(self):
        current = self.Device.get_current(self.Channel)
        self.set_current_unit(current)
        self.CurrentLabel.setText(u'{c:3.1f} {u}'.format(c=current / units[self.Unit], u=self.Unit) if self.Device.get_status(self.Channel) else '---')
        format_widget(self.CurrentLabel, color='red', font_size=DeviceBox.FONTSIZE * 2, bold=True, font='ubuntu')

    def set_current_unit(self, current):
        for unit, value in units.items():
            if abs(float(current) / value) < 1000:
                self.Unit = unit
                break

    def create_ramp_button(self):
        button = make_button('Set Ramp Speed')

        def f():
            self.Device.set_ramp_speed(float(self.RampField.text()))

        button.clicked.connect(f)
        return button

    def create_on_button(self):
        button = make_button('OFF' if self.Device.get_status(self.Channel) else 'ON', size=50, height=DeviceBox.HEIGHT * 2)

        def change_output():
            self.Device.power_down(self.Channel) if self.Device.get_status(self.Channel) else self.Device.set_output(ON, self.Channel)
            button.setText('ON' if self.Device.get_status(self.Channel) else 'OFF')

        button.clicked.connect(change_output)
        return button
