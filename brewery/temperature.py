from __future__ import generator_stop

from contextlib import contextmanager


class Thermocouple:
    def __init__(self, temperature_sensor, index, thermocouple_type):
        self.temperature_sensor = temperature_sensor
        self.index = index
        self.thermocouple_type = thermocouple_type

    def read(self):
        self.temperature_sensor.setThermocoupleType(self.index, self.thermocouple_type)
        return self.temperature_sensor.getTemperature(self.index)

