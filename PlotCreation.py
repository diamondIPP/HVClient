#!/usr/bin/env python
# -*- coding: utf-8 -*- 

"""
show how to add a matplotlib FigureCanvasGTK or FigureCanvasGTKAgg widget to a
gtk.Window
"""

from __future__ import unicode_literals
import matplotlib.dates as mdates
import math

time_converter = mdates.strpdate2num("%Y/%m/%d %H:%M:%S")


def convert(filename):
    splitted_filename = filename.split('.')[0].split('_')
    # device_name = splitted_filename[0]
    # device_type = splitted_filename[1]
    # interface = splitted_filename[2]
    year = int(splitted_filename[3])
    month = int(splitted_filename[4])
    date = int(splitted_filename[5])
    retval = []
    with open(filename) as f:
        lines = f.readlines()
        for line in lines:
            try:
                splitted = line.split()
                this_time = splitted[0]
                voltage = float(splitted[1])
                current = float(splitted[2])
            except IndexError:
                #             print 'could not convert ',splitted
                continue
            time_string = '%d/%d/%d %s' % (year, month, date, this_time)
            this_time = time_converter(time_string)
            try:
                diamond = splitted[3]
            except (IndexError, ValueError):
                diamond = 'UNKNOWN'
            retval.append([this_time, voltage, current, diamond])
    return retval


#  plot_data[0],converted[-1]
def update_plot(plot_data, fig, unit='nA'):
    if len(plot_data) == 0:
        return
    fig.clear()
    ax1 = fig.add_subplot(111)
    ax1.xaxis.set()
    ax2 = ax1.twinx()
    my_fmt = mdates.DateFormatter('%H:%M:%S')
    ax1.xaxis.set_major_formatter(my_fmt)
    ax2.xaxis.set_major_formatter(my_fmt)
    ax1.ticklabel_format(axis='y')  # , style='sci')
    ax2.ticklabel_format(axis='y')  # , style='sci')
    #     fig, ax1 = plt.subplots()
    times = [x[0] for x in plot_data]
    voltages = [x[1] for x in plot_data]
    sign = math.copysign(1, voltages[0])
    label_prefix = ''
    if sign == -1:
        pass
    # label_prefix = '-1 * '
    elif sign == 1:
        pass
    # label_prefix = ''
    else:
        raise Exception()
    if unit == 'fA':
        factor = 1e12
        label = 'fA'
    elif unit == 'nA':
        factor = 1e9
        label = 'nA'
    elif unicode(unit) == u'μA' or unicode(unit) == u'muA':
        factor = 1e6
        label = '$\mu$A'
    elif unit == 'mA':
        factor = 1e3
        label = 'mA'
    else:
        print 'ERROR: ', unit, type(unit)
        factor = 1
        label = 'A'
    label = label_prefix + 'current [' + label + ']'
    ax1.set_ylabel(label, color='r')
    currents = [x[2] * factor for x in plot_data]
    # delete first element which is always 0
    del currents[0]
    del times[0]
    del voltages[0]
    # print len(times),len(voltages),len(currents)
    max_v = max(voltages)
    min_v = min(voltages)
    max_c = max(currents)
    min_c = min(currents)

    # plot time vs current in red dots
    ax1.plot_date(times, currents, 'r.', ms=2)
    ax1.set_xlabel('time')
    for tl in ax1.get_yticklabels():
        tl.set_color('r')
    # adjust limits of y-axis
    margin = find_margin(currents, factor)
    ax1.set_ylim([min_c - margin, max_c + margin])

    # plot voltage as blue line
    ax2.plot_date(times, voltages, 'b-')
    margin_v = 20
    if max_v <= 0:
        ax2.set_ylim([min_v * 1.2, margin_v])
    elif min_v < 0:
        ax2.set_ylim([min_v * 1.2, max_v * 1.2])
    else:
        ax2.set_ylim([-margin_v, 1.2 * max_v])
    ax2.set_ylabel('voltage/V', color='b')
    for tl in ax2.get_yticklabels():
        tl.set_color('b')
    ax1.grid(True)
    fig.autofmt_xdate(bottom=.25)
    # if factor == 1:
    #     ax1.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
    ax1.ticklabel_format(style='plain', axis='y', scilimits=(0, 0))
    # else:
    #     ax1.ticklabel_format(axis='y')
    #     ax2.ticklabel_format(style='sci', axis='y', scilimits=(0,0))

    return fig, ax1, ax2


def find_margin(vec, fac):
    diff = max(vec) - min(vec)
    max_val = max(abs(max(vec)), abs(min(vec)))
    if max_val > 1e-6 * fac:
        if diff < 5e-8 * fac:
            return 5e-8 * fac
    if diff < 0.3 * max_val:
        return 0.3 * max_val
    return 0.15 * diff
