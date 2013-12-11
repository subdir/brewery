from __future__ import print_function, with_statement

from contextlib import contextmanager

from brewery.util import construct

class Thermocouple(object):
    @construct
    def __init__(self, temperature_sensor, index, thermocouple_type):
        pass


