# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import itertools
from .util import trim

def render(node):
    """ Convert the given node to it's Java representation.
    """
    if isinstance(node, Renderer):
        return node.render()
    elif isinstance(node, list):
        return ''.join(render(e) for e in node)
    else:
        return str(node)


class Renderer(object):
    template = ''
    _counter = itertools.count()

    def counter(self):
        return next(self._counter)

    def render_fields(self, fields):
        pass

    def render(self):
        fields = {k:v for k, v in vars(self).items() if not k.startswith('_')}
        self.render_fields(fields)
        for k, v in fields.items():
            fields[k] = render(v)
        try:
            return trim(self.template).format(**fields)
        except KeyError as e:
            raise KeyError(str(e), type(self))

