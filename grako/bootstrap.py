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
from .parsing import Parser, rule_def
from .util import simplify_list
from . import grammars
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

    @rule_def
    def void(self):
        self._token('()', 'void')

    @rule_def
    def token(self):
        self.TOKEN()

    @rule_def
    def TOKEN(self):
        with self._option():
            self._token("'")
            self._cut()
            self._pattern(r"(?:[^'\n]|\\'|\\\\)*", '@')
            self._token("'")
            return

        with self._option():
            self._token('"')
            self._cut()
            self._pattern(r'(?:[^"\n]|\\"|\\\\)*', '@')
            self._token('"')
            return

        raise FailedParse(self._buffer, '<"> or' + "<'>")

    @rule_def
    def word(self):
        self._pattern(r'[A-Za-z0-9_]+')

    @rule_def
    def qualified(self):
        self._pattern(r'[A-Za-z0-9_]+(?:\.[-_A-Za-z0-9]+)*', 'qualified')

    @rule_def
    def call(self):
        self.word()

    @rule_def
    def pattern(self):
        self.PATTERN()

    @rule_def
    def PATTERN(self):
        self._token('?/')
        self._cut()
        self._pattern(r'(.*?)(?=/\?)', '@')
        self._token('/?')

    @rule_def
    def cut(self):
        self._token('>>', 'cut')
        self._cut()

    @rule_def
    def eof(self):
        self._token('$')
        self._cut()

    @rule_def
    def subexp(self):
        self._token('(')
        self._cut()
        e = self.expre()
        self.ast['@'] = e
        self._token(')')

    @rule_def
    def optional(self):
        self._token('[')
        self._cut()
        e = self.expre()
        self.ast['@'] = e
        self._cut()
        self._token(']')

    @rule_def
    def plus(self):
        if not self._try_token('-', 'symbol'):
            self._token('+', 'symbol')

    @rule_def
    def repeat(self):
        self._token('{')
        self._cut()
        e = self.expre()
        self.ast['repeat'] = e
        self._token('}')
        if not self._try_token('*'):
            try:
                e = self.plus()
                self.ast['plus'] = e
            except FailedParse:
                pass

    @rule_def
    def special(self):
        self._token('?(')
        self._cut()
        self._pattern(r'(.*)\)?', 'special')

    @rule_def
    def kif(self):
        self._token('&')
        self._cut()
        e = self.term()
        self.ast['@'] = e

    @rule_def
    def knot(self):
        self._token('!')
        self._cut()
        e = self.term()
        self.ast['@'] = e

    @rule_def
    def atom(self):
        with self._option():
            self.void()
            self._cut()
            return
        with self._option():
            self.cut()
            self._cut()
            return
        with self._option():
            self.token()
            self._cut()
            return
        with self._option():
            self.call()
            self._cut()
            return
        with self._option():
            self.pattern()
            self._cut()
            return
        with self._option():
            self.eof()
            self._cut()
            return
        self._error('expecting atom')

    @rule_def
    def term(self):
        with self._option():
            self.atom()
            self._cut()
            return
        with self._option():
            self.subexp()
            self._cut()
            return
        with self._option():
            self.repeat()
            self._cut()
            return
        with self._option():
            self.optional()
            self._cut()
            return
        with self._option():
            self.special()
            self._cut()
            return
        with self._option():
            self.kif()
            self._cut()
            return
        with self._option():
            self.knot()
            self._cut()
            return
        self._error('expecting term')

    @rule_def
    def named(self):
        name = self.qualified()
        if not self._try_token('+:', 'force_list'):
            self._token(':')
        self._cut()
        self.ast.add('name', name)
        e = self.element()
        self.ast['value'] = e

    @rule_def
    def override(self):
        self._token('@')
        self._cut()
        e = self.element()
        self.ast['@'] = e

    @rule_def
    def element(self):
        with self._option():
            self.named()
            self._cut()
            return
        with self._option():
            self.override()
            self._cut()
            return
        with self._option():
            self.term()
            self._cut()
            return
        self._error('element')

    @rule_def
    def sequence(self):
        @self._closure_plus
        def callelm():
            e = self.element()
            self.ast.add_list('sequence', e)
        callelm()

    @rule_def
    def choice(self):
        @self._closure
        def options():
            self._token('|')
            self._cut()
            e = self.sequence()
            self.ast.add_list('options', e)

        e = self.sequence()
        self.ast.add_list('options', e)
        options()

    @rule_def
    def expre(self):
        self.choice()

    @rule_def
    def rule(self):
        # FIXME: This doesn't work, and it's usefullness is doubtfull.
        # p = self._pos
        # try:
        #     ast_name = self.word()
        #     self._token(':')
        #     self.ast.add('ast_name', str(ast_name))
        # except FailedParse:
        #     self._goto(p)
        e = self.word()
        self.ast['name'] = e
        self._cut()
        self._token('=')
        self._cut()
        e = self.expre()
        self.ast['rhs'] = e
        if not self._try_token(';'):
            try:
                self._token('.')
            except FailedParse:
                self._error('expecting one of: ; .')

    @rule_def
    def grammar(self):
        @self._closure_plus
        def rules():
            e = self.rule()
            self.ast['rules'] = e
        rules()
        self._next_token()
        self._check_eof()


class GrakoASTSemantics(object):

    def subexp(self, ast):
        return simplify_list(ast.exp)

    def element(self, ast):
        return simplify_list(ast)

    def sequence(self, ast):
        return simplify_list(ast.sequence)

    def choice(self, ast):
        if len(ast.options) == 1:
            return simplify_list(ast.options)
        return ast


class GrakoParser(GrakoParserBase):
    def __init__(self, grammar_name, semantics=None, **kwargs):
        if semantics is None:
            semantics = GrakoASTSemantics()
        super(GrakoParser, self).__init__(semantics=semantics, **kwargs)


class GrakoGrammarGenerator(GrakoParserBase):
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
        return grammars.Token(ast)

    def word(self, ast):
        return ast

    def qualified(self, ast):
        return ast.qualified

    def call(self, ast):
        return grammars.RuleRef(ast)

    def pattern(self, ast):
        return grammars.Pattern(ast)

    def cut(self, ast):
        return grammars.Cut()

    def eof(self, ast):
        return grammars.EOF()

    def void(self, ast):
        return grammars.Void()

    def subexp(self, ast):
        return grammars.Group(ast)

    def optional(self, ast):
        return grammars.Optional(ast)

    def plus(self, ast):
        return ast

    def repeat(self, ast):
        if ast.plus:
            return grammars.RepeatPlus(ast.repeat)
        return grammars.Repeat(ast.repeat)

    def special(self, ast):
        return grammars.Special(ast.special)

    def kif(self, ast):
        return grammars.Lookahead(ast)

    def knot(self, ast):
        return grammars.LookaheadNot(ast)

    def atom(self, ast):
        return ast

    def term(self, ast):
        return ast

    def named(self, ast):
        if ast.force_list:
            return grammars.NamedList(ast.name, ast.value)
        else:
            return grammars.Named(ast.name, ast.value)

    def override(self, ast):
        return grammars.Override(ast)

    def element(self, ast):
        return ast

    def sequence(self, ast):
        seq = ast.sequence
        assert isinstance(seq, list), str(seq)
        if len(seq) == 1:
            return simplify_list(seq)
        return grammars.Sequence(seq)

    def choice(self, ast):
        if len(ast.options) == 1:
            return ast.options[0]
        return grammars.Choice(ast.options)

    def expre(self, ast):
        return ast

    def rule(self, ast):
        ast_name = ast.ast_name
        name = ast.name
        rhs = ast.rhs
        if not name in self.rules:
            rule = grammars.Rule(name, rhs, ast_name=ast_name)
            self.rules[name] = rule
        else:
            rule = self.rules[name]
            if isinstance(rule.exp, grammars.Choice):
                rule.exp.options.append(rhs)
            else:
                rule.exp = grammars.Choice([rule.exp, rhs])
        return rule

    def grammar(self, ast):
        return grammars.Grammar(self.grammar_name, list(self.rules.values()))
