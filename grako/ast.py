# -*- coding: utf-8 -*-
"""
Define the AST class, a direct descendant of dict that's used during parsing
to store the values of named elements of grammar rules.
"""
from __future__ import print_function, division, absolute_import, unicode_literals

__all__ = ['AST']

class AST(dict):
    """
    A dictionary with attribute-style access. It maps attribute access to
    the real dictionary.
    """
    # ActiveState Recipe:
    # http://code.activestate.com/recipes/473786-dictionary-with-attribute-style-access/

    def __init__(self, *args, **kwargs):
        super(AST, self).__init__(*args, **kwargs)

    def __getstate__(self):
        return self.__dict__.items()

    def __setstate__(self, items):
        for key, val in items:
            self.__dict__[key] = val

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, super(AST, self).__repr__())

    def __setitem__(self, key, value):
        self.add(key, value)

    def __getitem__(self, name):
        if name in self:
            return super(AST, self).__getitem__(name)

    def __delitem__(self, name):
        return super(AST, self).__delitem__(name)

    __getattr__ = __getitem__
    __setattr__ = __setitem__

    def __getattribute__(self, name):
        if name in self:
            return self[name]
        return super(AST, self).__getattribute__(name)

    def copy(self):
        ch = AST(self)
        return ch

    def add(self, key, value, force_list=False):
        previous = self[key]
        if previous is None:
            if force_list:
                super(AST, self).__setitem__(key, [value])
            else:
                super(AST, self).__setitem__(key, value)
        elif isinstance(previous, list):
            previous.append(value)
        else:
            super(AST, self).__setitem__(key, [previous, value])
        return self
