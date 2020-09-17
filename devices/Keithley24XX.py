from .Keithley import *
from time import sleep
from configparser import NoOptionError
import math
from utils import isfloat, isint, warning


class Keithley24XX(Keithley):
    def __init__(self, config, device_no=1, hot_start=False):
        Keithley.__init__(self, config, device_no, hot_start)
        self.removeCharacters = '\r\n\x00\x13\x11\x10'
        self.init_keithley(hot_start)
        self.output = ''
        self.hot_start()

    def init_keithley(self, hot_start=False):
        sleep(.2)
        self.clear_buffer()
        self.identify()
        self.set_source_output()
        self.set_voltage_range(self.MaxVoltage)
        self.set_measurement_speed(2)  # was 10 before

        if not hot_start:
            self.set_output(OFF)
            self.reset()
            self.set_source_output()
            self.set_fixed_volt_mode()
            self.set_standard_output_format(':FORM:ELEM VOLT,CURR,RES,TIME,STAT')
            self.set_concurrent_measurement(True)
            self.set_filter_type('REP')
            self.set_average_filter(True)
            self.set_average_filter_count(3)
            self.set_current_protection(100e-6)
            self.set_compliance_abort_level('LATE')

        sleep(.3)
        self.clear_error_queue()

    # ============================
    # SET-FUNCTIONS

    def set_bias(self, voltage, channel=0):
        if self.validate_voltage(voltage):
            return self.write(':SOUR:VOLT %s' % voltage)

    def set_beeper(self, status):
        data = ':SYST:BEEP:STAT '
        data += 'ON' if status else 'OFF'
        return self.write(data)

    def set_beeper_on(self):
        return self.set_beeper(ON)

    def set_beeper_off(self):
        return self.set_beeper(OFF)

    def set_compliance_abort_level(self, abort_level):
        if abort_level not in ['NEVER', 'EARLY', 'LATE']:
            return False
        self.write(':SOURCE:SWEEP:CABort %s' % abort_level)

    def set_source_output(self):
        try:
            self.output = self.Config.get(self.SectionName, 'output')
        except NoOptionError as err:
            print(err)
        if self.output.lower().startswith('rear') or self.output.lower().startswith('back'):
            return self.write(':ROUT:TERM REAR')
        else:
            self.write(':ROUT:TERM FRONT')

    def set_fixed_volt_mode(self):
        return self.write(':SOUR:VOLT:MODE FIX')

    def set_trigger_counter(self, triggers):
        if triggers < 1 or triggers >= 2500:
            print('Trigger Counter is only allowed in range 1 to 2500! You entered: ', triggers)
            return -1
        return self.write(':TRIG:COUN %s' % int(triggers))

    def set_concurrent_measurement(self, status=True):
        if status:
            ret_value = self.write(':FUNC:CONC ON')
            ret_value *= self.write(':SENS:FUNC \'VOLT:DC\'')
            ret_value *= self.write(':SENS:FUNC \'CURR:DC\'')
            return ret_value
        else:
            return self.write(':FUNC:CONC OFF')

    def set_filter_type(self, filter_type):
        if filter_type not in ['MOV', 'REP']:
            raise Exception('invalid filterType: %s' % filter_type)
        return self.write(':SENS:AVER:TCON %s' % filter_type)

    def set_average_filter(self, status=True):
        if status:
            return self.write(':SENS:AVER:STAT ON')
        return self.write('SENS:AVER:STAT OFF')

    def set_average_filter_count(self, count):
        if count > 100 or count < 1:
            raise Exception('Average Filter Count not in valif rage: %s' % count)
        return self.write(':SENS:AVER:COUN %s' % count)

    def set_current_protection(self, value):
        if not self.validate_current(value):
            raise Exception('setting currentProtection: not valid current: %s' % value)
        return self.write(':CURR:PROT:LEV %s' % value)

    def set_max_voltage(self):
        self.MaxVoltage = 200 if self.Model == 2400 else 1100

    # ============================
    # GET-FUNCTIONS
    # returns the activated concurrent measured values
    def get_measure_mode(self):
        data = self.get_answer_for_query(':SENS:FUNC?')
        self.get_answer_for_query(data)

    def get_sweep_points(self):
        data = self.get_answer_for_query(':SOUR:SWE:POIN?')
        if data == '':
            return -1
        print('Sweep Points: %s' % data)
        return data if 0 <= int(data) <= 2500 else -1

    # ============================
    # region NOT USED
    @staticmethod
    def validate_current(current):
        if current:
            return True  # TODO

    def set_volt_sweep_start(self, start):
        if not self.validate_voltage(start):
            return -1
        return self.write(':SOUR:VOLT:START %s' % start)

    def set_volt_sweep_stop(self, stop):
        print('set sweepstopValue: %s' % stop)
        if self.MaxVoltage < math.fabs(stop):
            stop = math.copysign(self.MaxVoltage, stop)
            print('set voltage to maximum allowed voltage: %s' % stop)
        stop_voltage = float(stop)
        if not self.validate_voltage(stop_voltage):
            return -1
        return self.write(':SOUR:VOLT:STOP %s' % stop_voltage)

    def set_volt_sweep_step(self, step):
        step_voltage = float(step)
        if not self.validate_voltage(step_voltage):
            print('invalid sweepStepValue: ', step_voltage)
            return -1
        return self.write(':SOUR:VOLT:STEP %s' % step_voltage)

    def set_voltage_range(self, v_max):
        return self.write(":SOUR:VOLT:RANG {}".format(v_max))

    def set_current_measurement_range(self, curr_range):
        if not self.validate_current(curr_range):
            raise Exception('setting CurrentMeasurmentRange: not valid current: %s' % curr_range)
        return self.write(':SENS:CURR:RANG %s' % curr_range)

    def set_measurement_delay(self, delay):
        if delay < 0 or delay > 999.9999:
            raise Exception('measurmentdelay is out of range: %s' % delay)
        data = ':SOUR:DEL %s' % float(delay)
        return self.write(data)

    def set_sweep_ranging_mode(self, mode):
        if mode not in ['BEST', 'AUTO', 'FIXED']:
            raise Exception('not valid sweeping range mode %s' % mode)
        return self.write(':SOUR:SWE:RANG %s' % mode)

    def set_volt_source_mode(self, mode):
        if mode not in ['FIXED', 'MIXED', 'SWEEP']:
            raise Exception('VoltSourceMode not valid: %s' % mode)
        return self.write(':SOUR:VOLT:MODE %s' % mode)

    def set_sweep_spacing_type(self, spacing_type):
        if spacing_type not in ['LIN', 'LOG']:
            raise Exception('Sweep Spacing Type not valid %s' % spacing_type)
        return self.write(':SOUR:SWE:SPAC %s' % spacing_type)

    def set_sense_function(self, f):
        # todo: check if function ok..
        return self.write(':SENSE:FUNC \"%s\"' % f)

    def set_sense_resistance_range(self, res_range):
        if isfloat(res_range):
            # todo check if value is valid
            return self.write(':SENS:RES:RANG %s' % res_range)
        else:
            print('resistance is not in valid Range %s' % res_range)
            return False
        pass

    def set_sense_resistance_mode(self, mode):
        if mode in ['MAN', 'AUTO', 'MANUAL']:
            return self.write(':SENSE:RESISTANCE:MODE %s' % mode)
        else:
            print('Sense Resistance mode is not valid: %s' % mode)
            return False
        pass

    def set_sense_resistance_offset_compensated(self, state):
        if not isint(state):
            if state in ['True', 'TRUE', '1', 'ON', 'On']:
                state = True
            elif state in ['False', 'FALSE', '0', 'OFF', 'Off']:
                state = False
            else:
                warning('Four Wire Measurement not valid state: {}'.format(state))
                return False
        return self.write(':SENSE:RESISTANCE:OCOMPENSATED {}'.format('ON' if state else 'OFF'))

    def set_sense_voltage_protection(self, prot_volt):
        if isfloat(prot_volt):
            if self.validate_voltage(prot_volt):
                return self.write(':SENSE:VOLT:PROTECTION %s' % prot_volt)
            else:
                print('Protection Voltage not in valid area: %s' % prot_volt)
                return False
        else:
            print('Protection Voltage no a Float: %s' % prot_volt)
        pass

    def set_source_function(self, f):
        if f in ['VOLT', 'CURR', 'VOLTAGE', 'CURRENT']:
            return self.write(':SOURCE:FUNC %s' % f)
        else:
            print('try to set not valid source Function: %s' % f)
            return False
        pass

    def set_four_wire_measurement(self, state=True):
        if not isint(state):
            if state in ['True', 'False', 'TRUE', 'FALSE']:
                state = True
            else:
                print('Four Wire Measurement not valid state: %s' % state)
                return False
        if state:
            return self.write(':SYST:RSENSE ON')
        else:
            return self.write('SYST:RSENSE OFF')
        pass


if __name__ == '__main__':
    keithley = Keithley24XX(load_config('config/keithley.cfg'), 1, True)
