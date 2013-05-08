# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from grako import grammars as model


class ANTLRSemantics(object):
    def __init__(self, name):
        self.name = name

    def grammar(self, ast):
        return model.Grammar(self.name, ast.rules)

    def rule(self, ast):
        return model.Rule(ast.name, ast.exp)

    def alternatives(self, ast):
        options = [o for o in ast.options if o is not None]
        if len(options) == 1:
            return options[0]
        else:
            return model.Choice(options)

    def elements(self, ast):
        elements = [e for e in ast if e is not None]
        if not elements:
            return model.Void()
        elif len(elements) == 1:
            return elements[0]
        else:
            return model.Sequence(elements)

    def predicate_or_action(self, ast):
        def flatten(s):
            if s is None:
                return ''
            elif isinstance(s, list):
                return ''.join(flatten(e) for e in s if e is not None)
            else:
                return s
        text = flatten(ast)
        return model.Comment(text)

    def named(self, ast):
        return model.Named(ast.name, ast.exp, ast.force_list)

    def syntatic_predicate(self, ast):
        return model.Lookahead(ast)

    def optional(self, ast):
        return model.Optional(ast)

    def closure(self, ast):
        return model.Repeat(ast)

    def positive_closure(self, ast):
        return model.RepeatPlus(ast)

    def negative(self, ast):
        neg = model.LookaheadNot(ast)
        any = model.Pattern('.')
        return model.Sequence([neg, any])

    def range(self, ast):
        return model.Pattern('[%s-%s]' % (ast.first, ast.last))

    def non_terminal(self, ast):
        return model.RuleRef(ast)

    def any(self, ast):
        return model.Pattern('\w+|\S+')

    def string(self, ast):
        text = ast
        if isinstance(text, list):
            text = ''.join(text)
        return model.Token(text)

    def eof(self, ast):
        return model.EOF()
