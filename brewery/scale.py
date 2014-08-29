from __future__ import print_function, with_statement

import time
from contextlib import contextmanager

from brewery.util import struct

@struct
class Scale(object):
    def __init__(self, bridge, inputno, a, b):
        pass

    def enable(self):
        self.bridge.setEnabled(self.inputno, True)

    def disable(self):
        self.bridge.setEnabled(self.inputno, False)

    def read_weight(self):
        return self.bridge.getBridgeValue(self.inputno) * self.a + self.b

    @contextmanager
    def enabled_ctx(self):
        self.enable()
        try:
            time.sleep(2)
            yield
        finally:
            self.disable()

