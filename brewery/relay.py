from __future__ import generator_stop

import threading
from contextlib import contextmanager

from brewery.util import clog, INFO


class RelayError(Exception):
    pass


class Relay:
    def __init__(self, interface_kit, number):
        self.interface_kit = interface_kit
        self.number = number
        self.lock = threading.Lock()
        self.exclusive_use = 0
        self.shared_use = 0

    def __repr__(self):
        return "Relay({!r}, {!r})".format(self.interface_kit, self.number)

    def set_closed(self, is_closed):
        with clog(INFO, "Relay {!r}/{!r} -> {}".format(
            self.interface_kit.getSerialNum(),
            self.number,
            "closed" if is_closed else "open",
        )):
            self.interface_kit.setOutputState(self.number, int(is_closed))

    def get_closed(self):
        return bool(self.interface_kit.getOutputState(self.number))

    @contextmanager
    def set_closed_ctx(self, enter=True, exit=False):
        with self.lock:
            if self.shared_use or self.exclusive_use:
                raise RelayError('{!r} is already in use'.format(self))
            self.exclusive_use = 1
            self.set_closed(enter)
        try:
            yield
        finally:
            with self.lock:
                self.exclusive_use = 0
                self.set_closed(exit)

    @contextmanager
    def keep_closed_ctx(self, is_closed):
        with self.lock:
            if self.exclusive_use:
                raise RelayError('{!r} is already in use'.format(self))
            if self.shared_use and self.get_closed() != is_closed:
                raise RelayError('{!r} is already in use'.format(self))
            self.shared_use += 1
            self.set_closed(is_closed)
        try:
            yield
        finally:
            with self.lock:
                self.shared_use -= 1
                if self.shared_use == 0:
                    self.set_closed(False)


class RelayController:
    def __init__(self, direction_relay, layer_relay, control_relays):
        self.direction_relay = direction_relay
        self.layer_relay = layer_relay
        self.control_relays = control_relays

    @contextmanager
    def keep_direction_ctx(self, is_straight_current):
        with self.direction_relay.keep_closed_ctx(not is_straight_current):
            yield

    @contextmanager
    def keep_layer_ctx(self, layer):
        if layer not in (0, 1):
            raise RelayError('Invalid layer {!r}'.format(layer))
        with self.layer_relay.keep_closed_ctx(bool(layer)):
            yield


class ComplexRelay:
    def __init__(self, controller, control_number, layer, is_straight_current=True):
        self.controller = controller
        self.control_number = control_number
        self.layer = layer
        self.is_straight_current = is_straight_current

    @contextmanager
    def set_closed_ctx(self, enter=True, exit=False):
        with \
            self.controller.keep_direction_ctx(self.is_straight_current), \
            self.controller.keep_layer_ctx(self.layer), \
            self.controller.control_relays[self.control_number].set_closed_ctx(enter, exit):
                yield

