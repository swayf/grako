# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import itertools
from .util import trim

def render(node):
    """ Convert the given node to it's Java representation.
    """
    if node is None:
        return ''
    elif node is True:
        return 'true'
    elif node is False:
        return 'false'
    elif isinstance(node, int):
        return node
    elif isinstance(node, basestring):
        return node
    elif isinstance(node, list):
        return ''.join(render(e) for e in node)
    else:
        return node.render()


class Renderer(object):
    template = ''
    _counter = itertools.count()

    def counter(self):
        return self._counter.next()

    def render_fields(self, fields):
        pass

    def render(self):
        fields = {k:v for k, v in vars(self).iteritems() if not k.startswith('_')}
        self.render_fields(fields)
        for k, v in fields.iteritems():
            fields[k] = render(v)
        try:
            return trim(self.template).format(**fields)
        except KeyError as e:
            raise KeyError(str(e), type(self))

