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
from .buffering import Buffer
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
                       RepeatPlusGrammar,
                       RuleGrammar,
                       RuleRefGrammar,
                       SequenceGrammar,
                       SpecialGrammar,
                       TokenGrammar,
                       VoidGrammar)
from .exceptions import FailedParse

__all__ = ['GrakoParser', 'GrakoGrammarGenerator']

COMMENTS_RE = r'\(\*(?:.|\n)*?\*\)'


class GrakoParserBase(Parser):

    def parse(self, text, rule='grammar', filename=None, **kwargs):
        if not isinstance(text, Buffer):
            text = Buffer(text, comments_re=COMMENTS_RE, **kwargs)
        return super(GrakoParserBase, self).parse(text,
                                                  rule,
                                                  filename=filename,
                                                  **kwargs)

    def _void_(self):
        self._token('()', 'void')

    def _token_(self):
        self._call('TOKEN')

    def _TOKEN_(self):
        with self._option():
            self._token("'")
            self._cut()
            self._pattern(r"(?:[^'\\\n]|\\'|\\\\)*", '@')
            self._token("'")
            return

        with self._option():
            self._token('"')
            self._cut()
            self._pattern(r'(?:[^"\\\n]|\\"|\\\\)*', '@')
            self._token('"')
            return

        raise FailedParse(self._buffer, '<"> or' + "<'>")

    def _word_(self):
        self._pattern(r'[A-Za-z0-9_]+')

    def _qualified_(self):
        self._pattern(r'[A-Za-z0-9_]+(?:\.[-_A-Za-z0-9]+)*', 'qualified')

    def _call_(self):
        self._call('word')

    def _pattern_(self):
        self._call('PATTERN')

    def _PATTERN_(self):
        self._token('?/')
        self._cut()
        self._pattern(r'(.*?)(?=/\?)', '@')
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
        self._call('expre', '@')
        self._token(')')

    def _optional_(self):
        self._token('[')
        self._cut()
        self._call('expre', '@')
        self._cut()
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
            self._call('void')
            self._cut()
            return
        with self._option():
            self._call('cut')
            self._cut()
            return
        with self._option():
            self._call('token')
            self._cut()
            return
        with self._option():
            self._call('call')
            self._cut()
            return
        with self._option():
            self._call('pattern')
            self._cut()
            return
        with self._option():
            self._call('eof')
            self._cut()
            return
        self._error('expecting atom')

    def _term_(self):
        with self._option():
            self._call('atom')
            self._cut()
            return
        with self._option():
            self._call('subexp')
            self._cut()
            return
        with self._option():
            self._call('repeat')
            self._cut()
            return
        with self._option():
            self._call('optional')
            self._cut()
            return
        with self._option():
            self._call('special')
            self._cut()
            return
        with self._option():
            self._call('kif')
            self._cut()
            return
        with self._option():
            self._call('knot')
            self._cut()
            return
        self._error('expecting term')

    def _named_(self):
        name = self._call('qualified')
        if not self._try_token('+:', 'force_list'):
            self._token(':')
        self._cut()
        self.ast.add('name', name)
        self._call('element', 'value')

    def _override_(self):
        self._token('@')
        self._cut()
        self._call('element', '@')

    def _element_(self):
        with self._option():
            self._call('named')
            self._cut()
            return
        with self._option():
            self._call('override')
            self._cut()
            return
        with self._option():
            self._call('term')
            self._cut()
            return
        self._error('element')

    def _sequence_(self):
        self._call('element', 'sequence', True)
        f = lambda: self._call('element', 'sequence', True)
        self._repeater(f)

    def _choice_(self):
        def options():
            self._token('|')
            self._cut()
            self._call('sequence', 'options')

        self._call('sequence', 'options', True)
        self._repeat(options, False)

    def _expre_(self):
        self._call('choice')

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
        self._cut()
        self._token('=')
        self._cut()
        self._call('expre', 'rhs')
        if not self._try_token(';'):
            try:
                self._token('.')
            except FailedParse:
                self._error('expecting one of: ; .')

    def _grammar_(self):
        self._call('rule', 'rules')
        f = lambda: self._call('rule', 'rules')
        self._repeat(f, True)
        self._next_token()
        self._check_eof()


class GrakoParser(GrakoParserBase):

    def subexp(self, ast):
        return simplify(ast.exp)

    def element(self, ast):
        return simplify(ast)

    def sequence(self, ast):
        return simplify(ast.sequence)

    def choice(self, ast):
        if len(ast.options) == 1:
            return simplify(ast.options)
        return ast


class GrakoGrammarGenerator(GrakoParser):
    def __init__(self, grammar_name, semantics=None, **kwargs):
        if semantics is None:
            semantics = GrakoSemantics(grammar_name)
        super(GrakoGrammarGenerator, self).__init__(semantics=semantics, **kwargs)


class GrakoSemantics(object):
    def __init__(self, grammar_name):
        super(GrakoSemantics, self).__init__()
        self.grammar_name = grammar_name
        self.rules = OrderedDict()

    def token(self, ast):
        return TokenGrammar(ast)

    def word(self, ast):
        return ast

    def qualified(self, ast):
        return ast.qualified

    def call(self, ast):
        return RuleRefGrammar(ast)

    def pattern(self, ast):
        return PatternGrammar(ast)

    def cut(self, ast):
        return CutGrammar()

    def eof(self, ast):
        return EOFGrammar()

    def void(self, ast):
        return VoidGrammar()

    def subexp(self, ast):
        return GroupGrammar(ast)

    def optional(self, ast):
        return OptionalGrammar(ast)

    def plus(self, ast):
        return ast

    def repeat(self, ast):
        if ast.plus:
            return RepeatPlusGrammar(ast.repeat)
        return RepeatGrammar(ast.repeat)

    def special(self, ast):
        return SpecialGrammar(ast.special)

    def kif(self, ast):
        return LookaheadGrammar(ast.kif)

    def knot(self, ast):
        return LookaheadNotGrammar(ast.knot)

    def atom(self, ast):
        return ast

    def term(self, ast):
        return ast

    def named(self, ast):
        return NamedGrammar(ast.name, ast.value, 'force_list' in ast)

    def override(self, ast):
        return OverrideGrammar(ast)

    def element(self, ast):
        return ast

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
        return ast

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
