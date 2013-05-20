# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from .rendering import NodeVisitor


class GrammarVisitor(NodeVisitor):
    def visit_grammar(self, g, vrules):
        return g

    def visit_rule(self, r, vexp):
        return r

    def visit_rule_ref(self, rr):
        return rr

    def visit_special(self, s):
        return s

    def visit_override(self, o, vexp):
        return o

    def visit_named(self, n, vexp):
        return n

    def visit_cut(self, c):
        return c

    def visit_optional(self, o, vexp):
        return o

    def visit_repeat(self, r, vexp):
        return r

    def visit_repeat_plus(self, r, vexp):
        return r

    def visit_group(self, g, vexp):
        return g

    def visit_choice(self, c, vopt):
        return c

    def visit_sequence(self, s, vseq):
        return s

    def visit_lookahead(self, l, vexp):
        return l

    def visit_lookahead_not(self, l, vexp):
        return l

    def visit_pattern(self, p):
        return p

    def visit_token(self, t):
        return t

    def visit_void(self, v):
        return v

    def visit_fail(self, f):
        return f

    def visit_eof(self, e):
        return e

    def visit_Grammar(self, g):
        return self.visit_grammar(g, [r.accept(self) for r in g.rules])

    def visit_Rule(self, r):
        return self.visit_rule(r, r.exp.accept(self))

    def visit_RuleRef(self, r):
        return self.visit_rule_ref(r)

    def visit_Special(self, s):
        return self.visit_special(s)

    def visit_Override(self, o):
        return self.visit_override(o, o.exp.accept(self))

    def visit_Named(self, n):
        return self.visit_named(n, n.exp.accept(self))

    def visit_Cut(self, c):
        return self.visit_cut(c)

    def visit_Optional(self, o):
        return self.visit_optional(o, o.exp.accept(self))

    def visit_Repeat(self, r):
        return self.visit_repeat(r, r.exp.accept(self))

    def visit_RepeatPlus(self, r):
        return self.visit_repeat_plus(r, r.exp.accept(self))

    def visit_Group(self, g):
        return self.visit_group(g, g.exp.accept(self))

    def visit_Choice(self, c):
        return self.visit_choice(c, [o.accept(self) for o in c.options])

    def visit_Sequence(self, s):
        return self.visit_sequence(s, [e.accept(self) for e in s.sequence])

    def visit_Lookahead(self, l):
        return self.visit_lookahead(l, l.exp.accept(self))

    def visit_LookaheadNot(self, l):
        return self.visit_lookahead_not(l, l.exp.accept(self))

    def visit_Pattern(self, p):
        return self.visit_pattern(p)

    def visit_Token(self, t):
        return self.visit_token(t)

    def visit_Void(self, v):
        return self.visit_void(v)

    def visit_Fail(self, f):
        return self.visit_fail(f)

    def visit_EOF(self, e):
        return self.visit_eof(e)
