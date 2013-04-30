# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from grako import grammars as model


class ANTLRSemantics(object):
    def __init__(self, name):
        self.name = name

    def grammar(self, ast):
        return model.Grammar(self.name, ast.rules)

    def rule(self, ast):
        return model.RuleGrammar(ast.name, ast.exp)

    def alternatives(self, ast):
        options = [o for o in ast.options if o is not None]
        if len(options) == 1:
            return options[0]
        else:
            return model.ChoiceGrammar(options)

    def elements(self, ast):
        elements = [e for e in ast if e is not None]
        if not elements:
            return model.VoidGrammar()
        elif len(elements) == 1:
            return elements[0]
        else:
            return model.SequenceGrammar(elements)

    def predicate_or_action(self, ast):
        def flatten(s):
            if s is None:
                return ''
            elif isinstance(s, list):
                return ''.join(flatten(e) for e in s if e is not None)
            else:
                return s
        text = flatten(ast)
        return model.CommentGrammar(text)

    def named(self, ast):
        return model.NamedGrammar(ast.name, ast.exp, ast.force_list)

    def syntatic_predicate(self, ast):
        return model.LookaheadGrammar(ast)

    def optional(self, ast):
        return model.OptionalGrammar(ast)

    def closure(self, ast):
        return model.RepeatGrammar(ast)

    def positive_closure(self, ast):
        return model.RepeatPlusGrammar(ast)

    def negative(self, ast):
        neg = model.LookaheadNotGrammar(ast)
        any = model.PatternGrammar('.')
        return model.SequenceGrammar([neg, any])

    def range(self, ast):
        return model.PatternGrammar('[%s-%s]' % (ast.first, ast.last))

    def non_terminal(self, ast):
        return model.RuleRefGrammar(ast)

    def any(self, ast):
        return model.PatternGrammar('\w+|\S+')

    def string(self, ast):
        text = ast
        if isinstance(text, list):
            text = ''.join(text)
        return model.TokenGrammar(text)
