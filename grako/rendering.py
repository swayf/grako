# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import itertools
from .util import trim

def render(item, **fields):
    """ Render the given item
    """
    if isinstance(item, Renderer):
        return item.render(**fields)
    elif isinstance(item, list):
        return ''.join(render(e) for e in item)
    else:
        return str(item)


class Renderer(object):
    template = ''
    _counter = itertools.count()

    def __init__(self, template=None):
        if template is not None:
            self.template = template

    def counter(self):
        return next(self._counter)

    def render_fields(self, fields):
        pass

    def render(self, **fields):
        fields.update({k:v for k, v in vars(self).items() if not k.startswith('_')})
        self.render_fields(fields)
        fields = {k:render(v) for k, v in fields.items()}
        try:
            return trim(self.template).format(**fields)
        except KeyError as e:
            raise KeyError(str(e), type(self))

