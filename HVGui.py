#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import matplotlib
import os
try:
    import matplotlib.backends.backend_tkagg
except:
    pass
matplotlib.use('TkAgg')
import numpy as np
from numpy import arange, sin, pi,cos
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
#from matplotlib.backend_bases import key_press_handler

from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import sys
if sys.version_info[0] < 3:
    import Tkinter as Tk
else:
    import tkinter as Tk
from time import time
import datetime
import PlotCreation

# a2.setp(c, color='r', linewidth=2.0)

class HVGui():
    def on_key_event(event):
        print('you pressed %s'%event.key)
#     key_press_handler(event, canvas, toolbar)
    def update(self):
        try:
            self.root.update()
        except:
            pass
        
    def _quit(self):
        self.destroyed = True
        # print 'QUITTING',self.destroyed
        print 'Closing GUI'
        self.root.quit()     # stops mainloop
        try:
            self.root.destroy()  # this is necessary on Windows to prevent
        except:
            pass
        print '======================================='
        
                        # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    def __init__(self,devices):
        self.destroyed = False
        self.root = Tk.Tk()
            
        self.root.minsize(1000, 200)  # x/y
# root.maxsize(1000, 200)
        self.last_update = time()
        self.update_interval = Tk.IntVar()
        self.update_interval.set(2)
        self.next_update = Tk.StringVar()
        self.next_update.set('NAN s')
        self.max_age = 1 # maximum age 24h
        self.root.wm_title("HV Client - ETH Zurich")
        self.devices = {}
        self.plot_boxes = []
        self.toptopframe = Tk.Frame(master = self.root)
        self.toptopframe.pack( side = Tk.TOP)
        self.add_devices(devices)
        self.update_plots()
        self.update_clock()
        self.add_plots(2)
        
    def mainloop(self):
        self.root.mainloop()
        
    def set_status(self,device_name,status):
        self.devices[device_name]['status'] = status
        self.update_status_display(device_name)
        
    def set_mode(self,device_name,mode):
        self.devices[device_name]['mode'] = mode
        
    def set_target_bias(self,device_name,target_bias):
        self.devices[device_name]['target_bias'] = target_bias
        
    def update_status_display(self,device_name):
        if not self.devices[device_name].has_key('status'):
            self.devices[device_name]['status_var'].set('NAN')
            self.devices[device_name]['status_color'].set('yellow')
        elif not self.devices[device_name]['status']:
            self.devices[device_name]['status_var'].set('OFF')
            self.devices[device_name]['status_color'].set('black')
        elif  self.devices[device_name]['mode'] == 'MANUAL':
            self.devices[device_name]['status_var'].set('MANUAL')
            self.devices[device_name]['status_color'].set('red')
        elif self.devices[device_name]['mode'] == 'RAMPING':
            self.devices[device_name]['status_var'].set('Ramping to %.1f V'%self.devices[device_name]['target_bias'])
            self.devices[device_name]['status_color'].set('red')
        else:
            self.devices[device_name]['status_var'].set('ON')
            self.devices[device_name]['status_color'].set('red')
        self.devices[device_name]['status_label'].config(fg=self.devices[device_name]['status_color'].get())
        self.update()
        
    def add_multiple_measurements(self,device_name,measurements):
        if not self.devices[device_name].has_key('measurements'):
            self.devices[device_name]['measurements']=[]
        self.devices[device_name]['measurements'].extend(measurements)
        self.devices[device_name]['measurements']= sorted(self.devices[device_name]['measurements'])
        self.update_current_display(device_name)
        
    def add_measurement(self,device_name,time_stamp,voltage,current,diamond_name):
        if not self.devices[device_name].has_key('measurements'):
            self.devices[device_name]['measurements']=[]
        time_stamp = mdates.date2num(datetime.datetime.fromtimestamp(time_stamp))
        measurement = [time_stamp,voltage,current,diamond_name]
        if len(self.devices[device_name]['measurements']) != 0:
            if self.devices[device_name]['measurements'][-1] == measurement:
                return
#         print 'add measurement', measurement
        self.devices[device_name]['measurements'].append(measurement)
        self.update_measurement_buffer(device_name)
        self.update_current_display(device_name)
    
    def update_current_display(self, device_name):
        self.update_status_display(device_name)
        if not self.devices[device_name].has_key('measurements'):
            self.devices[device_name]['measurements'] = []
        if len(self.devices[device_name]['measurements']) ==0:
#             print 'update_current_display', ' -- empty display'
            return
        device = self.devices[device_name]
        last_measurement = device['measurements'][-1]
        self.devices[device_name]['name_var'].set(last_measurement[3])
        self.devices[device_name]['voltage_var'].set('%+4d V'%last_measurement[1])
        self.devices[device_name]['current_var'].set(self.get_current_string(last_measurement[2]))
        time_stamp = last_measurement[0]
        ts = mdates.num2date(time_stamp)
        time_stamp_string = ts.strftime('%H:%M:%S')
        self.devices[device_name]['time_var'].set(time_stamp_string)
        self.update( )
        
# #         print 'updated ',device_name,
#         print self.devices[device_name]['name_var'].get(),
#         print self.devices[device_name]['voltage_var'].get(),
#         print self.devices[device_name]['current_var'].get(),
#         print self.devices[device_name]['time_var'].get()
    
    def update_measurement_buffer(self,device_name):
        measurements = self.devices[device_name]['measurements']
        last_measurement = measurements[-1][0]
        for x in measurements:
            if x[0]-last_measurement > self.max_age:
                print 'remove',x[0]
                measurements.remove(x)
            else:
                return 
        measurements = filter(lambda x: last_measurement- x[0] < self.max_age, measurements)
        self.devices[device_name]['measurements'] = measurements
        
    def add_devices(self, devices):
        # print 'add DEVICES: ', devices
        for name,device_data in sorted(devices.items()):
            self.devices[name] = {
                                  'name': device_data.get_device_name(),
                                  'voltage': 0,
                                  'current': 0,
                                  'time': 0}
            device = self.devices[name]
            device['voltage']
            self.add_voltage_current_entry(self.toptopframe, name,device)
            device['device_var'].set(name)
            device['name_var'].set(device['name'])
            device['voltage_var'].set('%+4d V'%device['voltage'])
            device['current_var'].set(self.get_current_string(device['current']))
            device['time_var'].set(self.get_time_string(time()))
            device['time_var'].set('NAN')
            device['mode']='NORMAL'
            device['target_bias'] = float('nan')
        separator = Tk.Frame(self.toptopframe,width=50,     bd=0)#, relief=Tk.SUNKEN)
        separator.pack(side = Tk.LEFT,fill=Tk.Y)
        f = Tk.Frame(self.toptopframe)#, relief=Tk.SUNKEN)
        f.pack(side = Tk.RIGHT,fill=Tk.Y)
        
        self.time = Tk.StringVar()
        self.time.set(self.get_time_string(datetime.datetime.now()))
        self.clock = Tk.Label(f, textvariable=self.time,font=("Helvetica", 18) )
        self.clock.pack(side = Tk.TOP)
        l = Tk.Label(master=f,text='Update Interval:')
        l.pack(side=Tk.TOP)
        w = Tk.Spinbox(master=f,from_=1 , to=60,width = 5, textvariable=self.update_interval)
        w.pack(side=Tk.TOP)
        Tk.Label(f,text='Next Update in:').pack(side=Tk.TOP)
        Tk.Label(f,textvariable=self.next_update).pack(side=Tk.TOP)
        
        button = Tk.Button(master=f, text='Quit', command=self._quit)
        button.pack(side=Tk.TOP)

    def add_voltage_current_entry(self,frame,name,device):
        self.devices[name] = device
        subframe = Tk.Frame(master = frame)
        subframe.pack( side = Tk.LEFT)
        subsubframe = Tk.Frame(master = subframe)
        subsubframe.pack(side = Tk.TOP)
        device['device_var'] = Tk.StringVar()
        device['device_label'] = Tk.Label(subsubframe, textvariable=device['device_var'],font=("Helvetica", 16))
        device['device_label'].pack(side = Tk.LEFT)
        Tk.Label(subsubframe, text=' - ').pack(side = Tk.LEFT)
        device['name_var'] = Tk.StringVar()
        device['name_label'] = Tk.Label(subsubframe, textvariable=device['name_var'],font=("Helvetica", 16))
        device['name_label'].pack(side = Tk.LEFT)
        device['voltage_var'] = Tk.StringVar()
        device['voltage_label'] = Tk.Label(subframe, textvariable=device['voltage_var'],font=("Helvetica", 16))
        device['voltage_label'].pack(side = Tk.TOP)
        device['current_var'] = Tk.StringVar()
        device['current_label'] = Tk.Label(subframe, textvariable=device['current_var'],font=("Helvetica", 16) )
        device['current_label'].pack(side = Tk.TOP)
        
        device['status_color'] = Tk.StringVar()
        device['status_color'].set('black')
        device['status_var'] = Tk.StringVar()
        device['status_label'] = Tk.Label(subframe, 
                                          textvariable=device['status_var'],
                                          font=("Helvetica", 16,"bold"),
                                          fg = device['status_color'].get() )
        device['status_label'].pack(side = Tk.TOP)
        
        sf = Tk.Frame(master = subframe)
        sf.pack(side = Tk.TOP)
        device['time_var'] = Tk.StringVar()
        Tk.Label(sf, text='Last measurement: ',font=("Helvetica", 9) ).pack(side=Tk.LEFT)
        device['time_label'] = Tk.Label(sf, textvariable=device['time_var'],font=("Helvetica", 9) )
        device['time_label'].pack(side = Tk.LEFT)
        
        Tk.Frame(frame,width=10,     bd=0, relief=Tk.FLAT).pack(side = Tk.LEFT,fill=Tk.Y)
        Tk.Frame(frame,width=4,     bd=2, relief=Tk.GROOVE).pack(side = Tk.LEFT,fill=Tk.Y)
        Tk.Frame(frame,width=10,     bd=0, relief=Tk.FLAT).pack(side = Tk.LEFT,fill=Tk.Y)
        
        return subframe
    
    @staticmethod
    def get_current_string(current):
        if abs(current) < 1e-6:
            retVal = '%5.1f nA'%(current/1e-9)
        elif abs(current) < 1e-3:
            retVal = '%5.1f μA'%(current/1e-6)
        elif abs(current) < 1:
            retVal = '%5.1f mA'%(current/1e-3)
        else:
            retVal =  '%5.1f A'%(current)
        return retVal
    @staticmethod
    def get_time_string(t):
        try:
            ts = datetime.datetime.fromtimestamp(t)
        except:
            ts = t
        try:
            return ts.strftime('%H:%M:%S')
        except:
            print 'ERROR: ',type(t)
            

    def update_clock(self):
#         for name,device in sorted(self.devices.items()):
#             device['time_var'].set(self.get_time_string(time()))
        delta_t = time()-self.last_update
        self.time.set(self.get_time_string(datetime.datetime.now()))
        
        t = self.update_interval.get() - float(delta_t)
        str_t = '%d s'%int(t)
        self.next_update.set(str_t)
        self.root.after(900, self.update_clock)
#         self.root.update()
    
    def update_plots(self):
        for plot_box in self.plot_boxes:
            #self.plot_boxes
            duration = plot_box['optionFrame']['varDuration'].get()
            device = plot_box['optionFrame']['varDevice'].get()
            maxrange =  plot_box['optionFrame']['varMaxRange'].get()
            unit = plot_box['optionFrame']['varUnit'].get()
            if u'μA' == plot_box['optionFrame']['varUnit'].get():
                unit = 'muA'
            stop = plot_box['optionFrame']['varBreak'].get()
            if stop:
                continue
            plot_box['currentDevice'] = device
            plot_box['currentDuration'] = duration
            try:
                measurements = self.devices[device]['measurements']
            except:
#                 print 'Invalid device',device
                continue
            if len(measurements)==0:
                print device, 'empty mesurements'
                continue
            last = measurements[-1][0]
            plot_data = filter(lambda x:last-x[0]<duration/24.,measurements)
            if plot_box['currentDevice'] == device and plot_box['currentDuration'] == duration:
                if plot_box.has_key('last_measurement'):
                    if plot_box['last_measurement'] == last:
                        continue
            plot_box['last_measurement'] = last
            PlotCreation.update_plot(plot_data,plot_box['f'],current_range = 10**maxrange, unit=unit)
            plot_box['canvas'].draw()
        self.root.after(self.update_interval.get()*1000, self.update_plots)
        self.last_update = time()
        
        
    def add_draw_option_frame(self,frame):
        retVal = {}
        retVal['optionlist'] = self.devices.keys()
        retVal['optionlist2'] = [2,4,8,12,24]
        retVal['optionFrame'] = Tk.Frame(master = frame)
        retVal['optionFrame'].pack(side = Tk.LEFT)
        retVal['varDevice'] = Tk.StringVar()
        retVal['varDevice'].set(retVal['optionlist'][0])
        retVal['varDuration'] = Tk.IntVar()
        retVal['varDuration'].set(retVal['optionlist2'][-1])
        retVal['labelDevice'] = Tk.Label(text='Device Selection',master = retVal['optionFrame'])
        retVal['labelDevice'].pack(side=Tk.TOP)
        retVal['optDevice'] = Tk.OptionMenu(retVal['optionFrame'], retVal['varDevice'],*retVal['optionlist'])
        retVal['optDevice'].pack(side=Tk.TOP)
        retVal['labelDuration'] = Tk.Label(text='Plot last hours',master = retVal['optionFrame'])
        retVal['labelDuration'].pack(side=Tk.TOP)
        retVal['optDuration'] = Tk.OptionMenu(retVal['optionFrame'], retVal['varDuration'],*retVal['optionlist2'])
        retVal['optDuration'].pack(side=Tk.TOP)
        retVal['varMaxRange']= Tk.IntVar()
        retVal['varMaxRange'].set(3)
        retVal['labelMaxRange'] =  Tk.Label(text='Max Current Range\n (Exponent)',master = retVal['optionFrame'],fg='red')
        retVal['labelMaxRange'].pack(side=Tk.TOP)
        retVal['optMaxRange'] = Tk.Spinbox(master=retVal['optionFrame'],from_=-10 , to=10,width = 5, textvariable=retVal['varMaxRange'],fg='red')
        retVal['optMaxRange'].pack(sid=Tk.TOP)
        
        unit_options = ['fA', 'nA', u'μA', 'mA', 'A']
        retVal['varUnit']= Tk.StringVar()
        retVal['varUnit'].set('nA')
        retVal['labelUnit'] =  Tk.Label(text='Unit of Current',master = retVal['optionFrame'])
        retVal['labelUnit'].pack(side=Tk.TOP)
        retVal['optUnit'] = Tk.OptionMenu(retVal['optionFrame'], retVal['varUnit'],*unit_options)
        retVal['optUnit'].pack(side=Tk.TOP)
        
        retVal['varBreak'] = Tk.BooleanVar()
        retVal['varBreak'].set(False)
        retVal['optBreak'] = Tk.Checkbutton(retVal['optionFrame'], text="Break Update", variable=retVal['varBreak'])
        retVal['optBreak'].pack(side=Tk.TOP)
        
        return retVal
        
    def add_plot_box(self,frame):
        # print 'ADD Plot Box'
        # plot_box = {}
        plot_box = {}
        plot_box['f'] =   Figure(figsize=(8,3), dpi=100)
        plot_box['f'].autofmt_xdate()
        plot_box['subframe'] = Tk.Frame(master = frame)
        plot_box['subframe'].pack(side = Tk.TOP,fill=Tk.BOTH,expand=1)
        plot_box['optionFrame'] = self.add_draw_option_frame(plot_box['subframe'])
        plot_box['canvas'] = FigureCanvasTkAgg(plot_box['f'], master=plot_box['subframe'])
        plot_box['canvas'].show()
        plot_box['canvas'].get_tk_widget().pack(fill=Tk.BOTH,expand=1)
        
        plot_box['toolbar'] = NavigationToolbar2TkAgg( plot_box['canvas'], plot_box['subframe'] )
        plot_box['toolbar'].update()
        plot_box['canvas']._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        plot_box['currentDuration'] = 0
        plot_box['currentDevice'] = ''
        return plot_box
    
    def add_plots(self,n=2): 
        for i in range(n):
            self.plot_boxes.append(self.add_plot_box(self.root))    


if __name__ == '__main__':
    devices = {
               'HV1':{
                    'name':'SILICON',
                    'voltage':-200,
                    'current':13e-6,
                    },
               'HV5':{'name':'II6-94',
                      'voltage':-1100,
                      'current':15e-6,
                      },
               'HV6':{'name':'II6-96',
                      'voltage':-1100,
                      'current':12e-6,
                      }
               }
    gui = HVGui(devices)
    converted = []
    for dirname, dirnames, filenames in os.walk('.'):
        for filename in filenames:
            if filename.startswith('HV6_'):
                print filename
                convert = PlotCreation.convert(filename)
                converted.extend(convert)
    converted = filter(lambda x: abs(x[2])<1e10,converted)
    converted = sorted(converted)
    
    min_t = min(converted[:][0])
    max_t = max(converted[:][0])
    
    # print converted
    duration = 12./(24.)
    now = mdates.date2num(datetime.datetime.now())
    plot_data = converted #filter(lambda x: now-x[0] < duration,converted)
    print 'fill measurements'
    gui.add_multiple_measurements('HV6',converted)
    
    PlotCreation.update_plot(plot_data,gui.plot_boxes[0]['f'])
    gui.plot_boxes[0]['canvas'].draw()
    plot_data = converted[len(converted)/2:]
    PlotCreation.update_plot(plot_data,gui.plot_boxes[1]['f'])
    gui.plot_boxes[1]['canvas'].draw()
    
    
    b = gui.plot_boxes[0]
    f = b['f']
    c = b['canvas']

# If you put root.destroy() here, it will cause an error if
# the window is closed with the window manager.
