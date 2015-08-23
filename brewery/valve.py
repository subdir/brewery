from __future__ import print_function, with_statement

import time
from contextlib import contextmanager

from brewery.relay import ComplexRelay


class ValveError(Exception):
    pass


class MotorValve(object):
    def __init__(self, name, open_relay, close_relay, timeout=None):
        self.name = name
        self.open_relay = open_relay
        self.close_relay = close_relay
        self.timeout = timeout or 3

    @classmethod
    def from_ctl(cls, name, controller, control_number, layer, straight_open=True, timeout=None):
        return cls(
            name,
            open_relay = ComplexRelay(controller, control_number, layer, straight_open),
            close_relay = ComplexRelay(controller, control_number, layer, not straight_open),
            timeout = timeout,
        )

    def __repr__(self):
        return 'MotorValve({!r})'.format(self.name)

    def open(self):
        with self.open_relay.set_closed_ctx(True, False):
            time.sleep(self.timeout)

    def close(self):
        with self.close_relay.set_closed_ctx(True, False):
            time.sleep(self.timeout)

    @contextmanager
    def opened_ctx(self):
        self.open()
        try:
            yield
        finally:
            self.close()


class SolenoidValve(object):
    def __init__(self, name, open_relay):
        self.name = name
        self.open_relay = open_relay

    def __repr__(self):
        return 'SolenoidValve({!r})'.format(self.name)

    @contextmanager
    def opened_ctx(self):
        with self.open_relay.set_closed_ctx(True, False):
            yield

