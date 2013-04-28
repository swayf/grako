"""
Base definitions for models of programs.

** under construction **
"""
from __future__ import print_function, division, absolute_import, unicode_literals
from ..rendering import Renderer

EOLCOL = 50


class Context(object):
    """ Context for source code generation.

        It contains a copy of the source code when available,
        a symbol table, and a stack of active views for symbols
        that are used anonymously.
    """

    def __init__(self, **kwargs):
        super(Context, self).__init__()
        self._symbols = dict()
        self.__dict__.update(kwargs)


class Node(Renderer):
    """ Base class for model nodes, in charge of the rendering infrastructure.

        Rendering consists of providing arguments through object attributes
        and the :meth:render_fields method for them to be applied to a
        :class:`string.Template` instance created from the *template* class
        variable.
    """

    inline = True
    template = ''

    def __init__(self, ctx, parseinfo=None):
        super(Node, self).__init__()
        self._ctx = ctx
        self._parseinfo = parseinfo

    @property
    def ctx(self):
        return self._ctx

    @property
    def parseinfo(self):
        return self._parseinfo

    @property
    def line_info(self):
        if self.parseinfo:
            return self.parseinfo.buffer.line_info(self.parseinfo.pos)

    @property
    def text(self):
        if self.parseinfo:
            return self.line_info.text.strip('\n')

    def __str__(self):
        return self.render()
