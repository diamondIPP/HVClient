import keithleyInterface
import ConfigParser
import time

class keithleyDevice(keithleyInterface.keithleyInterface):
    def __init__(self,name,config):
        self.name       = name
        self.config     = config
        self.keithley   = None
        
        compliance = self.config.get(self.name,'compliance')

        self.port       = self.config.get(self.name,'address')
        self.ramp       = float(self.config.get(self.name,'ramp'))
        self.bias       = float(self.config.get(self.name,'bias'))        
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
            print "waiting for", self.name
            time.sleep(.1)




if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read('keithley.cfg')
    keithley = keithleyDevice('Keithley1',config)
    keithley.setOutput(1)

