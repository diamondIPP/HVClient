__author__ = 'testbeam'

# ============================
# IMPORTS
# ============================
from keithley24XX import Keithley24XX
from threading import Thread
from ConfigParser import ConfigParser, NoOptionError
from time import time, sleep
from math import copysign
import sys

# for *_interface do import bla

# U = Keithley24XX("blub")


# ============================
# MAIN CLASS
# ============================
class HVDevice(Thread):
    def __init__(self, config, device_no, hot_start):
        Thread.__init__(self)

        self.isKilled = False

        self.config = config
        self.keithley = None
        
        self.section_name = 'HV%d' % device_no

        try:
            self.port = self.config.get(self.section_name, 'address')
            self.ramp_speed = float(self.config.get(self.section_name, 'ramp'))
            self.target_bias = float(self.config.get(self.section_name, 'bias'))
            self.min_bias = float(self.config.get(self.section_name, 'min_bias'))
            self.max_bias = float(self.config.get(self.section_name, 'max_bias'))
            self.max_step = float(self.config.get(self.section_name, 'max_step'))
            self.model_number = int(self.config.get(self.section_name, 'model'))
            self.baudrate = self.config.get(self.section_name, 'baudrate')
        except NoOptionError, err:
            print err, '--> exiting program'
            sys.exit(-1)

        self.interface = None
        self.init_interface(config, device_no, hot_start)

        self.isBusy = False
        self.maxTime = 20

        # evealuate hot start
        if hot_start:
            self.status = 1
            self.update_voltage_current()
            voltage = self.get_bias()
            print voltage
            # self.immidiateVoltage = voltage
            self.target_bias = voltage
            self.biasNow = voltage
        else:
            self.status = 0
            self.biasNow = 0

        # last time the actual voltage was changed
        self.last_v_change = time()
        self.current_now = 0
        self.powering_down = False
        self.last_update = time()
        self.manual = False

        # make sure bias is consistent
        if self.max_bias < self.min_bias:
            raise Exception("Invalid config file (maxBias < minBias)")
        if self.target_bias < self.min_bias:
            raise Exception("Invalid config file (bias < minBias)")
        if self.target_bias > self.max_bias:
            raise Exception("Invalid config file (bias > maxBias)")

    # ============================
    # INIT DEVICE INTERFACE
    def init_interface(self, config, device_no, hot_start):
        # if statements for model name
        print self.model_number
        if self.model_number == 2400 or self.model_number == 2410:
            self.interface = Keithley24XX(config, device_no, hot_start)
        else:
            print "unkonwn model number: could not instantiate any device"

    # ============================
    # MAIN LOOP FOR THREAD (overwriting thread run)
    def run(self):
        now = time()
        while not self.isKilled:
            sleep(.5)
            if time() - now > 1 and not self.manual:
                self.update_voltage_current()
                self.ramp()
                self.update_voltage_current()
                now = time()

    # ============================
    # GET-FUNCTIONS
    def get_current(self):
        return self.current_now

    def get_bias(self):
        return self.biasNow

    def get_target_bias(self):
        return self.target_bias

    def get_status(self):
        return self.status

    def get_update_time(self):
        return self.last_update

    # ============================
    # SET-FUNCTIONS
    def set_target_bias(self, target):
        self.target_bias = target
        self.last_v_change = time()

    def set_to_manual(self, status):
        self.target_bias = self.interface.set_to_manual(status)
        self.manual = status

    # ============================
    # MISCELLANEOUS FUNCTIONS
    def is_ramping(self):
        return abs(self.biasNow - self.target_bias) > 0.1

    def power_down(self):
        self.set_target_bias(0)
        self.powering_down = True

    def wait_for_device(self):
        now = time()
        while time() - now < self.maxTime and self.isBusy:
            sleep(.2)

    def update_voltage_current(self):
        self.wait_for_device()
        self.isBusy = True
        self.status = self.interface.getOutputStatus()
        if self.status:
            try:
                iv = self.interface.read_iv()
                self.biasNow = iv[0]
                self.current_now = iv[1]
                self.last_update = time()
                # print 'readIV',voltage,current,self.targetBias,rest
            except Exception as inst:
                print 'Could not read valid iv', type(inst), inst
        self.isBusy = False

    def ramp(self):
        # Try to update voltage (we remember the measurement from the last loop)
        # (the step we can make in voltage is the ramp-speed times
        # how many seconds passed since last change)
        if not self.status:
            return
        delta_v = self.target_bias - self.biasNow
        print 'elapsed time:', (time() - self.last_v_change)
        step_size = abs(self.ramp_speed * (time() - self.last_v_change))

        # Limit the maximal voltage step size
        if step_size > self.max_step:
            step_size = self.max_step

        # print 'delta U ',delta_v,step_size
        newtime = time()
        if abs(delta_v) > 0.1:
            if abs(delta_v) <= step_size:
                new_bias = self.target_bias
            else:
                new_bias = self.biasNow + copysign(step_size, delta_v)
                # print self.biasNow, step_size,delta_v

            self.isBusy = True
            self.interface.setVoltage(new_bias)
            if new_bias == self.target_bias and not self.powering_down:
                print '%s is done with ramping to %d' % (self.interface.name, self.target_bias)
            self.last_v_change = newtime
            self.isBusy = False
        if self.powering_down and abs(self.biasNow) < .1:
            self.interface.setOutput(0)
            self.powering_down = False
            print '%s has ramped down and turned off' % self.interface.name
            # End of ramp

# ============================
# MAIN
# ============================
if __name__ == '__main__':
    conf = ConfigParser()
    conf.read('keithley.cfg')
    keithley = HVDevice(conf, 1, False)
    keithley.interface.set_on()
