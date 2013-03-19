# -*- coding: utf-8 -*-
"""
Implements parsing of Grako's EBNF idiom for grammars, and grammar model
creation using the .grammars module.

GrakoParserRoot is the bootstrap parser. It uses the facilities of parsing.Parser
as generated parsers do, but it does not conform to the patterns in the generated
code. Why? Because having Grako bootstrap itself from its grammar would be cool,
but very bad engineering. GrakoParserRoot is hand-crafted.

The GrakoGrammarGenerator class, a descendant of GrakoParserRoot constructs
a model of the grammar using semantic actions the model elements defined
in the .grammars module.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
from collections import OrderedDict
from .parsing import Parser
from .util import simplify
from .grammars import (ChoiceGrammar,
                       CutGrammar,
                       EOFGrammar,
                       Grammar,
                       GroupGrammar,
                       LookaheadGrammar,
                       LookaheadNotGrammar,
                       NamedGrammar,
                       OptionalGrammar,
                       OverrideGrammar,
                       PatternGrammar,
                       RepeatGrammar,
                       RepeatOneGrammar,
                       RuleGrammar,
                       RuleRefGrammar,
                       SequenceGrammar,
                       SpecialGrammar,
                       TokenGrammar,
                       VoidGrammar)
from .exceptions import (FailedCut,
                         FailedParse)

__all__ = ['GrakoParser', 'GrakoGrammarGenerator']

COMMENTS_RE = r'\(\*(?:.|\n)*?\*\)'


class GrakoParserRoot(Parser):

    def __init__(self, grammar_name, trace=False):
        super(GrakoParserRoot, self).__init__(comments_re=COMMENTS_RE,
                                              ignorecase=True,
                                              trace=trace)
        self.grammar_name = grammar_name

    def parse(self, text, rule='grammar', filename=None):
        return super(GrakoParserRoot, self).parse(text, rule, filename=filename)

    def _void_(self):
        self._token('()', 'void')

    def _token_(self):
        with self._option():
            self._token("'")
            self._cut()
            self._pattern(r"(?:[^'\\]|\\')*", 'token')
            self._token("'")
            return

        with self._option():
            self._token('"')
            self._cut()
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
        self._cut()
        self._pattern(r'(.*?)(?=/\?)', 'pattern')
        self._token('/?')

    def _cut_(self):
        self._token('>>', 'cut')
        self._cut()

    def _eof_(self):
        self._token('$')
        self._cut()

    def _subexp_(self):
        self._token('(')
        self._cut()
        self._call('expre', 'exp')
        self._token(')')

    def _optional_(self):
        self._token('[')
        self._cut()
        self._call('expre', 'optional')
        self._token(']')

    def _plus_(self):
        if not self._try_token('-', 'symbol'):
            self._token('+', 'symbol')

    def _repeat_(self):
        self._token('{')
        self._cut()
        self._call('expre', 'repeat')
        self._token('}')
        if not self._try_token('*'):
            try:
                self._call('plus', 'plus')
            except FailedParse:
                pass

    def _special_(self):
        self._token('?(')
        self._cut()
        self._pattern(r'(.*)\)?', 'special')

    def _kif_(self):
        self._token('&')
        self._cut()
        self._call('term', 'kif')

    def _knot_(self):
        self._token('!')
        self._cut()
        self._call('term', 'knot')

    def _atom_(self):
        with self._option():
            self._call('void', 'atom')
            self._cut()
            return
        with self._option():
            self._call('cut', 'atom')
            self._cut()
            return
        with self._option():
            self._call('token', 'atom')
            self._cut()
            return
        with self._option():
            self._call('call', 'atom')
            self._cut()
            return
        with self._option():
            self._call('pattern', 'atom')
            self._cut()
            return
        with self._option():
            self._call('eof', 'atom')
            self._cut()
            return
        raise FailedParse(self._buffer, 'atom')

    def _term_(self):
        with self._option():
            self._call('atom', 'term')
            self._cut()
            return
        with self._option():
            self._call('subexp', 'term')
            self._cut()
            return
        with self._option():
            self._call('repeat', 'term')
            self._cut()
            return
        with self._option():
            self._call('optional', 'term')
            self._cut()
            return
        with self._option():
            self._call('special', 'term')
            self._cut()
            return
        with self._option():
            self._call('kif', 'term')
            self._cut()
            return
        with self._option():
            self._call('knot', 'term')
            self._cut()
            return
        raise FailedParse(self._buffer, 'term')

    def _named_(self):
        name = self._call('qualified')
        if not self._try_token('+:', 'force_list'):
            self._token(':')
        self._cut()
        self.ast.add('name', name)
        try:
            self._call('element', 'value')
        except FailedParse as e:
            raise FailedCut(self._buffer, e)

    def _override_(self):
        self._token('@')
        self._cut()
        try:
            self._call('element', '@')
        except FailedParse as e:
            raise FailedCut(self._buffer, e)

    def _element_(self):
        with self._option():
            self._call('named', 'element')
            self._cut()
            return
        with self._option():
            self._call('override', 'element')
            self._cut()
            return
        with self._option():
            self._call('term', 'element')
            self._cut()
            return
        raise FailedParse(self._buffer, 'element')

    def _sequence_(self):
        self._call('element', 'sequence', True)
        f = lambda: self._call('element', 'sequence', True)
        self._repeater(f)

    def _choice_(self):
        self._call('sequence', 'options', True)
        while True:
            p = self._pos
            try:
                with self._try():
                    self._token('|')
                    self._cut()
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
        # FIXME: This doesn't work, and it's usefullness is doubtfull.
        # p = self._pos
        # try:
        #     ast_name = self._call('word')
        #     self._token(':')
        #     self.ast.add('ast_name', str(ast_name))
        # except FailedParse:
        #     self._goto(p)
        self._call('word', 'name')
        self._token('=')
        self._cut()
        self._call('expre', 'rhs')
        if not self._try_token(';'):
            self._token('.')

    def _grammar_(self):
        self._call('rule', 'rules')
        while True:
            p = self._pos
            try:
                with self._try():
                    self._call('rule', 'rules')
                    self._cut()
            except FailedParse:
                self._goto(p)
                break
        self._next_token()
        self._check_eof()


class GrakoParserBase(GrakoParserRoot):
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

    def override(self, ast):
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


class GrakoParser(GrakoParserBase):

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

    def override(self, ast):
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


class GrakoGrammarGenerator(GrakoParserBase):

    def __init__(self, grammar_name, trace=False):
        super(GrakoGrammarGenerator, self).__init__(grammar_name, trace=trace)
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

    def override(self, ast):
        return OverrideGrammar(ast)

    def element(self, ast):
        return ast.element

    def sequence(self, ast):
        seq = ast.sequence
        assert isinstance(seq, list), str(seq)
        if len(seq) == 1:
            return simplify(seq)
        return SequenceGrammar(seq)

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
            rule = RuleGrammar(name, rhs, ast_name=ast_name)
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
