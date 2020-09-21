#!/usr/bin/env python
# --------------------------------------------------------
#       Device Box Class fot the GUI of the ETH High Voltage Client
# created on June 29th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtCore import Qt
from .live_monitor import LiveMonitor, times, units
from src.device_box import *


class DisplayBox(DeviceBox):

    def __init__(self, device=None, channel=None):

        super().__init__(device, channel)
        if device is None:
            return

        # Drawing
        self.MaxCurrent = make_spinbox(-10000, 10000, 0, 1)
        self.MinCurrent = make_spinbox(-10000, 10000, 0, 1)
        self.MinVoltage = make_spinbox(-1500, 1500, -1000, 50)
        self.MaxVoltage = make_spinbox(-1500, 1500, 1000, 50)
        self.DisplayTimes = make_combobox(times.keys(), ind=len(times) - 1)
        self.Units = make_combobox(units.keys(), ind=1)
        self.Labels = self.make_labels()
        self.Widgets = [self.MaxCurrent, self.MinCurrent, self.MinVoltage, self.MaxVoltage, self.DisplayTimes, self.Units]

        self.LiveMonitor.init(self.Device.get_data_from_logs(self.Channel))
        self.make()

    def update(self):
        if self.Device is None:
            return
        if self.Device.LastUpdate:
            self.LiveMonitor.add_data(self.Device.LastUpdate, self.Device.BiasNow[self.Channel], self.Device.CurrentNow[self.Channel], dttime=True)
            self.LiveMonitor.update(self.Units.currentText(), int(self.MinCurrent.text()), int(self.MaxCurrent.text()), int(self.MinVoltage.text()), int(self.MaxVoltage.text()),
                                    t_displayed=str(self.DisplayTimes.currentText()))

    @staticmethod
    def make_labels():
        return [QLabel(n) for n in ['Displayed Time', 'Current Limits', 'Voltage Limits', 'Current Unit']]

    def make_placeholder(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        dummy = LiveMonitor(dummy=True)
        layout.addWidget(dummy.canvas, 0, 3, 12, 1)
        self.setLayout(layout)

    def make(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # drawing
        for i, label in enumerate(self.Labels, 1):
            layout.addWidget(label, i, 0, Qt.AlignRight)
        layout.addWidget(self.DisplayTimes, 1, 1, Qt.AlignLeft)
        layout.addWidget(self.MinCurrent, 2, 1, Qt.AlignLeft)
        layout.addWidget(self.MaxCurrent, 2, 2, Qt.AlignLeft)
        layout.addWidget(self.MinVoltage, 3, 1, Qt.AlignLeft)
        layout.addWidget(self.MaxVoltage, 3, 2, Qt.AlignLeft)
        layout.addWidget(self.Units, 4, 1, Qt.AlignLeft)
        layout.addWidget(self.LiveMonitor.canvas, 0, 3, 6, 1)
        layout.setColumnStretch(3, 50)
        for widget in self.children():
            try:
                widget.setFont(QFont('Ubuntu', 5))
                format_widget(widget, color='darkCyan')
            except AttributeError:  # catch the widgets that can't be formatted by a stylesheet
                pass
            except Exception as err:
                print(err, type(err))
                pass
        self.setLayout(layout)
