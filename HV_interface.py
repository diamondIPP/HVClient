# Base class for all High Voltage interfaces

# ============================
# IMPORTS
# ============================


# ============================
# CONSTANTS
# ============================
ON = 1
OFF = 0


# ============================
# MAIN CLASS
# ============================
class HVInterface:
    def __init__(self, config, device_no=1, hot_start=False):
        self.device_no = device_no
        self.set_voltage = 0
        self.config = config
        self.section_name = 'HV%d' % self.device_no
        self.model_number = self.config.get(self.section_name, 'model')
        self.name = self.config.get(self.section_name, 'name')
        self.model = ''
        pass

    def set_to_manual(self, status):
        pass

    def set_output(self, status):
        pass

    def set_bias(self, voltage):
        pass

    def get_output(self):
        pass

    def read_current(self):
        pass

    def read_voltage(self):
        pass

    def read_iv(self):
        pass

    def set_voltage(self, value):
        return self.set_bias(value)

    def set_on(self):
        return self.set_output(ON)

    def set_off(self):
        return self.set_output(OFF)

    def get_set_voltage(self):
        return self.set_voltage

    def get_device_name(self, log=0):
        space = ("_" if log else " ")
        out = self.section_name + space + self.name + space + self.model_number
        return out

    def get_model_name(self):
        pass

    @staticmethod
    def is_number(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_float(s):
        try:
            float(s)
            return True
        except ValueError:
            return False
