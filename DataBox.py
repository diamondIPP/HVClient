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

HEIGHT = 20


class DataBox(QGroupBox):

    def __init__(self, device, channel):

        super(DataBox, self).__init__()
        self.setTitle('CH{c} - {n}'.format(n=device.read_device_name(channel), c=channel))

        self.Device = device
        self.Channel = channel

        format_widget(self, color='red', bold=True, font_size=22)

        # Drawing
        self.MaxCurrent = make_spinbox(-10000, 10000, 0, 1)
        self.MinCurrent = make_spinbox(-10000, 10000, 0, 1)
        self.MinVoltage = make_spinbox(-1500, 1500, -1000, 50)
        self.MaxVoltage = make_spinbox(-1500, 1500, 1000, 50)
        self.DisplayTimes = make_combobox(times.keys(), ind=len(times) - 1)
        self.Units = make_combobox(units.keys(), ind=1)

        # Canvas
        self.LiveMonitor = LiveMonitor()
        self.LiveMonitor.init(self.Device.get_data_from_logs(self.Channel))
        self.make()

    def update(self):
        self.LiveMonitor.add_data(self.Device.LastUpdate, self.Device.BiasNow[self.Channel], self.Device.CurrentNow[self.Channel], dttime=True)
        self.LiveMonitor.update(convert_unicode(self.Units.currentText()), int(self.MinCurrent.text()), int(self.MaxCurrent.text()), int(self.MinVoltage.text()), int(self.MaxVoltage.text()),
                                t_displayed=str(self.DisplayTimes.currentText()))

    def make(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # drawing
        layout.addWidget(QLabel('Displayed Time'), 8, 0, Qt.AlignRight)
        layout.addWidget(self.DisplayTimes, 8, 1, Qt.AlignLeft)
        layout.addWidget(QLabel('Current Limits'), 9, 0, Qt.AlignRight)
        layout.addWidget(self.MinCurrent, 9, 1, Qt.AlignLeft)
        layout.addWidget(self.MaxCurrent, 9, 2, Qt.AlignLeft)
        layout.addWidget(QLabel('Voltage Limits'), 10, 0, Qt.AlignRight)
        layout.addWidget(self.MinVoltage, 10, 1, Qt.AlignLeft)
        layout.addWidget(self.MaxVoltage, 10, 2, Qt.AlignLeft)
        layout.addWidget(QLabel('Current Unit'), 11, 0, Qt.AlignRight)
        layout.addWidget(self.Units, 11, 1, Qt.AlignLeft)
        layout.addWidget(self.LiveMonitor.canvas, 0, 3, 12, 1)
        layout.setColumnStretch(3, 50)
        for widget in self.children():
            try:
                format_widget(widget, font='ubuntu', color='black', font_size=10, bold=False)
            except AttributeError:  # catch the widgets that can't be formatted by a stylesheet
                pass
            except Exception as err:
                print err, type(err)
                pass
        self.setLayout(layout)


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
