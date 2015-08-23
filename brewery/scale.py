
from __future__ import generator_stop

import time
from contextlib import contextmanager


class Scale:
    def __init__(self, bridge, inputno, a, b):
        self.bridge = bridge
        self.inputno = inputno
        self.a = a
        self.b = b

    def enable(self):
        self.bridge.setEnabled(self.inputno, True)

    def disable(self):
        self.bridge.setEnabled(self.inputno, False)

    def read_weight(self):
        return self.bridge.getBridgeValue(self.inputno) * self.a + self.b

    def read_weight_avg(self, n=100, sleep_time=0.005):
        weight = 0.0
        for i in range(1, n+1):
            weight += self.read_weight()
            time.sleep(sleep_time)
        return weight / n

    @contextmanager
    def enabled_ctx(self):
        self.enable()
        try:
            time.sleep(2)
            yield
        finally:
            self.disable()

