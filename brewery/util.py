# coding: utf-8

from __future__ import generator_stop

import inspect
from functools import wraps
from contextlib import contextmanager
from logging import log, INFO


@contextmanager
def clog(level,message):
    try:
        log(level, message + "...")
        yield
    except Exception as err:
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

