import keithleyInterface
import ConfigParser
import time

class keithleyDevice(keithleyInterface.keithleyInterface):
    def __init__(self,name,config):
        self.name = name
        self.config = config
        self.keithley = None
        port = self.config.get(self.name,'address')
        bias = self.config.get(self.name,'bias')
        compliance = self.config.get(self.name,'compliance')
        self.isBusy =False
        self.maxTime = 20
        if self.config.has_option(self.name,'baudrate'):
            baudrate = self.config.get_option(self.name,'baudrate')
        else:
            baudrate = 57600
        keithleyInterface.keithleyInterface.__init__(self,port,immidiateVoltage=bias,baudrate=baudrate)


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

