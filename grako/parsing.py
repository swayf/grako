# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import re
from contextlib import contextmanager
from .util import memoize
from . import buffering
from .exceptions import *  # @UnusedWildImport
from .ast import AST


class AbstractParserMixin(object):
    def _find_semantic_rule(self, name):
        result = getattr(self, name, None)
        if result is None or not isinstance(result, type(self._find_rule)):
            raise MissingSemanticFor(name)
        return result


class Parser(object):
    def __init__(self, text,
                        whitespace=None,
                        comments_re=None,
                        ignorecase=False,
                        simple=False,
                        trace=False,
                        nameguard=True,
                        bufferClass=buffering.Buffer):
        if isinstance(text, buffering.Buffer):
            self._buffer = text
        else:
            self._buffer = buffering.Buffer(text, whitespace, ignorecase=ignorecase)
        self.comments_re = comments_re
        self._simple = simple
        self._trace = trace
        self._bufferClass = bufferClass
        self._buffer.nameguard = nameguard
        self._ast_stack = []
        self._concrete_stack = [None]
        self._rule_stack = []
        self._cut_stack = [False]
        if not self._trace:
            self.trace = lambda x: ()
            self.trace_event = lambda x: ()

    def parse(self, rule_name):
        try:
            self._ast_stack = []
            self._push_ast()
            self._concrete_stack = [None]
            self._rule_stack = []
            self._cut_stack = [False]
            return self._call(rule_name, rule_name)
        finally:
            del self._ast_stack[1:]

    @property
    def ast(self):
        return self._ast_stack[-1]

    @ast.setter
    def ast(self, value):
        self._ast_stack[-1] = value

    def _push_ast(self):
        self._ast_stack.append(AST())

    def _pop_ast(self):
        return self._ast_stack.pop()

    def _add_ast_node(self, name, node, force_list=False):
        if name is not None:  # and node:
            self.ast.add(name, node, force_list)
        self._add_cst_node(node)
        return node

    def result(self):
        return self.ast

    @property
    def cst(self):
        return self._concrete_stack[-1]

    def _push_cst(self):
        self._concrete_stack.append(None)

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

    def _pop_cst(self):
        return self._concrete_stack.pop()

    def rulestack(self):
        stack = '.'.join(self._rule_stack)
        if len(stack) > 60:
            stack = '...' + stack[-60:]
        return stack

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


    def _call(self, name, node_name=None, force_list=False):
        self._rule_stack.append(name)
        if name[0].islower():
            self._next_token()
        pos = self._pos
        try:
            self.trace_event('ENTER ')
            result, newpos = self._invoke_rule(name, pos)
            self._goto(newpos)
            self.trace_event('SUCCESS')
            self._add_ast_node(node_name, result, force_list)
            return result
        except FailedParse:
            self.trace_event('FAILED')
            self._goto(pos)
            raise
        finally:
            self._rule_stack.pop()

    @memoize
    def _invoke_rule(self, name, pos):
        rule = self._find_rule(name)
        self._push_ast()
        self._push_cst()
        try:
            rule()
            node = self.ast
            if node:
                if not self._simple:
                    node.add('parseinfo', AST(rule=name, pos=pos))
            else:
                node = self.cst
        finally:
            self._pop_cst()
            self._pop_ast()
        semantic_rule = self._find_semantic_rule(name)
        if semantic_rule:
            node = semantic_rule(node)
        return (node, self._pos)

    def _token(self, token, node_name=None, force_list=False):
        self._next_token()
        if self._buffer.match(token) is None:
            raise FailedToken(self._buffer, token)
        self.trace_match(token, node_name)
        self._add_ast_node(node_name, token, force_list)
        return token

    def _try(self, token, node_name=None, force_list=False):
        self._next_token()
        if self._buffer.match(token) is not None:
            self.trace_match(token, node_name)
            self._add_ast_node(node_name, token, force_list)
            return True


    def _pattern(self, pattern, node_name=None, force_list=False):
        token = self._buffer.matchre(pattern)
        if token is None:
            raise FailedPattern(self._buffer, pattern)
        self.trace_match(token, pattern)
        self._add_ast_node(node_name, token, force_list)
        return token

    def _try_pattern(self, pattern, node_name=None, force_list=False):
        token = self._buffer.matchre(pattern)
        if token is None:
            return None
        self.trace_match(token)
        self._add_ast_node(node_name, token, force_list)
        return token

    def _find_rule(self, name):
        rule = getattr(self, '_%s_' % name, None)
        if rule is None or not isinstance(rule, type(self._find_rule)):
            raise FailedRef(self._buffer, name)
        return rule

    def _find_semantic_rule(self, name):
        result = getattr(self, name, None)
        if result is None or not isinstance(result, type(self._find_rule)):
            return None
        return result

    def error(self, item, etype=FailedParse):
        raise etype(self._buffer, item)

    def trace(self, msg, *params):
        if self._trace:
            print(msg % params, file=sys.stderr)

    def trace_event(self, event):
        self.trace('%s   %s \n\t%s', event, self.rulestack(), self._buffer.lookahead())

    def trace_match(self, token, name=''):
        if self._trace:
            self.trace('MATCHED <%s> /%s/\n\t%s', token, name, self._buffer.lookahead())

    @contextmanager
    def _option(self):
        p = self._pos
        try:
            self._push_ast()
            try:
                yield
                ast = self.ast
            finally:
                self._pop_ast()
            self.ast.update(ast)
        except FailedCut as e:
            self._goto(p)
            raise e.nested
        except FailedParse:
            self._goto(p)

    _optional = _option

    @contextmanager
    def _repeat_context(self):
        p = self._pos
        try:
            yield
        except FailedParse:
            self._goto(p)
            raise

    def _repeat_iterator(self, f):
        while 1:
            p = self._pos
            try:
                value = f()
                if value is not None:
                    yield value
            except FailedCut as e:
                raise e.nested
            except FailedParse:
                self._goto(p)
                raise StopIteration()

    def _repeat(self, f, plus=False):
        if plus:
            return [f()] + list(self._repeat_iterator(f))
        else:
            return list(self._repeat_iterator(f))

    def _eof(self):
        return self._buffer.atend()

    def _eol(self):
        return self._buffer.ateol()

    def _check_eof(self):
        self._next_token()
        if not self._buffer.atend():
            raise FailedParse(self._buffer, 'expecting end of file')

    def _cut(self):
        self._cut_stack[-1] = True

    def _push_cut(self):
        self._cut_stack.append(False)

    def _pop_cut(self):
        return self._cut_stack.pop()

    @contextmanager
    def _sequence(self):
        self._push_cut()
        try:
            yield
        except FailedParse as e:
            if self._cut():
                self.error(e, FailedCut)
            raise e
        finally:
            self._pop_cut()

    @contextmanager
    def _group(self):
        self._push_cst()
        try:
            yield
            node = self.cst
        finally:
            self._pop_cst()
        self._add_cst_node(node)

    @contextmanager
    def _if(self):
        p = self._pos
        try:
            yield
        finally:
            self._goto(p)

    @contextmanager
    def _ifnot(self):
        p = self._pos
        try:
            yield
        except FailedParse:
            self._goto(p)
            pass
        else:
            self._goto(p)
            self.error('', etype=FailedLookahead)
