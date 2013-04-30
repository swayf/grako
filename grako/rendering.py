# -*- coding: utf-8 -*-
"""
The Renderer class provides the infrastructure for generating template-based
code. It's used by the .grammars module for parser generation.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import itertools
import string
from .util import trim, ustr, isiter, strtype, indent


def render(item, join='', **fields):
    """ Render the given item
    """
    if item is None:
        return ''
    elif isinstance(item, strtype):
        return item
    elif isinstance(item, Renderer):
        return item.render(join=join, **fields)
    elif isiter(item):
        return join.join(render(e, join=join, **fields) for e in iter(item) if e is not None)
    else:
        return ustr(item)


class RenderingFormatter(string.Formatter):
    def format_field(self, value, spec):
        if ':' not in spec:
            return super(RenderingFormatter, self).format_field(render(value), spec)

        ind, sep, fmt = spec.split(':')
        if sep == '\\n':
            sep = '\n'

        if not ind:
            ind = 0
            mult = 0
        elif '*' in ind:
            ind, mult = ind.split('*')
        else:
            mult = 4
        ind = int(ind)
        mult = int(mult)

        if not fmt:
            fmt = '%s'

        if isiter(value):
            return indent(sep.join(fmt % render(v) for v in value), ind, mult)
        else:
            return indent(fmt % render(value), ind, mult)


class Renderer(object):
    template = ''
    _counter = itertools.count()
    formatter = RenderingFormatter()

    def __init__(self, template=None):
        if template is not None:
            self.template = template

    @classmethod
    def counter(cls):
        return next(cls._counter)

    @classmethod
    def reset_counter(cls):
        Renderer._counter = itertools.count()

    def render_fields(self, fields):
        pass

    def render(self, template=None, **fields):
        fields.update({k: v for k, v in vars(self).items() if not k.startswith('_')})

        override = self.render_fields(fields)
        if template is None:
            if override is not None:
                template = override
            else:
                template = self.template

        try:
            return self.formatter.format(trim(template), **fields)
        except KeyError as e:
            raise KeyError(str(e), type(self))
