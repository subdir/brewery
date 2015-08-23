from __future__ import print_function, with_statement

import time
from contextlib import contextmanager


class Stove(object):
    def __init__(self, power_relay, on_off_relay, program_relay):
        self.power_relay = power_relay
        self.on_off_relay = on_off_relay
        self.program_relay = program_relay

    @contextmanager
    def enabled_ctx(self):
        with self.power_relay.set_closed_ctx():
            time.sleep(2)

            with self.on_off_relay.set_closed_ctx():
                time.sleep(0.2)

            for i in range(4):
                time.sleep(1)
                with self.program_relay.set_closed_ctx():
                    time.sleep(0.6)

            yield

