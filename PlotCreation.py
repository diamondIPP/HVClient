#!/usr/bin/env python
# -*- coding: utf-8 -*- 

"""
show how to add a matplotlib FigureCanvasGTK or FigureCanvasGTKAgg widget to a
gtk.Window
"""

from matplotlib.figure import Figure
import numpy as np
import matplotlib.pyplot as plt
from numpy import arange, sin, pi
import matplotlib.dates as mdates
import datetime
import time
import math

time_converter = mdates.strpdate2num("%Y/%m/%d %H:%M:%S")
def convert(filename):
    splitted_filename = filename.split('.')[0].split('_')
    device_name = splitted_filename[0]
    device_type = splitted_filename[1]
    interface = splitted_filename[2]
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
            except:
    #             print 'could not convert ',splitted
                continue
            time_string = '%d/%d/%d %s'%(year,month,date,this_time)
            this_time = time_converter(time_string)
            try:
                diamond = splitted[3]
            except:
                diamond = 'UNKNOWN'
            retval.append([this_time,voltage,current,diamond])
    return retval

#  plot_data[0],converted[-1]
def update_plot(plot_data,fig,current_range=None,unit='nA'):
    if len( plot_data)==0:
        return
    fig.clear()
    ax1 = fig.add_subplot(111)
    ax1.xaxis.set
    ax2 = ax1.twinx()
    myFmt = mdates.DateFormatter('%H:%M:%S')
    ax1.xaxis.set_major_formatter(myFmt)
    ax2.xaxis.set_major_formatter(myFmt)
    ax1.ticklabel_format(axis='y', style='sci')
    ax2.ticklabel_format(axis='y', style='sci')
#     fig, ax1 = plt.subplots()
    times = [x[0] for x in plot_data]
    voltages = [x[1] for x in plot_data]
    if unit == 'fA':
        currents = [x[2]*1e12 for x in plot_data]
        ax1.set_ylabel('current/fA', color='r')
    elif unit == 'nA':
        currents = [x[2]*1e9 for x in plot_data]
        ax1.set_ylabel('current/nA', color='r')
    elif unit == 'μA':
        currents = [x[2]*1e6 for x in plot_data]
        ax1.set_ylabel('current/μA', color='r')
    elif unit == 'μA':
        currents = [x[2]*1e3 for x in plot_data]
        ax1.set_ylabel('current/mA', color='r')
    else:
        currents = [x[2] for x in plot_data]
        ax1.set_ylabel('current/A', color='r') 
#     print len(times),len(voltages),len(currents)
    max_v = max(voltages)
    min_v = min(voltages)
    
    
    max_c = max(currents)
    min_c = min(currents)
    if current_range:
        if abs(max_c) > current_range:
            max_c = math.copysign(current_range,max_c)
        if abs(min_c) > current_range:
            min_c = math.copysign(current_range,min_c)
    # plot time vs current in red dots
    ax1.plot_date(times, currents, 'r.',ms=2)
    ax1.set_xlabel('time')
    
    
    for tl in ax1.get_yticklabels():
        tl.set_color('r')
    if max_c <= 0 and min_c <= 0:
        ax1.set_ylim([min_c*1.1,-.1*min_c])
    elif max_c>=0 and min_c >= 0:
        ax1.set_ylim([-max_c*.1,max_c*1.1])
    else:
        ax1.set_ylim([min_c-.1*(max_c-min_c),max_c+.1*(max_c-min_c)])
    ax2.plot_date(times,voltages, 'b-')
    if max_v <= 0:
        ax2.set_ylim([min_v*1.2,0])
    elif min_v < 0:
        ax2.set_ylim([min_v*1.2,max_v*1.2])
    else:
        ax2.set_ylim([0,1.2*max_v])
    ax2.set_ylabel('voltage/V', color='b')
    for tl in ax2.get_yticklabels():
        tl.set_color('b')
    ax1.grid(True)
    fig.autofmt_xdate(bottom=.25)
    ax1.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
#     ax2.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
    
    return fig,ax1,ax2