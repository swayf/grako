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
from .buffering import Buffer
from .parsing import Parser, rule_def
from .exceptions import FailedParse
from .semantics import GrakoASTSemantics, GrakoSemantics

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
        with self._choice():
            with self._option():
                self._token("'")
                self._cut()
                self._pattern(r"(?:[^'\n]|\\'|\\\\)*", '@')
                self._token("'")

            with self._option():
                self._token('"')
                self._cut()
                self._pattern(r'(?:[^"\n]|\\"|\\\\)*', '@')
                self._token('"')
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
        self.expre()
        self.ast['@'] = self.last_node
        self._token(')')

    @rule_def
    def optional(self):
        self._token('[')
        self._cut()
        self.expre()
        self.ast['@'] = self.last_node
        self._cut()
        self._token(']')

    @rule_def
    def plus(self):
        if not self._try_token('-', 'symbol'):
            self._token('+', 'symbol')

    @rule_def
    def closure(self):
        self._token('{')
        self._cut()
        self.expre()
        self.ast['exp'] = self.last_node
        self._token('}')
        if not self._try_token('*'):
            try:
                self.plus()
                self.ast['plus'] = self.last_node
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
        self.term()
        self.ast['@'] = self.last_node

    @rule_def
    def knot(self):
        self._token('!')
        self._cut()
        self.term()
        self.ast['@'] = self.last_node

    @rule_def
    def atom(self):
        with self._choice():
            with self._option():
                self.void()
                self._cut()
            with self._option():
                self.cut()
                self._cut()
            with self._option():
                self.token()
                self._cut()
            with self._option():
                self.call()
                self._cut()
            with self._option():
                self.pattern()
                self._cut()
            with self._option():
                self.eof()
                self._cut()
            self._error('expecting atom')

    @rule_def
    def term(self):
        with self._choice():
            with self._option():
                self.atom()
                self._cut()
            with self._option():
                self.subexp()
                self._cut()
            with self._option():
                self.closure()
                self._cut()
            with self._option():
                self.optional()
                self._cut()
            with self._option():
                self.special()
                self._cut()
            with self._option():
                self.kif()
                self._cut()
            with self._option():
                self.knot()
                self._cut()
            self._error('expecting term')

    @rule_def
    def named(self):
        name = self.qualified()
        if not self._try_token('+:', 'force_list'):
            self._token(':')
        self._cut()
        self.ast.add('name', name)
        self.element()
        self.ast['value'] = self.last_node

    @rule_def
    def override(self):
        self._token('@')
        self._cut()
        self.element()
        self.ast['@'] = self.last_node

    @rule_def
    def element(self):
        with self._choice():
            with self._option():
                self.named()
                self._cut()
            with self._option():
                self.override()
                self._cut()
            with self._option():
                self.term()
                self._cut()
            self._error('element')

    @rule_def
    def sequence(self):
        @self._positive_closure
        def seq():
            self.element()
            self.ast.add_list('sequence', self.last_node)
        seq()

    @rule_def
    def choice(self):
        @self._closure
        def options():
            self._token('|')
            self._cut()
            self.sequence()
            self.ast.add_list('options', self.last_node)

        self.sequence()
        self.ast.add_list('options', self.last_node)
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
        self.word()
        self.ast['name'] = self.last_node
        self._cut()
        self._token('=')
        self._cut()
        self.expre()
        self.ast['rhs'] = self.last_node
        if not self._try_token(';'):
            try:
                self._token('.')
            except FailedParse:
                self._error('expecting one of: ; .')
        self._cut()

    @rule_def
    def grammar(self):
        @self._positive_closure
        def rules():
            self.rule()
            self.ast['rules'] = self.last_node
        rules()
        self._next_token()
        self._check_eof()


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
