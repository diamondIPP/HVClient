#!/usr/bin/env python
# --------------------------------------------------------
#       Module to set the config files
# created on September 18th 2020 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from os.path import join, getmtime
from src.utils import *
from typing import Any
from json import loads
from configparser import NoOptionError, NoSectionError


class Config(ConfigParser):
    
    def __init__(self, name='main.ini', display=False, section=None):

        super().__init__()
        self.Display = display

        self.Dir = join(get_base_dir(), 'config')
        self.MainFile = join(self.Dir, make_config_name(name))
        self.read(self.MainFile)
        self.Section = section
        self.NChannels = self.get_value('number of channels', int, default=1)

    def __call__(self, section, option):
        return self.get(section, option)

    def is_old(self):
        """Checks if the config file was changed during the last month."""
        return time() - getmtime(self.MainFile) > 60 * 60 * 30

    def save(self):
        with open(self.MainFile, 'r+') as f:
            self.write(f)
            f.truncate()

    def get_value(self, option, dtype: Any = str, section=None, default=None):
        try:
            v = self.get(choose(section, self.Section), option)
            return loads(v) if dtype == list or '[' in v and dtype is not str else dtype(v)
        except (NoOptionError, NoSectionError):
            return default

    def get_channel_values(self, option, dtype=float, section=None, default=None):
        v = make_list(self.get_value(option, dtype, section, default)).astype(dtype)
        return v.repeat(self.NChannels) if v.size == 1 else v

    def get_strings(self, option, default='UNKNOWN'):
        name_str = self.get_value(option)
        return [default] * self.NChannels if name_str is None else name_str.strip('[]').replace(' ', '').split(',')

    def get_active_devices(self):
        return self.get_value('active', list, 'Devices')

    def get_active_channels(self):
        return self.get_value('active channels', list, default=[0])

    def get_sections(self):
        return {section: self.get(section, 'name') for section in self.sections() if section.startswith('HV')}

    def set_section(self, section):
        self.Section = section

    def set_active_devices(self, values: str):
        if not values:
            return
        values = values if '[' in values else '[{}]'.format(values)
        values = loads(values) if type(values) == str and '[' in values else make_list(int(values))
        self.set('Devices', 'active', str(values))
        self.save()

    def set_active_channels(self, values):
        if not values:
            return
        values = values if '[' in values else '[{}]'.format(values)
        values = loads(values) if type(values) == str and '[' in values else make_list(int(values))
        self.set(self.Section, 'active channels', str(values))
        self.save()


if __name__ == '__main__':

    z = Config(section='HV1')
