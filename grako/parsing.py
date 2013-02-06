# -*- coding: utf-8 -*-
"""
Parser is the base class for generated parsers and for the bootstrap parser
(the parser that parses Grako grammars).

Parser does memoization at the rule invocation level, and provides the
decorators, context managers, and iterators needed to make generated parsers
simple.

Parser is also in charge of dealing with comments, with the help of
the .buffering module.

Parser.parse() will take the text to parse directly, or an instance of the
.buffeing.Buffer class.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
from contextlib import contextmanager
from . import buffering
from .exceptions import *  # @UnusedWildImport
from .ast import AST
from .contexts import ParseContext


class AbstractParserMixin(object):
    def _find_semantic_rule(self, name):
        result = getattr(self, name, None)
        if result is None or not isinstance(result, type(self._find_rule)):
            raise MissingSemanticFor(name)
        return result


class Parser(ParseContext):

    def parse(self, text, rule_name, filename=None):
        try:
            self._reset_context()
            if isinstance(text, buffering.Buffer):
                self._buffer = text
            else:
                self._buffer = self.bufferClass(text,
                                                filename=filename,
                                                whitespace=self.whitespace,
                                                ignorecase=self.ignorecase,
                                                nameguard=self.nameguard)
            self._push_ast()
            return self._call(rule_name, rule_name)
        finally:
            self._memoization_cache = dict()

    @classmethod
    def rule_list(cls):
        import inspect
        methods = inspect.getmembers(cls, predicate=inspect.ismethod)
        result = []
        for m in methods:
            name = m[0]
            if name[0] != '_' or name[-1] != '_':
                continue
            if not name[1:-1].isalnum():
                continue
            result.append(name[1:-1])
        return result

    def result(self):
        return self.ast

    def _call(self, name, node_name=None, force_list=False):
        self._rule_stack.append(name)
        if name[0].islower():
            self._next_token()
        pos = self._pos
        try:
            self._trace_event('ENTER ')
            node, newpos = self._invoke_rule(name, pos)
            self._goto(newpos)
            self._trace_event('SUCCESS')
            self._add_ast_node(node_name, node, force_list)
            self._add_cst_node(node)
            return node
        except FailedParse:
            self._trace_event('FAILED')
            self._goto(pos)
            raise
        finally:
            self._rule_stack.pop()

    def _invoke_rule(self, name, pos):
        key = (pos, name)
        cache = self._memoization_cache

        if key in cache:
            return cache[key]

        rule = self._find_rule(name)
        self._push_ast()
        try:
            rule()
            node = self.ast
            if not node:
                node = self.cst
            elif '@' in node:
                node = node['@']  # override the AST
            elif not self._simple:
                node.add('parseinfo',
                         AST(rule=name, pos=pos, endpos=self._pos)
                         )
        finally:
            self._pop_ast()
        semantic_rule = self._find_semantic_rule(name)
        if semantic_rule:
            node = semantic_rule(node)
        result = (node, self._pos)

        cache[key] = result
        return result

    def _token(self, token, node_name=None, force_list=False):
        self._next_token()
        if self._buffer.match(token) is None:
            raise FailedToken(self._buffer, token)
        self._trace_match(token, node_name)
        self._add_ast_node(node_name, token, force_list)
        self._add_cst_node(token)
        return token

    def _try(self, token, node_name=None, force_list=False):
        p = self._pos
        self._next_token()
        if self._buffer.match(token) is None:
            self._goto(p)
            return None
        self._trace_match(token, node_name)
        self._add_ast_node(node_name, token, force_list)
        self._add_cst_node(token)
        return token


    def _pattern(self, pattern, node_name=None, force_list=False):
        token = self._buffer.matchre(pattern)
        if token is None:
            raise FailedPattern(self._buffer, pattern)
        self._trace_match(token, pattern)
        self._add_ast_node(node_name, token, force_list)
        self._add_cst_node(token)
        return token

    def _try_pattern(self, pattern, node_name=None, force_list=False):
        p = self._pos
        token = self._buffer.matchre(pattern)
        if token is None:
            self._goto(p)
            return None
        self._trace_match(token)
        self._add_ast_node(node_name, token, force_list)
        self._add_cst_node(token)
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

    def _eof(self):
        return self._buffer.atend()

    def _eol(self):
        return self._buffer.ateol()

    def _check_eof(self):
        self._next_token()
        if not self._buffer.atend():
            raise FailedParse(self._buffer, 'Expecting end of text.')

    @contextmanager
    def _option(self):
        p = self._pos
        self._push_cut()
        try:
            self._push_ast()
            try:
                yield
                ast = self.ast
                cst = self.cst
            finally:
                self._pop_ast()
            self.ast.update(ast)
            self._extend_cst(cst)
        except FailedCut:
            raise
        except FailedParse as e:
            if self._is_cut_set():
                self._error(e, FailedCut)
            self._goto(p)
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

    def _repeat_iterator(self, f):
        while 1:
            p = self._pos
            self._push_cut()
            try:
                value = f()
                if value is not None:
                    yield value
            except FailedCut:
                raise
            except FailedParse as e:
                if self._is_cut_set():
                    self._error(e, FailedCut)
                self._goto(p)
                raise StopIteration()
            finally:
                self._pop_cut()

    def _repeat(self, f, plus=False):
        if plus:
            return [f()] + list(self._repeat_iterator(f))
        else:
            return list(self._repeat_iterator(f))

