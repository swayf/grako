# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from collections import OrderedDict, Mapping
import json

__all__ = ['AST']

class AST(Mapping):
    def __init__(self, *args, **kwargs):
        self._elements = OrderedDict(*args, **kwargs)
        self.__setattr__ = self._setter

    def add(self, key, value, force_list=False):
        previous = self._elements.get(key, None)
        if previous is None:
            if force_list:
                self._elements[key] = [value]
            else:
                self._elements[key] = value
        elif isinstance(previous, list):
            previous.append(value)
        else:
            self._elements[key] = [previous, value]

    def update(self, *args, **kwargs):
        for dct in args:
            for k, v in dct.items():
                self.add(k, v)
        for k, v in kwargs.items():
            self.add(k, v)

    @property
    def first(self):
        key = self._elements.keys[0]
        return self._elements[key]

    def keys(self):
        return self._elements.keys()

    def items(self):
        return self._elements.items()

    def __iter__(self):
        return iter(self._elements)

    def __contains__(self, key):
        return key in self._elements

    def __len__(self):
        return len(self._elements)

    def __getitem__(self, key):
        if key not in self._elements:
            return None
        return self._elements[key]

    def __setitem__(self, key, value):
        self.add(key, value)

    def __getattr__(self, key):
        return self.__getitem__(key)

    def _setter(self, key, value):
        self.add(key, value)

    @staticmethod
    def serializable(obj):
        if isinstance(obj, AST):
            return obj._elements
        return obj

    def __repr__(self):
        return repr(self._elements)

    def json(self):
        return json.dumps(self._elements, indent=2, default=self.serializable)

