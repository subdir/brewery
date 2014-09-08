# coding: utf-8

from __future__ import print_function, with_statement

import inspect
from functools import wraps


class StructError(Exception):
    pass


class StructType(type):
    def __new__(mcs, name, bases, dict):
        if '__init__' not in dict:
            dict['__slots__'] = ()

        else:
            orig_init = dict['__init__']

            argspec = inspect.getargspec(orig_init)
            if argspec.varargs or argspec.keywords:
                raise StructError('varargs and keyword args are not supported')

            @wraps(orig_init)
            def init(self, *args, **kwargs):
                orig_init(self, *args, **kwargs)
                # Доопределяем недоопределенные аттрибуты
                callargs = inspect.getcallargs(
                    orig_init,
                    *([self] + list(args)),
                    **kwargs
                )
                for attr, val in callargs.iteritems():
                    if attr != argspec.args[0]:
                        if not hasattr(self, attr):
                            setattr(self, attr, val)

            dict.update({'__slots__':argspec.args[1:], '__init__':init})

        if '__repr__' not in dict:
            # на repr'ы из базовых классов накласть
            dict['__repr__'] = repr_struct

        return type.__new__(mcs, name, bases, dict)


def repr_struct(self, first_named_attr=0):
    attr_strs = []
    for num, name in enumerate(self.__slots__):
        val_repr = repr(getattr(self, name))
        if num < first_named_attr:
            attr_strs.append(val_repr)
        else:
            attr_strs.append(name + "=" + val_repr)
    return "{}({})".format(type(self).__name__, ", ".join(attr_strs))


class Struct(object):
    """
    >>> class Test(Struct):
    ...     def __init__(self, a, b=1, c=None):
    ...         if a is None:
    ...             self.a = 'undefined'
    ...     def test(self):
    ...         return (self.a, self.b, self.c)
    >>> type(Test) is StructType
    True
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
    >>> t
    Test(a='undefined', b=1, c=2)
    >>> print(repr_struct(t, first_named_attr=1))
    Test('undefined', b=1, c=2)

    НАСЛЕДОВАНИЕ (автонаследование слотов не написано, и не факт что оно нужно)

    >>> class Test2(Test):
    ...    def __init__(self, a): pass
    >>> t2 = Test2(1)
    >>> isinstance(t2, Test)
    True
    >>> t2.a
    1
    >>> t2.b
    Traceback (most recent call last):
    ...
    AttributeError: b
    >>> t2.test()
    Traceback (most recent call last):
    ...
    AttributeError: b
    """
    __metaclass__ = StructType

