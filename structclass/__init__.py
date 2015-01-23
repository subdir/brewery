# coding: utf-8

from __future__ import print_function, with_statement

import inspect
from functools import wraps, total_ordering


class StructError(Exception):
    pass


def autoinit(orig_init):
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

    return init


def struct_patch(name, bases, dict):
    if '__init__' not in dict:
        dict['__slots__'] = ()
    else:
        orig_init = dict['__init__']
        argspec = inspect.getargspec(orig_init)
        dict.update({
            '__slots__' : argspec.args[1:],
            '__init__' : autoinit(orig_init)
        })

    dict.update({
        '__eq__' : struct_eq,
        '__lt__' : struct_lt,
        '__iter__' : struct_iter,
    })
    
    if '__repr__' not in dict:
        # на repr'ы из базовых классов накласть
        dict['__repr__'] = repr_struct

    return name, bases, dict


def struct(cls):
    ''' Декоратор, превращающий класс в структуру.
        Метакласс не меняется, это полезно, например, если хочется сделать
        структуру абстрактным базовым классом.

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

        НАСЛЕДОВАНИЕ

        >>> @struct
        ... class Test2(object): pass
        >>> @struct
        ... class ChildTest(Test, Test2):
        ...     pass
        >>> c = ChildTest(a=1)
        >>> c.a
        1
        >>> c.c
        >>> c.d = 2
        Traceback (most recent call last):
        ...
        AttributeError: 'ChildTest' object has no attribute 'd'

        СРАВНЕНИЕ

        >>> t > Test('a', b=0)
        True
        >>> t > Test('b', b=0)
        False

        ХЕШИ

        >>> d = {t : True}
        >>> t in d
        True
        >>> t.a = 'x'
        >>> t in d
        True

        ХИТРЫЙ КОНСТРУКТОР

        >>> @struct
        ... class SubtleTest(object):
        ...     def __init__(self, a, b=1):
        ...         if a is None:
        ...             self.a = 'undefined'

        МЕТАКЛАССЫ

        >>> from abc import ABCMeta
        >>> @struct
        ... class TestAbc(object):
        ...     __metaclass__ = ABCMeta
        ...     def __init__(self, x, y):
        ...         pass
        >>> type(TestAbc) is ABCMeta
        True
    '''
    assert object in inspect.getmro(cls), "{!r} must be derived from 'object'".format(cls.__name__)
    return total_ordering(getattr(cls, '__metaclass__', type)(*struct_patch(
        cls.__name__,
        get_base_classes(cls),
        dict(cls.__dict__),
    )))


def repr_struct(self, first_named_attr=0):
    attr_strs = []
    for num, name in enumerate(self.__slots__):
        val_repr = repr(getattr(self, name))
        if num < first_named_attr:
            attr_strs.append(val_repr)
        else:
            attr_strs.append(name + "=" + val_repr)
    return "{}({})".format(type(self).__name__, ", ".join(attr_strs))


def struct_iter(self):
    return (getattr(self, attr) for attr in self.__slots__)


def tuple_from_struct(self):
    return tuple(struct_iter(self))


def struct_eq(self, other):
    if type(self) is type(other):
        return tuple_from_struct(self) == tuple_from_struct(other)
    else:
        return False


def struct_lt(self, other):
    if type(self) is type(other):
        return tuple_from_struct(self) < tuple_from_struct(other)
    else:
        return NotImplemented


def struct_hash(self):
    return hash(tuple_from_struct(self))


class StructType(type):
    def __new__(mcs, name, bases, dict):
        return total_ordering(type.__new__(mcs, *struct_patch(name, bases, dict)))


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


def traverse_class_tree(tree):
    for entry in tree:
        if isinstance(entry, list):
            for entry in traverse_class_tree(entry):
                yield entry
        else:
            yield entry


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

