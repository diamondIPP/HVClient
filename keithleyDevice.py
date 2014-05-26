import keithleyInterface
import ConfigParser
import time
import math
from threading import Thread

class keithleyDevice(keithleyInterface.keithleyInterface, Thread):
    def __init__(self,name,config):

        Thread.__init__(self)
        self.isKilled = False

        self.name       = name
        self.config     = config
        self.keithley   = None

        compliance = self.config.get(self.name,'compliance')

        self.port    = self.config.get(self.name,'address')
        self.ramp    = float(self.config.get(self.name,'ramp'))
        self.targetBias = float(self.config.get(self.name,'bias'))
        self.minBias = float(self.config.get(self.name,'minBias'))
        self.maxBias = float(self.config.get(self.name,'maxBias'))
        self.maxStep = float(self.config.get(self.name,'maxStep'))

        # make sure bias is consistent
        if self.maxBias < self.minBias:
            raise Exception("Invalid config file (maxBias < minBias)")
        if self.targetBias < self.minBias:
            raise Exception("Invalid config file (bias < minBias)")
        if self.targetBias > self.maxBias:
            raise Exception("Invalid config file (bias > maxBias)")

        # last time the actual voltage was changed
        self.lastUChange = time.time()
        self.biasNow = 0
        self.currentNow = 0
        self.status = 0
        self.powering_down = False
        self.lastUpdate = time.time()
        self.manual = False

        self.isBusy   = False
        self.maxTime  = 20

        if self.config.has_option(self.name,'baudrate'):
            baudrate = self.config.get_option(self.name,'baudrate')
        else:
            baudrate = 57600

        # Start with an intial voltage of 0
        keithleyInterface.keithleyInterface.__init__(self,
                                                     self.port,
                                                     immidiateVoltage=0,
                                                     baudrate=baudrate)


    def set_manual(self,status):
        if status == False:
            target = self.getSetVoltage()
            self.set_target_bias(target)
        self.manual = status
        print 'set Mode of keithley %s to %b'%(self.name,self.manual)


    def get_current(self):
        return self.currentNow

    def get_bias(self):
        return self.biasNow

    def get_target_bias(self):
        return self.targetBias

    def set_target_bias(self,target):
        self.targetBias = target
        self.lastUChange = time.time()

    def get_status(self):
        return self.status

    def get_update_time(self):
        return self.lastUpdate

    def is_ramping(self):
        return  abs( self.biasNow - self.targetBias)> 0.1

    def power_down(self):
        self.set_target_bias(0)
        self.powering_down = True

    def run(self):
        now = time.time()
        while not self.isKilled:
            time.sleep(.1)
            if time.time()-now>1 and not self.manual:
                self.updateVoltageCurrent()
                self.doRamp()
                self.updateVoltageCurrent()
                now = time.time()




    def wait_for_device(self):
        now = time.time()
        while time.time()-now < self.maxTime and self.isBusy:
            time.sleep(.1)

    def updateVoltageCurrent(self):
        self.wait_for_device()
        self.isBusy=True
        self.status = self.getOutputStatus()
        if self.status:
            try:
                [voltage, current,rest] = self.readIV()
                self.biasNow = voltage
                self.currentNow = current
                self.lastUpdate = time.time()
                #print 'readIV',voltage,current,self.targetBias,rest
            except Exception as inst:
                print 'Could not read valid iv',type(inst),inst
        self.isBusy=False

        pass


    def doRamp(self):
        # Try to update voltage (we remember the measurement from the last loop)
        # (the step we can make in voltage is the ramp-speed times
        # how many seconds passed since last change)
        if not self.status:
            return
        deltaU = self.targetBias - self.biasNow
        Ustep = abs(self.ramp * (time.time() - self.lastUChange))

        # Limit the maximal voltage step size
        if Ustep > self.maxStep:
            Ustep = self.maxStep

        #print 'delta U ',deltaU,Ustep
        newtime = time.time()
        if abs(deltaU) > 0.1:
            if abs(deltaU) <= Ustep:
                newBias =  self.targetBias
            else:
                newBias = self.biasNow + math.copysign( Ustep, deltaU )
                #print self.biasNow, Ustep,deltaU

            self.isBusy=True
            self.setVoltage(newBias)
            self.lastUChange = newtime
            self.isBusy=False
        if self.powering_down and abs(self.biasNow) <.1:
            self.setOutput(0)
            self.powering_down = False
    # End of ramp



if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read('keithley.cfg')
    keithley = keithleyDevice('Keithley1',config)
    keithley.setOutput(1)

