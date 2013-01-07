# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import re
import logging
from copy import deepcopy
from .util import memoize, simplify, indent, trim
from .rendering import Renderer, render
from .buffering import Buffer
from .exceptions import *  # @UnusedWildImport
from .ast import AST

log = logging.getLogger('grako.grammars')

def check(result):
    assert isinstance(result, _Grammar), str(result)

def dot(x, y, k):
    return set([ (a + b)[:k] for a in x for b in y])

class Context(object):
    def __init__(self, rules, text):
        self.rules = {rule.name :rule for rule in rules}
        self.buf = Buffer(text)
        self.buf.goto(0)
        self._ast_stack = [AST()]
        self._rule_stack = []

    def goto(self, pos):
        self.buf.goto(pos)

    @property
    def pos(self):
        return self.buf.pos

    def rulestack(self):
        return '.'.join(self._rule_stack)

    @property
    def ast(self):
        return self._ast_stack[-1]

    def push_ast(self):
        self._ast_stack.append(AST())

    def pop_ast(self):
        return self._ast_stack.pop()

    def add_ast_node(self, name, node):
        if name is not None and node:
            self.ast.add(name, node)
        return node

class _Grammar(Renderer):
    def __init__(self):
        super(_Grammar, self).__init__()
        self._first_set = None

    def parse(self, ctx):
        return None

    @property
    def firstset(self, k=1):
        if self._first_set is None:
            self._first_set = self._first(k, {})
        return self._first_set

    def _first(self, k, F):
        return set()


class EOFGrammar(_Grammar):
    def parse(self, ctx):
        if not ctx.buf.atend():
            raise FailedParse(ctx.buf, '<EOF>')

    template = 'self._eol()'


class _DecoratorGrammar(_Grammar):
    def __init__(self, exp):
        assert isinstance(exp, _Grammar), str(exp)
        super(_DecoratorGrammar, self).__init__()
        self.exp = exp

    def parse(self, ctx):
        return self.exp.parse(ctx)

    def _first(self, k, F):
        return self.exp._first(k, F)

    def __str__(self):
        return str(self.exp)

class GroupGrammar(_DecoratorGrammar):
    def __str__(self):
        return '(%s)' % str(self.exp).strip()

    def render_fields(self, fields):
        fields.update(
                      n=self.counter(),
                      exp=indent(render(self.exp))
                      )

    template = '''\
                def group{n}():
                {exp}
                    return exp
                exp = group{n}() # @UnusedVariable'''


class TokenGrammar(_Grammar):
    def __init__(self, token):
        super(TokenGrammar, self).__init__()
        self.token = token

    def parse(self, ctx):
        log.debug('token <%s>\n\t%s', self.token, ctx.buf.lookahead())
        result = ctx.buf.match(self.token)
        if result is None:
            raise FailedToken(ctx.buf, self.token)
        return result

    def _first(self, k, F):
        return set([(self.token,)])

    def __str__(self):
        if "'" in self.token:
            if '"' in self.token:
                return "'%s'" % self.token.encode('string-escape')
            else:
                return '"%s"' % self.token
        return "'%s'" % self.token

    def render_fields(self, fields):
        fields.update(token=self.token)

    template = "exp = self._token('{token}') # @UnusedVariable"


class PatternGrammar(_Grammar):
    def __init__(self, pattern):
        super(PatternGrammar, self).__init__()
        self.pattern = pattern
        self._re = re.compile(pattern)

    def parse(self, ctx):
        log.debug('pattern <%s>\n\t%s', self.pattern, ctx.buf.lookahead())
        result = ctx.buf.matchre(self._re)
        if result is None:
            raise FailedPattern(ctx.buf, self.pattern)
        return result

    def _first(self, k, F):
        return set([(self.pattern,)])

    def __str__(self):
        return '?/%s/?' % self.pattern

    def render_fields(self, fields):
        fields.update(pattern=self.pattern)

    template = '''\
                exp = self._pattern(r'{pattern}') # @UnusedVariable
                '''


class SequenceGrammar(_Grammar):
    def __init__(self, sequence):
        super(SequenceGrammar, self).__init__()
        assert isinstance(sequence, list), str(sequence)
        self.sequence = sequence

    def parse(self, ctx):
        return simplify(self.parse_seq(ctx, self.sequence))

    def parse_seq(self, ctx, seq):
        log.debug('sequence %s', str([type(s) for s in self.sequence]))
        result = []
        for _i, s in enumerate(seq):
            tree = s.parse(ctx)
            result.append(tree)
        return [r for r in result if r is not None]

    def _first(self, k, F):
        result = {()}
        for s in self.sequence:
            result = dot(result, s._first(k, F), k)
        return result

    def __str__(self):
        return ' '.join(str(s).strip() for s in self.sequence)

    def render_fields(self, fields):
        fields.update(seq='\n'.join(trim(render(s)) for s in self.sequence))

    template = '''
                {seq}\
                '''


class ChoiceGrammar(_Grammar):
    def __init__(self, options):
        super(ChoiceGrammar, self).__init__()
        assert isinstance(options, list), repr(options)
        self.options = options

    def parse(self, ctx):
        items = []
        pos = ctx.pos
        for o in self.options:
            ctx.goto(pos)
            try:
                return o.parse(ctx)
            except FailedCut as e:
                raise e.nested
            except FailedParse as e:
                items.append(e.item)
        raise FailedParse(ctx.buf, 'one of {%s}' % ','.join(items))


    def _first(self, k, F):
        result = set()
        for o in self.options:
            result |= o._first(k, F)
        return result

    def __str__(self):
        return ' | '.join(str(o).strip() for o in self.options)

    def render_fields(self, fields):
        template = trim(self.option_template)
        options = [template.format(option=indent(render(o))) for o in self.options]
        options = '\n'.join(o for o in options)
        fields.update(n=self.counter(),
                      options=indent(options))

    def render(self):
        if len(self.options) == 1:
            return render(self.options[0])
        else:
            return super(ChoiceGrammar, self).render()

    option_template = '''\
                    try:
                    {option}
                        return exp
                    except FailedCut as e:
                        raise e.nested
                    except FailedParse:
                        self._goto(p)\
                    '''

    template = '''\
                def choice{n}():
                    p = self._pos
                {options}
                    self.error('no viable option')
                exp = choice{n}()
                '''


class RepeatGrammar(_DecoratorGrammar):
    def parse(self, ctx):
        log.debug('repeat %s', str(self.exp))
        result = []
        while True:
            p = ctx.buf.pos
            try:
                tree = self.exp.parse(ctx)
                if tree is not None:
                    result.append(tree)
            except FailedParse:
                ctx.buf.goto(p)
                break
        return simplify(result)


    def _first(self, k, F):
        result = {()}
        for _i in range(k):
            result = dot(result, self.exp._first(k, F), k)
        return {()} | result

    def __str__(self):
        return '{%s}' % str(self.exp)

    def render_fields(self, fields):
        fields.update(n=self.counter(),
                      innerexp=indent(render(self.exp), 3))

    def render(self):
        if {()} in self.exp.firstset:
            raise GrammarError('may repeat empty sequence')
        return super(RepeatGrammar, self).render()

    template = '''
                def repeat{n}():
                    result = []
                    while True:
                        p = self._pos
                        try:
                {innerexp}
                            if exp is not None:
                                result.append(exp)
                        except FailedParse:
                            self._goto(p)
                            break
                    return result
                exp = repeat{n}() # @UnusedVariable'''


class RepeatOneGrammar(RepeatGrammar):
    def parse(self, ctx):
        head = self.exp.parse(ctx)
        return simplify([head] + super(RepeatOneGrammar, self).parse(ctx))

    def _first(self, k, F):
        result = {()}
        for _i in range(k):
            result = dot(result, self.exp._first(k, F), k)
        return result

    def __str__(self):
        return '{%s}+' % str(self.exp)

    def render_fields(self, fields):
        fields.update(n=self.counter(),
                      exp=indent(render(self.exp)),
                      innerexp=indent(render(self.exp), 3))

    template = '''
                def repeat{n}():
                {exp}
                    result = [exp]
                    while True:
                        p = self._pos
                        try:
                {innerexp}
                            result.append(exp)
                        except FailedParse:
                            self._goto(p)
                            break
                    return result
                exp = repeat{n}() # @UnusedVariable'''


class OptionalGrammar(_DecoratorGrammar):
    def parse(self, ctx):
        p = ctx.pos
        try:
            return self.exp.parse(ctx)
        except FailedParse:
            ctx.goto(p)
            return None

    def _first(self, k, F):
        return {()} | self.exp._first(k, F)

    def __str__(self):
        return '[%s]' % str(self.exp)

    def render_fields(self, fields):
        fields.update(exp=indent(render(self.exp)))

    template = '''\
            p = self._pos
            exp = None
            try:
            {exp}
            except FailedParse:
                self._goto(p)\
            '''



class CutGrammar(_Grammar):
    def parse(self, ctx):
        return None

    def _first(self, k, F):
        return {('!',)}

    def __str__(self):
        return '!'

    template = 'cut_seen = True # @UnusedVariable'


class NamedGrammar(_DecoratorGrammar):
    def __init__(self, name, exp):
        super(NamedGrammar, self).__init__(exp)
        assert isinstance(exp, _Grammar), str(exp)
        self.name = name

    def parse(self, ctx):
        value = self.exp.parse(ctx)
        ctx.add_ast_node(self.name, value)
        return value

    def __str__(self):
        return '%s:%s' % (self.name, str(self.exp))

    template = '''
                {exp}
                self._add_ast_node('{name}', exp)'''


class SpecialGrammar(_Grammar):
    def __init__(self, special):
        super(SpecialGrammar, self).__init__()
        self.special = special

    def _first(self, k, F):
        return set([(self.special,)])

    def __str__(self):
        return '?/%s/?' % self.pattern


class RuleRefGrammar(_Grammar):
    def __init__(self, name):
        super(RuleRefGrammar, self).__init__()
        self.name = name

    def parse(self, ctx):
        try:
            rule = ctx.rules[self.name]
            return rule.parse(ctx)
        except KeyError:
            raise FailedRef(ctx.buf, self.name)
        except FailedParse:
            raise

    def _first(self, k, F):
        self._first_set = F.get(self.name, set())
        return self._first_set

    def __str__(self):
        return self.name

    template = '''exp = self._call("{name}") # @UnusedVariable'''


class RuleGrammar(NamedGrammar):
    def parse(self, ctx):
        ctx._rule_stack.append(self.name)
        ctx.push_ast()
        log.debug('%s \n\t%s', ctx.rulestack(), ctx.buf.lookahead())
        try:
            _tree, newpos = self._invoke_rule(self.name, ctx, ctx.pos)
            ctx.goto(newpos)
            log.debug('SUCCESS %s \n\t%s', ctx.rulestack(), ctx.buf.lookahead())
            return ctx.ast
        except FailedParse:
            log.debug('FAIL %s \n\t%s', ctx.rulestack(), ctx.buf.lookahead())
            raise
        finally:
            ctx.pop_ast()
            ctx._rule_stack.pop()

    @memoize
    def _invoke_rule(self, name, ctx, pos):
        ctx.goto(pos)
        return (self.exp.parse(ctx), ctx.pos)


    def _first(self, k, F):
        if self._first_set:
            return self._first_set
        return self.exp._first(k, F)

    def __str__(self):
        return '%s = %s ;' % (self.name, str(self.exp).strip())

    def render_fields(self, fields):
        fields.update(exp=indent(render(self.exp)))

    template = '''
                def _{name}_(self):
                {exp}

                '''

class Grammar(Renderer):
    def __init__(self, name, rules):
        super(Grammar, self).__init__()
        assert isinstance(rules, list), str(rules)
        self.name = name
        self.rules = rules
        self._first_sets = self._calc_first_sets()

    @property
    def first_sets(self):
        return self._first_sets

    def _calc_first_sets(self, k=1):
        F = dict()
        while True:
            F1 = deepcopy(F)
            for rule in self.rules:
                F[rule.name] = F.get(rule.name, set()) | rule._first(k, F)
            if F1 == F:
                break
        for rule in self.rules:
            rule._first_set = F[rule.name]
        return F

    def parse(self, start, text):
        log.info('enter grammar')
        try:
            try:
                ctx = Context(self.rules, text)
                start_rule = ctx.rules[start]
                tree = start_rule.parse(ctx)
                ctx.add_ast_node(start, tree)
                ctx.buf.eatwhitespace()
                if not ctx.buf.atend():
                    raise FailedParse(ctx.buf, '<EOF>')
                log.info('SUCCESS grammar')
                return ctx.ast
            except FailedCut as e:
                raise e.nested
        except:
            log.warning('failed grammar')
            raise

    def __str__(self):
        return '\n\n'.join(str(rule) for rule in self.rules) + '\n'

    def render_fields(self, fields):
        abstract_template = trim(self.abstract_rule_template)
        abstract_rules = [abstract_template.format(name=rule.name) for rule in self.rules]
        abstract_rules = indent('\n'.join(abstract_rules))
        fields.update(rules=indent(render(self.rules)),
                      abstract_rules=abstract_rules
                      )


    abstract_rule_template = '''
            def {name}(self, ast):
                return ast
            '''

    template = '''\
                # -*- coding: utf-8 -*-
                from __future__ import print_function, division, absolute_import, unicode_literals
                from grako.parsing import * # @UnusedWildImport
                from grako.exceptions import * # @UnusedWildImport

                class {name}ParserBase(Parser):
                {rules}
                class Abstract{name}Parser({name}ParserBase):
                {abstract_rules}
                '''
