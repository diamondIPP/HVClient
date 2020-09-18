#!/usr/bin/env python
# -*- coding: utf-8 -*-

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, date2num, num2date
from datetime import datetime, timedelta
from collections import OrderedDict
from warnings import filterwarnings, catch_warnings


times = OrderedDict([('5min', 5 / 60.), ('10min', 10 / 60.), ('20min', 20 / 60.), ('0.5', .5), ('1', 1), ('2', 2), ('4', 4), ('8', 8), ('inf', 1000)])
units = OrderedDict([('pA', 1e-12), ('nA', 1e-9), (u'μA', 1e-6), ('mA', 1e-3), ('A', 1)])


class LiveMonitor(object):

    def __init__(self, dummy=False):

        self.Unit = 'nA'
        self.VMin = -100
        self.VMax = 100
        self.CMin = None
        self.CMax = None
        self.TMin = 'inf'

        fig, ax1 = plt.subplots()
        self.fig = fig
        self.ax1 = ax1
        if dummy:
            self.format_dummy()
            self.canvas = FigureCanvas(fig)
            return

        self.ax1.set_xlabel('Time [hh:mm]')
        self.ax1.set_ylabel('Leakage Current [{}]'.format(self.Unit), color='r')
        self.ax1.tick_params('y', colors='r')

        self.ax2 = self.ax1.twinx()
        self.ax2.set_ylabel('Voltage', color='b')
        self.ax2.tick_params('y', colors='b')

        self.canvas = FigureCanvas(self.fig)
        self.canvas.draw()

        # these lists hold the data
        self.time = []
        self.voltage = []
        self.current = []

    def init(self, lst):
        for data in lst:
            self.current.append(data[2])
            self.voltage.append(data[1])
            self.time.append(date2num(data[0]))

    def format_dummy(self):
        with catch_warnings():
            filterwarnings('ignore')
            col = 'snow'
            self.ax1.spines['bottom'].set_color(col)
            self.ax1.spines['top'].set_color(col)
            self.ax1.spines['right'].set_color(col)
            self.ax1.spines['left'].set_color(col)
            self.ax1.tick_params(axis='x', colors=col)
            self.ax1.tick_params(axis='y', colors=col)
            self.ax1.set_axis_bgcolor(col)
            self.fig.patch.set_facecolor(col)

    def get_duration(self):
        return num2date(self.time[-1]) - num2date(self.time[0]) if len(self.time) > 1 else timedelta(seconds=1)

    def format(self):
        if len(self.time) > 2:
            self.ax1.xaxis.set_major_formatter(DateFormatter('%H:%M{}'.format(':%S' if self.get_duration().total_seconds() < 60 * 5 else '')))
            self.ax1.set_xlabel('Time [hh:mm]')
            self.ax2.set_ylabel('Voltage', color='b')
            self.ax1.set_ylabel(u'Leakage Current [{}]'.format(self.Unit), color='r')
            self.ax1.tick_params('y', colors='r')
            self.ax2.tick_params('y', colors='b')
            self.ax2.set_ylim(self.VMin, self.VMax)
            self.ax1.set_ylim(auto=True) if self.CMin == self.CMax else self.ax1.set_ylim(self.CMin, self.CMax)
            self.ax1.set_xlim(self.TMin, self.time[-1])
            self.ax2.set_xlim(self.TMin, self.time[-1])
            self.fig.subplots_adjust(bottom=.15)
            self.ax1.grid(ls='--', lw=.4)

    def add_data(self, t, v, i, dttime=False):
        if v and (not self.time or t != self.time[-1] and v != 0):
            self.time.append(date2num(datetime.fromtimestamp(t) if not dttime else t))
            self.voltage.append(float(v))
            self.current.append(float(i))

    def update(self, unit, cmin, cmax, vmin, vmax, t_displayed):
        self.Unit = unit
        self.CMin = cmin
        self.CMax = cmax
        self.VMin = vmin
        self.VMax = vmax
        self.ax1.cla()
        self.ax2.cla()
        if self.time:
            self.TMin = self.time[0] if t_displayed == 'inf' else date2num(num2date(self.time[-1]) - timedelta(hours=times[t_displayed]))
        self.format()

        if len(self.time) > 2:
            try:
                n_points = len(self.time) - 1  # prevent racing conditions

                self.ax1.plot(self.time[:n_points], [c / units[self.Unit] for c in self.current[:n_points]], '.r', lw=.2, ls='-', ms=1)
                self.ax2.plot(self.time[:n_points], self.voltage[:n_points], '.b', lw=.2, ls='-', ms=1)
                self.canvas.draw()
            except Exception as err:
                print(err)
                pass

    def reset(self):
        self.time = []
        self.voltage = []
        self.current = []
        self.fig.clf()
