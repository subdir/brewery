# coding: utf-8

from __future__ import print_function, with_statement

import inspect
from functools import wraps


class StructError(Exception):
    pass


def struct_patch(name, bases, dict):
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

    return name, bases, dict


def struct(cls):
    '''
    >>> @struct
    ... class Test: pass
    Traceback (most recent call last):
    ...
    AssertionError: 'Test' must be derived from 'object'
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
    '''
    assert object in inspect.getmro(cls), "{!r} must be derived from 'object'".format(cls.__name__)
    return type(*struct_patch(
        cls.__name__,
        get_base_classes(cls),
        dict(cls.__dict__),
    ))


class StructType(type):
    def __new__(mcs, name, bases, dict):
        return type.__new__(mcs, *struct_patch(name, bases, dict))


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


def pairs(items, second_default):
    '''
    >>> list(pairs([1,2,3], 4))
    [(1, 2), (3, 4)]
    '''
    items_iter = iter(items)
    while True:
        yield (next(items_iter), next(items_iter, second_default))


def traverse_class_tree(tree):
    for (cls, bases), subtree in pairs(tree, []):
        yield cls, bases
        for subcls, subbases in traverse_class_tree(subtree):
            yield subcls, subbases


def get_base_classes(cls):
    '''
    >>> class A(object): pass
    >>> get_base_classes(A) == (object,)
    True
    >>> class B(A): pass
    >>> get_base_classes(B) == (A,)
    True
    >>> class C(object): pass
    >>> class D(B, C): pass
    >>> get_base_classes(D) == (B, C)
    True
    '''
    tree = inspect.getclasstree(inspect.getmro(cls), unique=True)
    for cls0, bases in traverse_class_tree(tree):
        if cls0 is cls:
            return bases
    assert False, "Class {!r} not found in its own tree {!r}".format(cls, tree)

