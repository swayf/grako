# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import parser_base
from model import *  # @UnusedWildImport

class RegexpParser(parser_base.RegexParserBase):
    def __init__(self, **kwargs):
        super(RegexpParser, self).__init__(**kwargs)
        self._count = 0

    def START(self, ast):
        return Regexp(ast.expre)

    def CHOICE(self, ast):
        return Choice(ast.opts)

    def SEQUENCE(self, ast):
        if not ast.terms:
            return Empty()
        elif len(ast.terms) < 2:
            return ast.terms[0]
        else:
            return Sequence(ast.terms)

    def CLOSURE(self, ast):
        return Closure(ast.atom)

    def SUBEXP(self, ast):
        return ast.expre

    def LITERAL(self, ast):
        return Literal(ast)

def translate(regexp, trace=False):
    parser = RegexpParser(trace=trace)
    model = parser.parse(regexp, 'START')
    model.set_rule_numbers()
    return model.render()
