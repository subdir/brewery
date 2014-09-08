# coding: utf-8

from __future__ import print_function, with_statement

import inspect
from functools import wraps


def struct(cls):
    """
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
    >>> t
    Test(a='undefined', b=1, c=2)
    >>> print(repr_struct(t, first_named_attr=1))
    Test('undefined', b=1, c=2)

    НАСЛЕДОВАНИЕ (без проверок на упячечность)

    >>> @struct
    ... class Test2(Test):
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
    >>> t2.test() # да, вот такая упячка. Зато задокументированная.
    Traceback (most recent call last):
    ...
    AttributeError: b

    NEW-STYLE CLASSES

    >>> @struct
    ... class Test3:
    ...    pass
    Traceback (most recent call last):
    ...
    AssertionError: struct.Test3 must be derived from `object`
    """
    assert object in inspect.getmro(cls), "{} must be derived from `object`".format(cls)

    argspec = inspect.getargspec(cls.__init__)
    assert not argspec.varargs
    assert not argspec.keywords

    @wraps(cls.__init__)
    def init(self, *args, **kwargs):
        cls.__init__.im_func(self, *args, **kwargs)
        # Доопределяем недоопределенные аттрибуты
        callargs = inspect.getcallargs(
            cls.__init__,
            *([self] + list(args)),
            **kwargs
        )
        for attr, val in callargs.iteritems():
            if attr != argspec.args[0]:
                if not hasattr(self, attr):
                    setattr(self, attr, val)

    class_attrs = {'__slots__':argspec.args[1:], '__init__':init}
    class_attrs.update(iter_class_methods(cls))

    if '__repr__' not in class_attrs:
        # на repr'ы из базовых классов накласть
        class_attrs['__repr__'] = repr_struct

    return type(cls.__name__, get_base_classes(cls), class_attrs)


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


def iter_class_methods(cls):
    '''
    >>> class A(object):
    ...   def a(self): pass
    ...   def x(self): pass
    >>> class B(A):
    ...   def b(self): pass
    ...   def x(self): pass
    >>> sorted(iter_class_methods(A)) == [('a', A.a.im_func), ('x', A.x.im_func)]
    True
    >>> sorted(iter_class_methods(B)) == [('b', B.b.im_func), ('x', B.x.im_func)]
    True
    '''
    for attr_name, attr in cls.__dict__.iteritems():
        if inspect.isfunction(attr):
            yield attr_name, attr


def repr_struct(self, first_named_attr=0):
    attr_strs = []
    for num, name in enumerate(self.__slots__):
        val_repr = repr(getattr(self, name))
        if num < first_named_attr:
            attr_strs.append(val_repr)
        else:
            attr_strs.append(name + "=" + val_repr)
    return "{}({})".format(type(self).__name__, ", ".join(attr_strs))

