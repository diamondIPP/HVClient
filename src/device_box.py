#!/usr/bin/env python
# --------------------------------------------------------
#       Data box parent class fot the GUI of the ETH High Voltage Client
# created on June 29th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QGroupBox, QLabel, QLineEdit, QPushButton, QSpinBox, QComboBox, QCheckBox, QPlainTextEdit
from .utils import do, do_nothing
from src.live_monitor import LiveMonitor


class DeviceBox(QGroupBox):
    HEIGHT = 40
    FONTSIZE = 13

    def __init__(self, device=None, channel=None):

        super(DeviceBox, self).__init__()

        self.Device = device
        self.Channel = channel
        self.Widgets, self.Labels = [], []
        if self.Device is None:
            self.make_placeholder()
            return

        # Canvas
        self.LiveMonitor = LiveMonitor()
        self.set_title()

    def set_title(self):
        self.setTitle(self.Device.get_idname(self.Channel))
        self.setFont(QFont('Ubuntu', 8, QFont.Bold))
        format_widget(self, color='red')

    def set_fonts(self, font):
        for widget in self.Widgets:
            widget.setFont(font)
        for label in self.Labels:
            label.setFont(font)

    def make_placeholder(self):
        pass

    def make(self):
        pass


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


def make_text_edit(txt='', length=None, min_height=None):
    text_edit = QPlainTextEdit()
    text_edit.setPlainText(txt)
    do(text_edit.setMaximumWidth, length)
    do(text_edit.setMinimumHeight, min_height)
    return text_edit


def make_button(txt, f=do_nothing, size=None, height=DeviceBox.HEIGHT):
    but = QPushButton()
    but.setText(txt)
    do(but.setFixedWidth, size)
    do(but.setMaximumHeight, height)
    but.clicked.connect(f)
    return but


def make_check_box(value=False):
    check_box = QCheckBox()
    check_box.setChecked(value)
    return check_box


def make_label(txt, color=None, bold=False, font=None, font_size=DeviceBox.FONTSIZE * 1.5, bg_col=None):
    label = QLabel(txt)
    format_widget(label, color, bold, font_size, font, bg_col)
    return label


def format_widget(widget, color=None, bold=None, font_size=None, font=None, bg_col=None):
    dic = {'color': color, 'font-weight': 'bold' if bold else None, 'font-size': '{}px'.format(font_size) if font_size is not None else None, 'font-family': font, 'background-color':
           bg_col if bg_col is not None else None}
    widget.setStyleSheet(make_style_sheet(dic))


def make_style_sheet(dic):
    return '; '.join('{key}: {val}'.format(key=key, val=value) for key, value in dic.items() if value is not None)
