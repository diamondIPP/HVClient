#!/usr/bin/env python

""" CLI.py: Command line interface
"""

#######################################
# Imports
#######################################
import cmd
import time
import datetime
from threading import Thread


#######################################
# Class CLI
#######################################

class CLI(cmd.Cmd, Thread):
    """Command Line Interface"""

    def __init__(self):
        cmd.Cmd.__init__(self)
        Thread.__init__(self)
        self.prompt = 'HV Cmd =>>> '
        self.running = True
        self.devices = {}

    def run(self):
        self.cmdloop()

    def set_keithleys(self, keithleys):
        """ set a map of  keithley devices"""
        self.devices = keithleys
        print 'Following devices were set up:'
        for name in keithleys:
            print name, keithleys[name].interface.name, keithleys[name].name
        print '=======================================\n'

    def do_exit(self, line=''):
        """Quit CLI"""
        print '\n=============EXITING==================='
        print 'Quitting CLI'
        # Turn off the devices
        print 'Turning off all devices'
        for k in self.devices.keys():
            self.devices[k].isKilled = True
        self.running = False
        return True

    def do_EOF(self, line=''):
        for k in self.devices.keys():
            self.devices[k].isKilled = True
        self.running = False
        return True

    def do_names(self, line):
        """Print connected Keithley devices"""
        print 'There are %d devices connected:' % len(self.devices)
        k = 1
        for i in self.devices:
            print k, i
            k += 1

    def set_device_name(self,name,device_name):
        if self.devices.has_key(name):
            keithley = self.devices[name]
            keithley.set_device_name(device_name)
        else:
            print 'cannot find %s' % name

    def do_SET_NAME(self,line):
        """ Set device name of device to new_name
        Usage: SET_NAME KeithleyName NEW_DEVICE_NAME
        """
        name = line.split()[0]
        device_name = line.split()[1]
        self.set_device_name(name,device_name)

    #######################################
    # do_STATUS
    #######################################

    def read_status(self, name):
        if self.devices.has_key(name):
            device = self.devices[name]
            device.wait_for_device()
            device.isBusy = True
            try:
                print 'STATUS of %s'%name
                print '  * status: %s'%device.get_status()
                print '  * target voltage: %.1f V'%device.get_target_bias()
                print '  * current voltage: %.1f V'%device.get_bias_now()
                print '  * current current: %.2e A'%device.get_current_now()
                print '  * last updated before  %ds'%(time.time() - device.get_last_update())
            except Exception as inst:
                print type(inst), inst
            device.isBusy = False
        else:
            print 'cannot find %s' % name

    def do_STATUS(self, line):
        """ Read the status of the device
        Usage: STATUS KeithleyName
        """
        self.read_status(line)

    #######################################
    # do_ON / do_OFF
    #######################################

    def set_output(self, line, status):
        name = line.split()[0]
        try:
            assert self.devices.has_key(name), 'cannot find {name}'.format(name=name)
        except AssertionError, err:
            print err
            return
        chan_str = self.prepare_chan(line)
        chan_num = self.prepare_chan(line, get_num=True)
        if self.devices[name].has_channels:
            print 'Set Output of {ch} of {dev} to:'.format(ch=chan_str, dev=name), status
        else:
            print 'Set Output %d: %s' % (status, name)
        # if name.upper() == 'ALL':
        #     for k in self.devices:
        #         self.set_output(k, status)
        #     return
        device = self.devices[name]
        device.wait_for_device()
        device.isBusy = True
        try:
            device.interface.set_output(status, chan_num) if device.has_channels else device.interface.set_output(status)
            device.last_v_change = time.time()
            device.powering_down[chan_num] = False
        except Exception as inst:
            print type(inst), inst
        device.isBusy = False

    def do_ON(self, line):
        """ Set output of device to ON.
        Usage: ON KeithleyName
        (ON ALL to turn on all devices)
        """
        self.set_output(line, True)

    def do_OFF_FAST(self, line):
        """ Set output of device to OFF.
        Usage: OFF_FAST KeithleyName
        (OFF_FAST ALL to turn on all devices)
        """
        self.set_output(line, False)

    # todo: make on all

    def do_OFF(self, line):
        """ Set output of device to OFF.
        Usage: OFF KeithleyName
        (OFF ALL to turn off all devices)
        """
        try:
            name = line.split()[0]
            print name
            if name.upper() == 'ALL':
                for key, item in self.devices.iteritems():
                    for chan in item.ch_str:
                        self.do_OFF(key + ' ' + chan) if item.has_channels else self.do_OFF(key)
            else:
                chan = self.prepare_chan(line)
                self.devices[name].power_down(chan)
        except Exception as inst:
            print type(inst), inst

    def prepare_chan(self, line, get_num=False):
        line = line.split()
        chan = None
        if len(line) > 1:
            chan = line[1]
        if self.devices[line[0]].has_channels:
            try:
                assert chan in self.devices[line[0]].ch_str, 'This is not a valid channel'
            except AssertionError, err:
                print err
                return False
            if chan is None:
                print 'You did not enter a channel, try again!'
                return
            elif get_num:
                return int(chan[-1])
        else:
            chan = 'CH0'
        return chan


    #######################################
    # do_FILTER
    #######################################
    def setFilter(self, name, status):
        print 'Set Filter %d: %s' % (status, name)
        if name.upper() == 'ALL':
            for k in self.devices:
                self.setFilter(k, status)
            return
        if self.devices.has_key(name):
            keithley = self.devices[name]
            keithley.wait_for_device()
            keithley.isBusy = True
            try:
                keithley.set_average_filter(status)
            except Exception as inst:
                print type(inst), inst
            keithley.isBusy = False
        else:
            print 'cannot find %s' % name

    def do_FILTER(self, line):
        """ Set filter of device.
        FILTER KeithleyName status
        status should be 0/1
        ('FILTER ALL 0/1' sets all devices)"""
        try:
            name = line.split()[0]
            status = int(line.split()[1])
            print 'do_FILTER', line, name, status
            self.setFilter(name, status)
        except Exception as inst:
            print type(inst), inst

    #######################################
    # do_MANUAL
    #######################################

    def set_to_manual(self, name, status):
        """ (De-)Activates manual control mode.
        MANUAL KeithleyName status
        status should be 0/1
        ('MANUAL ALL 0/1' sets all devices)"""
        try:
            device = self.devices[name]
            try:
                device.set_to_manual(status)
            except Exception as inst:
                print type(inst), inst
        except Exception:
            print 'cannot find keithley with name "%s"' % name


    def do_MANUAL(self, line):
        try:
            [name, status] = line.split()
            status = int(status)
        except:
            print 'Wrong input for MANUAL', line
            return
        if name.upper() == 'ALL':
            for k in self.devices:
                self.set_to_manual(k, status)
        else:
            try:
                device = self.devices[name]
                device.set_to_manual(status)
            except:
                print 'cannot find keithley with name "%s"' % name

    #######################################
    # do_BIAS
    #######################################

    def setBias(self, name, target_bias, chan='CH0'):

        try:
            if self.devices.has_key(name):
                device = self.devices[name]

                min_bias = device.min_bias[chan]
                max_bias = device.max_bias[chan]
                if not min_bias <= target_bias <= max_bias:
                    print "This bias voltage", target_bias, "is not allowed! Boundaries are: ", min_bias, max_bias
                    return
                device.set_target_bias(target_bias, chan)
        except Exception as inst:
            print type(inst), inst

    def do_BIAS(self, line):
        """ Set target voltage of device.
        Usage:
        BIAS KeithleyName voltage"""
        try:
            name = line.split()[0]
            chan = self.prepare_chan(line)
            target_bias = float(line.split()[2]) if self.devices[name].has_channels else float(line.split()[1])
            self.setBias(name, target_bias, chan)

        except Exception as inst:
            print type(inst), inst

    #######################################
    # do_COMMAND
    #######################################
    def do_COMMAND(self, line):
        """performs any command on device"""
        try:
            command = line.split(None, 1)
            name = command[0]
            if self.devices.has_key(name):
                keithley = self.devices[name]
                keithley.wait_for_device()
                keithley.isBusy = True
                try:
                    print 'Write to "%s" "%s"' % (name, command[1])
                    keithley.write(command[1])
                except:
                    pass
                keithley.isBusy = False
            else:
                print 'cannot find %s' % name
        except Exception as inst:
            print type(inst), inst

    def do_read(self, line):
        """Call read for device"""
        try:
            name = line
            keithley = self.devices[name]
            keithley.wait_for_device()
            keithley.isBusy = True
            try:
                print keithley.read()
            except:
                pass
            keithley.isBusy = False
        except Exception as inst:
            print type(inst), inst
            print Exception

    #######################################
    # do_LOG
    #######################################
    def do_LOG(self,line):
        log_entry = line.split(None, 1)
        name = log_entry[0]
        self.devices[name].add_log_entry(log_entry[1])
    #######################################
    # do_NEWLOG
    #######################################

    def do_NEWLOG(self, line):
        """ Closes the current logfile and opens a new one"""

        # Close old and open new logging file
        value = datetime.datetime.fromtimestamp(time.time())
        logfile_name = "keithleyLog_" + value.strftime('%Y_%m_%d_%H_%M') + ".txt"
        self.logfile.close()
        self.logfile = open(logfile_name, "w", 1)

    # make sure it does not repeat the last command when pressing enter
    def emptyline(self):
        pass

# End of Class CLI
