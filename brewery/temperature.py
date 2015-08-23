from __future__ import print_function, with_statement

from contextlib import contextmanager

from brewery.util import struct

@struct
class Thermocouple(object):
    def __init__(self, temperature_sensor, index, thermocouple_type):
        pass

    def read(self):
        self.temperature_sensor.setThermocoupleType(self.index, self.thermocouple_type)
        return self.temperature_sensor.getTemperature(self.index)

