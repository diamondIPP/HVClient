# Base class for all High Voltage interfaces

ON=1
OFF=0


class HV_interface():
    def __init(self,config, device_no=1, hotStart=False):
        self.__device_no = device_no
        self.__set_voltage=0
        self.__config=config
        self.section_name = 'HV%d'%self.__device_no
        pass

    def set_output(self,status):
        pass

    def set_bias(self,voltage):
        self.__set_voltage = voltage
        pass

    def get_output(self):
        pass

    def read_current(self):
        pass

    def read_voltage(self):
        pass

    def getModelName(self):
        pass

    def set_voltage(self,value):
        return self.set_bias(value)

    def set_ON(self):
        self.set_output(ON)

    def set_OFF(self):
        self.set_output(OFF)

    def get_set_voltage(self):
        return self.__set_voltage

    def is_number(self,s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def is_float(self,s):
        try:
            float(s)
            return True
        except ValueError:
            return False

