import keithleyInterface
import ConfigParser
import time
import math

class keithleyDevice(keithleyInterface.keithleyInterface):
    def __init__(self,name,config):
        self.name       = name
        self.config     = config
        self.keithley   = None
        
        compliance = self.config.get(self.name,'compliance')

        self.port    = self.config.get(self.name,'address')
        self.ramp    = float(self.config.get(self.name,'ramp'))
        self.bias    = float(self.config.get(self.name,'bias'))        
        self.minBias = float(self.config.get(self.name,'minBias'))        
        self.maxBias = float(self.config.get(self.name,'maxBias'))        
        self.maxStep = float(self.config.get(self.name,'maxStep'))  

        # make sure bias is consistent
        if self.maxBias < self.minBias:
            raise Exception("Invalid config file (maxBias < minBias)")
        if self.bias < self.minBias:
            raise Exception("Invalid config file (bias < minBias)")
        if self.bias > self.maxBias:
            raise Exception("Invalid config file (bias > maxBias)")
        

        # last time the actual voltage was changed 
        self.lastUChange = time.time()
        self.lastBias    = 0

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


    def wait_for_device(self):
        now = time.time()
        while time.time()-now < self.maxTime and self.isBusy:
            time.sleep(.1)

    def doRamp(self):
        # Try to update voltage (we remember the measurement from the last loop)
        # (the step we can make in voltage is the ramp-speed times 
        # how many seconds passed since last change)
        deltaU = self.bias - self.lastBias
        Ustep = abs(self.ramp * (time.time() - self.lastUChange))

        # Limit the maximal voltage step size
        if Ustep > self.maxStep:
            Ustep = self.maxStep

        if abs(deltaU) > 0.1:
            if abs(deltaU) <= Ustep:
                self.setVoltage( self.bias )
                self.lastUChange = time.time()
            else:
                self.setVoltage( self.lastBias + math.copysign( Ustep, deltaU ))
                self.lastUChange = time.time()
    # End of ramp



if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read('keithley.cfg')
    keithley = keithleyDevice('Keithley1',config)
    keithley.setOutput(1)

