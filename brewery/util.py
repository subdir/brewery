# coding: utf-8

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


def struct(cls):
    """
    >>> @struct
    ... class Test:
    ...    pass
    Traceback (most recent call last):
    ...
    AssertionError: util.Test must be derived from `object`
    >>> @struct
    ... class Test(object):
    ...     def __init__(self, a, b=1, c=None):
    ...         if a is None:
    ...             self.a = 'undefined'
    ...     def test(self):
    ...         return (self.a, self.b, self.c)
    >>> t = Test('a')
    >>> t.test()
    ('a', 1, None)
    >>> t.c = 2
    >>> t.test()
    ('a', 1, 2)
    >>> t.d = 3
    Traceback (most recent call last):
    ...
    AttributeError: 'Test' object has no attribute 'd'
    >>> t = Test(a=None, c=2)
    >>> t.test()
    ('undefined', 1, 2)
    """
    # cls должен наследоваться непосредственно от object (т.е. быть new-style классом)
    # и только от него.
    assert inspect.getmro(cls) == (cls, object), "{} must be derived from `object`".format(cls)

    argspec = inspect.getargspec(cls.__init__)
    assert not argspec.varargs
    assert not argspec.keywords

    @wraps(cls.__init__)
    def init(self, *args, **kwargs):
        cls.__init__.__func__(self, *args, **kwargs)
        # Доопределяем недоопределенные аттрибуты
        callargs = inspect.getcallargs(
            cls.__init__,
            *([self] + list(args)),
            **kwargs
        )
        for attr, val in callargs.iteritems():
            if not hasattr(self, attr):
                setattr(self, attr, val)

    class_attrs = {'__slots__':argspec.args, '__init__':init}
    for attr_name in dir(cls):
        if attr_name != '__init__':
            attr = getattr(cls, attr_name)
            if inspect.ismethod(attr):
                class_attrs[attr_name] = attr.__func__

    return type(cls.__name__, (object,), class_attrs)


