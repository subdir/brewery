from __future__ import print_function, with_statement

import inspect
from functools import wraps
from contextlib import contextmanager
from logging import log, INFO

@contextmanager
def clog(level,message):
    try:
        log(level, message + "...")
        yield
    except Exception, err:
        log(level, message + "... ERROR: {!r}".format(err))
    finally:
        log(level, message + "... Done.")

@contextmanager
def open_phidget(phidget_class, serial_no, attach_timeout=10000):
    phidget = phidget_class()
    phidget.openPhidget(serial_no)
    try:
        with clog(INFO, "Waiting for attach {!r} #{!r} (timeout {!r}ms)".format(
            phidget_class.__name__,
            serial_no,
            attach_timeout,
        )):
            phidget.waitForAttach(attach_timeout)
        yield phidget
    finally:
        phidget.closePhidget()

def construct(func):
    argspec = inspect.getargspec(func)
    assert not argspec.varargs
    assert not argspec.keywords
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        for attr, val in inspect.getcallargs(func, *([self] + args), **kwargs).iteritems():
            setattr(self, attr, val)
        func(self, *args, **kwargs)
    return wrapper

