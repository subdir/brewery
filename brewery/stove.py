from __future__ import print_function, with_statement

from contextlib import contextmanager

from brewery.util import construct

class Stove(object):
    @construct
    def __init__(self, power_relay, on_off_relay, program_relay):
        pass

