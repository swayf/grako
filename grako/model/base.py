""" Base definitions for models of programs.
"""
import os.path
import weakref
from ..rendering import Renderer

EOLCOL = 50

def render(node, **kwargs):
    """ Convert the given node to it's Java representation.
    """
    if node is None:
        return ''
    elif node is True:
        return 'true'
    elif node is False:
        return 'false'
    elif isinstance(node, list):
        return ''.join(render(e, **kwargs) for e in node)
    else:
        return str(node)

def indent(text, indent=1):
    """ Indent the given block of text by indent*4 spaces
    """
    if text is None:
        return ''
    text = str(text)
    if indent >= 0:
        lines = [' ' * 4 * indent + t for t in text.split('\n')]
        # check that a trailing EOL is not indented
#        if lines and not lines[-1].strip():
#            lines[-1] = ''
        text = '\n'.join(lines)
    return text

def rate(obj):
    """ Rate the given tree negatively for each node that is a generic Node
    """
    result = 0
    if isinstance(obj, Node):
        result += -1 * (obj.__class__ == Node)
        result += sum(rate(c) for c in obj.children)
    if isinstance(obj, list):
        result += sum(rate(e) for e in obj)
    return result


class Context(object):
    """ Context for source code generation.

        It contains a copy of the source code when available,
        a symbol table, and a stack of active views for symbols
        that are used anonymously.
    """

    def __init__(self, buf, eol_comments=True):
        super(Context, self).__init__()
        self.buf = buf
        self.eol_comments = eol_comments

        self._symbols = dict()

    def basename(self):
        """ Base name of the original source code file.
        """
        return os.path.splitext(os.path.basename(self.buf.filename))[0]

    def add_symbol(self, name, node):
        """ Add a symbol to the symbol table.
        """
        assert isinstance(name, basestring)
        self._symbols[name] = node

    def get_symbol(self, name):
        """ Get symbol from symbol table.
        """
        if not isinstance(name, basestring):
            print 'get_symbol', name, type(name)
        assert isinstance(name, basestring)
        return self._symbols.get(name)

    def get_or_create_symbol(self, name, node_type=None, children=None):
        symbol = self.get_symbol(name)
        if symbol is None and '.' not in name:  # FIXME: this is patch to avoid declaring dotted names
            if node_type is None:
                node_type = InferredSymbol
            if children is None:
                children = []
            # asume that it is a global and declare it
            symbol = node_type(self, None, "ID", [name] + children, None, None)
            self._symbols[name] = symbol
            self.globals.append(symbol)
        return symbol

class Node(Renderer):
    """ Base class for model nodes, in charge of the rendering infrastructure.

        Rendering consists of providing arguments through object attributes
        and the :meth:render_args method for them to be applied to a
        :class:`string.Template` instance created from the *template* class
        variable.
    """

    inline = True
    template = '$name'

    def __init__(self, context, children):
        super(Node, self).__init__()
        self._context = context
        self._children = children
        self._parent = None
        self.text = self._text()
        if context.eol_comments and self.line:
            self._eol_comment = self.__eol_comment()
        else:
            self._eol_comment = ''

        # only expressions and declarations have types,
        # but we'll declare it here for convenience
        self.type = None
        self._adopt_children(self.children)
        self.__postinit__()
        self.__unify__()

    def __postinit__(self):
        """ Convenience post-constructor without all the required paramenters.
        """
        pass

    def __topdowninit__(self):
        """ The builder should call this method after the model is created
            so children have a chance to look at their initialized parents.
        """
        pass


    def __unify__(self):
        """ Called as a second-pass initialization to allow for type unification
        """
        pass

    def _adopt_children(self, childs):
        for c in childs:
            if isinstance(c, Node):
                c._parent = weakref.proxy(self)
            elif isinstance(c, list):
                self._adopt_children(c)


    @property
    def context(self):
        return self._context

    @property
    def children(self):
        return self._children

    @property
    def parent(self):
        return self._parent

    def child(self, selector):
        """ Return the child node identified by the given *selector*.
        """
        if isinstance(selector, int):
            return self._child_index(selector)
        elif isinstance(selector, basestring):
            return self._child_named(selector)
        else:
            return self._child_classed(selector)

    def _child_index(self, i):
        """ Safely retrieve the child at the given index.
        """
        return self._children[i] if len(self._children) > i else None

    def _child_named(self, name):
        """ Find a child with the given name.
        """
        for c in self._children:
            if c == name:
                return c
            if isinstance(c, Node) and c.name == name:
                return c

    def _child_classed(self, cls):
        """ Find a child of the given class.
        """
        for c in self._children:
            if isinstance(c, cls):
                return c

    def _children_classed(self, cls):
        """ Find all children of the given class.
        """
        result = []
        for c in self._children:
            if isinstance(c, cls):
                result.append(c)
            elif isinstance(c, Node):
                result += c._children_classed(cls)
        return result


    def _text(self):
        """ Return the first line of the source code for the current node.
        """
        if self.line:
            return self.context.text[self.line - 1]
        else:
            return ''

    def __eol_comment(self):
        """ A generic end-of-line comment.
        """
        def compress_whitespace(s):
            if not s:
                return ''
            return ' '.join(s.split())
        return '// %s' % (compress_whitespace(self.text).strip())

    def unify_types(self, anode, bnode):
        """ Simplistic type unification.
        """
        if not isinstance(anode, Node) or not isinstance(bnode, Node):
            return
        if anode.type is None:
            anode.type = bnode.type
        elif bnode.type is None:
            bnode.type = anode.type

    def find_enclosing_view(self):
        """ Find the closest parent that defines a VIEW context.
        """
        if self.parent:
            return self.parent.find_enclosing_view()


    def rate(self):
        """Rate -1 for each generic Node in this tree.
        """
        return rate(self)

    @property
    def line(self):
        """ Return the source-code line number for this node.
        """
        if self.pos:
            return self.pos[0]
        else:
            return -1

    def render_comments(self, javadoc=False):
        if not self._comments:
            return ''

        result = '\n' + '\n'.join(' * ' + c.strip() for c in self._comments) + '\n */\n'
        if javadoc:
            result = '/**' + result
        else:
            result = '/*' + result
        result = '\n' + result
        return result

    def _add_eol_comment(self, text):
        if not (text and self._eol_comment):
            return text
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if '$eol_comment' in line:
                line = line.replace('$eol_comment', '').rstrip()
                lines[i] = line + ' ' * (EOLCOL - len(line)) + self._eol_comment
        return '\n'.join(lines)


    def render_args(self, args):
        """ Provide arguments for template rendering.
        """
        args.update(
            pos=self.pos,
            name=self.name,
            lineno=self.lineno,
            type=str(self.type) if self.type else 'Object'
            )

    def render(self):
        """ Render the current node as Java.
        """
        code = super(Node, self).render()
        comments = self.render_comments()
        return comments + self._add_eol_comment(code)

    def __str__(self):
        return self.render()


class SymbolNode(Node):
    def __postinit__(self):
        super(SymbolNode, self).__postinit__()
        self.value = self.children[0]
        self.ident = self._ident()
        self.type = None
        self._record = None
        self._redefined = None
        self.context.add_symbol(self.ident, self)

    def _ident(self):
        ''' Allow sub-classes to override how self.ident is constructed
        '''
        if hasattr(self, 'ident'):
            return self.ident
        elif isinstance(self.value, basestring):
            return self.value
        else:
            return str(self.value.raw_id)

    def id_path(self):
        if not self._record:
            return [self.java_id]
        else:
            return self._record.id_path() + [self.java_id]

    def qualified_id(self):
        return '.'.join(self.id_path())

    def find_symbol(self, name):
        if self.ident == name:
            return self

    def render_args(self, args):
        if self.type is None:
            args.update(type='Object')

    template = '$type $java_id;'


class InferredSymbol(SymbolNode):
    def __postinit__(self):
        super(InferredSymbol, self).__postinit__()
        self._eol_comment = '// generated automatically'

    template = '$type $java_id; $eol_comment'
