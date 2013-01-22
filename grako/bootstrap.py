# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from collections import OrderedDict
from .grammars import *  # @UnusedWildImport
from .parsing import *  # @UnusedWildImport

__all__ = ['GrakoParser', 'GrakoGrammarGenerator']

COMMENTS_RE = r'\(\*(?:.|\n)*?\*\)'

class GrakoParserBase(Parser):

    def __init__(self, grammar_name, text, trace=False):
        super(GrakoParserBase, self).__init__(text,
                comments_re=COMMENTS_RE,
                ignorecase=True,
                trace=trace)
        self.grammar_name = grammar_name

    def parse(self, rule='grammar'):
        return super(GrakoParserBase, self).parse(rule)

    def _void_(self):
        self._token('()', 'void')

    def _token_(self):
        with self._option():
            self._token("'")
            self._pattern(r"(?:[^'\\]|\\')*", 'token')
            self._token("'")
            return

        with self._option():
            self._token('"')
            self._pattern(r'(?:[^"\\]|\\")*', 'token')
            self._token('"')
            return

        raise FailedParse(self._buffer, '<"> or' + "<'>")

    def _word_(self):
        self._pattern(r'[A-Za-z0-9_]+', 'word')

    def _qualified_(self):
        self._pattern(r'[A-Za-z0-9_]+(?:\.[-_A-Za-z0-9]+)*', 'qualified')

    def _call_(self):
        self._call('word', 'call')

    def _pattern_(self):
        self._token('?/')
        self._pattern(r'(.*?)(?=/\?)', 'pattern')
        self._token('/?')

    def _cut_(self):
        self._token('>>', 'cut')

    def _eof_(self):
        self._token('$')

    def _subexp_(self):
        self._token('(')
        self._call('expre', 'exp')
        self._token(')')

    def _optional_(self):
        self._token('[')
        self._call('expre', 'optional')
        self._token(']')

    def _plus_(self):
        if not self._try('-', 'symbol'):
            self._token('+', 'symbol')

    def _repeat_(self):
        self._token('{')
        self._call('expre', 'repeat')
        self._token('}')
        if not self._try('*'):
            try:
                self._call('plus', 'plus')
            except FailedParse:
                pass

    def _special_(self):
        self._token('?(')
        self._pattern(r'(.*)\)?', 'special')

    def _kif_(self):
        self._token('&')
        self._call('term', 'kif')

    def _knot_(self):
        self._token('!')
        self._call('term', 'knot')

    def _atom_(self):
        with self._option():
            self._call('void', 'atom')
            return
        with self._option():
            self._call('cut', 'atom')
            return
        with self._option():
            self._call('token', 'atom')
            return
        with self._option():
            self._call('call', 'atom')
            return
        with self._option():
            self._call('pattern', 'atom')
            return
        with self._option():
            self._call('eof', 'atom')
            return
        raise FailedParse(self._buffer, 'atom')


    def _term_(self):
        with self._option():
            self._call('atom', 'term')
            return
        with self._option():
            self._call('subexp', 'term')
            return
        with self._option():
            self._call('repeat', 'term')
            return
        with self._option():
            self._call('optional', 'term')
            return
        with self._option():
            self._call('special', 'term')
            return
        with self._option():
            self._call('kif', 'term')
            return
        with self._option():
            self._call('knot', 'term')
            return
        raise FailedParse(self._buffer, 'term')

    def _named_(self):
        name = self._call('qualified')
        if not self._try('+:', 'force_list'):
            self._token(':')
        self.ast.add('name', name)
        try:
            self._call('element', 'value')
        except FailedParse as e:
            raise FailedCut(self._buffer, e)

    def _element_(self):
        with self._option():
            self._call('named', 'element')
            return
        with self._option():
            self._call('term', 'element')
            return
        raise FailedParse(self._buffer, 'element')

    def _sequence_(self):
        self._call('element', 'sequence', True)
        f = lambda : self._call('element', 'sequence')
        for _ in self._repeat_iterator(f):
            pass

    def _choice_(self):
        self._call('sequence', 'options', True)
        while True:
            p = self._pos
            try:
                self._token('|')
                self._call('sequence', 'options')
            except FailedCut as e:
                self._goto(p)
                raise e.nested
            except FailedParse:
                self._goto(p)
                break

    def _expre_(self):
        self._call('choice', 'expre')

    def _rule_(self):
        p = self._pos
        try:
            ast_name = self._call('word')
            self._token(':')
            self.ast.add('ast_name', ast_name)
        except FailedParse:
            self._goto(p)
        self._call('word', 'name')
        self._token('=')
        self._call('expre', 'rhs')
        if not self._try(';'):
            self._token('.')

    def _grammar_(self):
        self._call('rule', 'rules')
        while True:
            p = self._pos
            try:
                self._call('rule', 'rules')
            except FailedParse:
                self._goto(p)
                break
        self._next_token()
        self._check_eof()


class AbstractGrakoParser(GrakoParserBase):
    def token(self, ast):
        return ast

    def word(self, ast):
        return ast

    def pattern(self, ast):
        return ast

    def cut(self, ast):
        return ast

    def void(self, ast):
        return ast

    def subexp(self, ast):
        return ast

    def optional(self, ast):
        return ast

    def repeat(self, ast):
        return ast

    def special(self, ast):
        return ast

    def kif(self, ast):
        return ast

    def knot(self, ast):
        return ast

    def atom(self, ast):
        return ast


    def term(self, ast):
        return ast.term

    def named(self, ast):
        return ast

    def element(self, ast):
        return ast

    def sequence(self, ast):
        return ast

    def choice(self, ast):
        return ast

    def expre(self, ast):
        return ast

    def rule(self, ast):
        return ast

    def grammar(self, ast):
        return ast


class GrakoParser(AbstractGrakoParser):

    def token(self, ast):
        return ast

    def word(self, ast):
        return ast

    def call(self, ast):
        return ast

    def pattern(self, ast):
        return ast

    def cut(self, ast):
        return ast

    def eof(self, ast):
        return ast

    def void(self, ast):
        return ast

    def subexp(self, ast):
        return simplify(ast.exp)

    def optional(self, ast):
        return ast

    def plus(self, ast):
        return ast

    def repeat(self, ast):
        return ast

    def special(self, ast):
        return ast

    def kif(self, ast):
        return ast

    def knot(self, ast):
        return ast

    def atom(self, ast):
        return ast.atom

    def term(self, ast):
        return ast.term

    def named(self, ast):
        return ast

    def element(self, ast):
        return simplify(ast.element)

    def sequence(self, ast):
        return simplify(ast.sequence)

    def choice(self, ast):
        if len(ast.options) == 1:
            return simplify(ast.options)
        return ast

    def expre(self, ast):
        return simplify(ast.expre)

    def rule(self, ast):
        return ast

    def grammar(self, ast):
        return ast


class GrakoGrammarGenerator(AbstractGrakoParser):

    def __init__(self, grammar_name, text, trace=False):
        super(GrakoGrammarGenerator, self).__init__(grammar_name, text, trace=trace)
        self.rules = OrderedDict()

    def token(self, ast):
        return TokenGrammar(ast.token)

    def word(self, ast):
        return ast.word

    def qualified(self, ast):
        return ast.qualified

    def call(self, ast):
        return RuleRefGrammar(ast.call)

    def pattern(self, ast):
        return PatternGrammar(ast.pattern)

    def cut(self, ast):
        return CutGrammar()

    def eof(self, ast):
        return EOFGrammar()

    def void(self, ast):
        return VoidGrammar()

    def subexp(self, ast):
        return GroupGrammar(ast.exp)

    def optional(self, ast):
        return OptionalGrammar(ast.optional)

    def plus(self, ast):
        return ast

    def repeat(self, ast):
        if 'plus' in ast:
            return RepeatOneGrammar(ast.repeat)
        return RepeatGrammar(ast.repeat)

    def special(self, ast):
        return SpecialGrammar(ast.special)

    def kif(self, ast):
        return LookaheadGrammar(ast.kif)

    def knot(self, ast):
        return LookaheadNotGrammar(ast.knot)

    def atom(self, ast):
        return ast.atom

    def term(self, ast):
        return ast.term

    def named(self, ast):
        return NamedGrammar(ast.name, ast.value, 'force_list' in ast)

    def element(self, ast):
        return ast.element

    def sequence(self, ast):
        if len(ast.sequence) == 1:
            return simplify(ast.sequence)
        return SequenceGrammar(ast.sequence)

    def choice(self, ast):
        if len(ast.options) == 1:
            return ast.options[0]
        return ChoiceGrammar(ast.options)

    def expre(self, ast):
        return ast.expre

    def rule(self, ast):
        ast_name = ast.ast_name
        name = ast.name
        rhs = ast.rhs
        if not name in self.rules:
            rule = RuleGrammar(name, rhs, ast_name)
            self.rules[name] = rule
        else:
            rule = self.rules[name]
            if isinstance(rule.exp, ChoiceGrammar):
                rule.exp.options.append(rhs)
            else:
                rule.exp = ChoiceGrammar([rule.exp, rhs])
        return rule

    def grammar(self, ast):
        return Grammar(self.grammar_name, list(self.rules.values()))

