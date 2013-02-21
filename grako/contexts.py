# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import re
from contextlib import contextmanager
from collections import namedtuple
from .ast import AST
from .exceptions import FailedParse, FailedCut, FailedLookahead
from . import buffering

ParseInfo = namedtuple('ParseInfo', ['buffer', 'rule', 'pos', 'endpos'])

class ParseContext(object):
    def __init__(self,
                 whitespace=None,
                 comments_re=None,
                 ignorecase=False,
                 parseinfo=False,
                 trace=False,
                 nameguard=True,
                 encoding='utf-8',
                 bufferClass=buffering.Buffer):
        super(ParseContext, self).__init__()

        self.whitespace = whitespace
        self.comments_re = comments_re
        self.ignorecase = ignorecase
        self.encoding = encoding
        self.parseinfo = parseinfo
        self.bufferClass = bufferClass
        self.nameguard = nameguard

        self._buffer = None
        self._ast_stack = []
        self._concrete_stack = [None]
        self._rule_stack = []
        self._cut_stack = [False]
        self._memoization_cache = dict()
        if not trace:
            self._trace = lambda x: ()
            self._trace_event = lambda x: ()
            self._trace_match = lambda x, y: ()

    def _reset_context(self):
        self._buffer = None
        self._ast_stack = []
        self._concrete_stack = [None]
        self._rule_stack = []
        self._cut_stack = [False]
        self._memoization_cache = dict()

    def goto(self, pos):
        self._buffer.goto(pos)

    @property
    def _pos(self):
        return self._buffer.pos

    def _goto(self, pos):
        self._buffer.goto(pos)

    def _eatwhitespace(self):
        self._buffer.eatwhitespace()

    def _eatcomments(self):
        if self.comments_re is not None:
            opts = re.MULTILINE if '\n' in self.comments_re else 0
            while self._buffer.matchre(self.comments_re, opts):
                pass

    def _next_token(self):
        p = None
        while self._pos != p:
            p = self._pos
            self._eatwhitespace()
            self._eatcomments()

    @property
    def ast(self):
        return self._ast_stack[-1]

    @ast.setter
    def ast(self, value):
        self._ast_stack[-1] = value

    def _push_ast(self):
        self._push_cst()
        self._ast_stack.append(AST())

    def _pop_ast(self):
        self._pop_cst()
        return self._ast_stack.pop()

    def _add_ast_node(self, name, node, force_list=False):
        if name is not None:  # and node:
            self.ast.add(name, node, force_list)
        return node

    def _update_ast(self, ast):
        for key, value in ast.items():
            if key not in self.ast or not isinstance(value, list):
                self._add_ast_node(key, value)
            else:
                prev = self.ast[key]
                if isinstance(prev, list):
                    prev.extend(value)
                else:
                    self.ast[key] = [prev] + value

    @property
    def cst(self):
        return self._concrete_stack[-1]

    @cst.setter
    def cst(self, cst):
        self._concrete_stack[-1] = cst

    def _push_cst(self):
        self._concrete_stack.append(None)

    def _pop_cst(self):
        return self._concrete_stack.pop()

    def _add_cst_node(self, node):
        if node is None:
            return
        previous = self._concrete_stack[-1]
        if previous is None:
            self._concrete_stack[-1] = node
        elif previous == node:  # FIXME: Don't know how this happens, but it does
            return
        elif isinstance(previous, list):
            previous.append(node)
        else:
            self._concrete_stack[-1] = [previous, node]

    def _extend_cst(self, cst):
        if cst is None:
            return
        if self.cst is None:
            self.cst = cst
        elif isinstance(self.cst, list):
            if isinstance(cst, list):
                self.cst.extend(cst)
            else:
                self.cst.append(cst)
        elif isinstance(cst, list):
            self.cst = [self.cst] + cst
        else:
            self.cst = [self.cst, cst]

    def _is_cut_set(self):
        return self._cut_stack[-1]

    def _cut(self):
        self._cut_stack[-1] = True

    def _push_cut(self):
        self._cut_stack.append(False)

    def _pop_cut(self):
        return self._cut_stack.pop()

    def _rulestack(self):
        stack = '.'.join(self._rule_stack)
        if len(stack) > 60:
            stack = '...' + stack[-60:]
        return stack

    def _find_rule(self, name):
        return None

    def _find_semantic_rule(self, name):
        return None

    def _trace(self, msg, *params):
        print(unicode(msg % params).encode(self.encoding), file=sys.stderr)

    def _trace_event(self, event):
        self._trace('%s   %s \n\t%s', event, self._rulestack(), self._buffer.lookahead())

    def _trace_match(self, token, name=None):
        if self._trace:
            name = name if name else ''
            self._trace('MATCHED <%s> /%s/\n\t%s', token, name, self._buffer.lookahead())

    def _error(self, item, etype=FailedParse):
        raise etype(self._buffer, item)

    @contextmanager
    def _try(self):
        p = self._pos
        self._push_ast()
        try:
            yield
            ast = self.ast
            cst = self.cst
        except:
            self._goto(p)
            raise
        finally:
            self._pop_ast()
        self._update_ast(ast)
        self._extend_cst(cst)

    @contextmanager
    def _option(self):
        self._push_cut()
        try:
            with self._try():
                yield
        except FailedCut:
            raise
        except FailedParse as e:
            if self._is_cut_set():
                self._error(e, FailedCut)
        finally:
            self._pop_cut()

    _optional = _option

    @contextmanager
    def _group(self):
        self._push_cst()
        try:
            yield
            cst = self.cst
        finally:
            self._pop_cst()
        self._add_cst_node(cst)

    @contextmanager
    def _if(self):
        p = self._pos
        self._push_ast()
        try:
            yield
        finally:
            self._goto(p)
            self._pop_ast()  # simply discard

    @contextmanager
    def _ifnot(self):
        p = self._pos
        self._push_ast()
        try:
            yield
        except FailedParse:
            self._goto(p)
            pass
        else:
            self._goto(p)
            self._error('', etype=FailedLookahead)
        finally:
            self._pop_ast()  # simply discard

    def _repeater(self, f):
        result = []
        while True:
            self._push_cut()
            try:
                with self._try():
                    value = f()
                if value is not None:
                    result.append(value)
            except FailedCut:
                raise
            except FailedParse as e:
                if self._is_cut_set():
                    self._error(e, FailedCut)
                else:
                    return result
            finally:
                self._pop_cut()

    def _repeat(self, f, plus=False):
        one = []
        if plus:
            with self._try():
                one = [f()]
        return one + self._repeater(f)

