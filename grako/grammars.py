# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import re
import logging
from copy import deepcopy
from keyword import iskeyword
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

def urepr(obj):
    return repr(obj).lstrip('u')

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

    def add_ast_node(self, name, node, force_list):
        if name is not None and node:
            self.ast.add(name, node, force_list)
        return node

    def next_token(self):
        self.buf.eatwhitespace()


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

    def _validate(self, rules):
        pass

    def _first(self, k, F):
        return set()


class VoidGrammar(_Grammar):
    def __str__(self):
        return '()'

    template = 'pass'


class EOFGrammar(_Grammar):
    def parse(self, ctx):
        ctx.buf.eatwhitespace()
        if not ctx.buf.atend():
            raise FailedParse(ctx.buf, '<EOF>')

    def __str__(self):
        return '$'

    template = 'self._check_eof()'


class _DecoratorGrammar(_Grammar):
    def __init__(self, exp):
        assert isinstance(exp, _Grammar), str(exp)
        super(_DecoratorGrammar, self).__init__()
        self.exp = exp

    def parse(self, ctx):
        return self.exp.parse(ctx)

    def _validate(self, rules):
        self.exp._validate(rules)

    def _first(self, k, F):
        return self.exp._first(k, F)

    def __str__(self):
        return str(self.exp)

    template = '{exp}'


class GroupGrammar(_DecoratorGrammar):
    def __str__(self):
        return '(%s)' % str(self.exp).strip()

    def render_fields(self, fields):
        fields.update(exp=indent(render(self.exp)))

    template = '''\
                with self._group():
                {exp}
                    _e = self.cst
                '''


class TokenGrammar(_Grammar):
    def __init__(self, token):
        super(TokenGrammar, self).__init__()
        self.token = token

    def parse(self, ctx):
        log.debug('token <%s>\n\t%s', self.token, ctx.buf.lookahead())
        ctx.next_token()
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
        fields.update(token=urepr(self.token))

    template = "_e = self._token({token})"


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
        fields.update(pattern=urepr(self.pattern))

    template = '_e = self._pattern({pattern})'


class LookaheadGrammar(_DecoratorGrammar):
    def __str__(self):
        return '!' + self.exp

    def parse(self, ctx):
        p = ctx.pos
        try:
            super(LookaheadNotGrammar, self).parse(ctx)
        finally:
            ctx.goto(p)

    def render_fields(self, fields):
        fields.update(exp=indent(render(self.exp)))

    template = '''\
                with self._if():
                {exp}\
                '''

class LookaheadNotGrammar(_DecoratorGrammar):
    def __str__(self):
        return '!' + self.exp

    def parse(self, ctx):
        p = ctx.pos
        try:
            super(LookaheadNotGrammar, self).parse(ctx)
            ctx.goto(p)
            raise FailedLookahead(str(self.exp))
        except FailedParse:
            ctx.goto(p)
            pass

    def render_fields(self, fields):
        fields.update(exp=indent(render(self.exp)))

    template = '''\
                with self._ifnot():
                {exp}\
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

    def _validate(self, rules):
        for s in self.sequence:
            s._validate(rules)

    def _first(self, k, F):
        result = {()}
        for s in self.sequence:
            result = dot(result, s._first(k, F), k)
        return result

    def __str__(self):
        return ' '.join(str(s).strip() for s in self.sequence)

    def render_fields(self, fields):
        fields.update(seq=indent('\n'.join(render(s) for s in self.sequence)))

    template = '''
                with self._sequence():
                {seq}\
                '''


class ChoiceGrammar(_Grammar):
    def __init__(self, options):
        super(ChoiceGrammar, self).__init__()
        assert isinstance(options, list), urepr(options)
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

    def _validate(self, rules):
        for o in self.options:
            o._validate(rules)

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
        firstset = ' '.join(str(urepr(f[0])) for f in self.firstset if f)
        if firstset:
            error = 'expecting one of: ' + firstset
        else:
            error = 'no available options'
        fields.update(n=self.counter(),
                      options=indent(options),
                      error=urepr(error)
                      )

    def render(self):
        if len(self.options) == 1:
            return render(self.options[0])
        else:
            return super(ChoiceGrammar, self).render()

    option_template = '''\
                    with self._option():
                    {option}
                        return _e\
                    '''

    template = '''\
                def choice{n}():
                    _e = None
                {options}
                    self.error({error})
                _e = choice{n}() \
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
                      innerexp=indent(render(self.exp)))

    def render(self):
        if {()} in self.exp.firstset:
            raise GrammarError('may repeat empty sequence')
        return super(RepeatGrammar, self).render()

    template = '''
                def repeat{n}():
                {innerexp}
                    return _e
                _e = self._repeat(repeat{n})\
                '''


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
                      exp=render(self.exp),
                      innerexp=indent(render(self.exp)))

    template = '''
                def repeat{n}():
                {innerexp}
                    return _e
                _e = self._repeat(repeat{n}, plus=True)\
                '''


class OptionalGrammar(_DecoratorGrammar):
    def parse(self, ctx):
        p = ctx.pos
        try:
            return self.exp.parse(ctx)
        except FailedCut:
            raise
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
                _e = None
                with self._optional():
                {exp}\
                '''


class CutGrammar(_Grammar):
    def parse(self, ctx):
        return None

    def _first(self, k, F):
        return {('>>',)}

    def __str__(self):
        return '>>'

    template = 'self._cut()'


class NamedGrammar(_DecoratorGrammar):
    def __init__(self, name, exp, force_list):
        super(NamedGrammar, self).__init__(exp)
        assert isinstance(exp, _Grammar), str(exp)
        self.name = name
        self.force_list = force_list

    def parse(self, ctx):
        value = self.exp.parse(ctx)
        ctx.add_ast_node(self.name, value, self.force_list)
        return value

    def __str__(self):
        if self.force_list:
            return '%s+:%s' % (self.name, str(self.exp))
        return '%s:%s' % (self.name, str(self.exp))

    def render_fields(self, fields):
        fields.update(
                      n=self.counter(),
                      exp=render(self.exp),
                      force_list=', force_list=True' if self.force_list else ''
                      )
    template = '''
                {exp}
                self.ast.add('{name}', _e{force_list})
                '''


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
        if iskeyword(name):
            name += '_'
        super(RuleRefGrammar, self).__init__()
        self.name = name

    def parse(self, ctx):
        try:
            rule = ctx.rules[self.name]
            if self.name[0].islower():
                ctx.next_token()
            return rule.parse(ctx)
        except KeyError:
            raise FailedRef(ctx.buf, self.name)
        except FailedParse:
            raise

    def _validate(self, rules):
        if self.name not in rules:
            raise GrammarError("reference to unknown rule '%s'" % self.name)

    def _first(self, k, F):
        self._first_set = F.get(self.name, set())
        return self._first_set

    def __str__(self):
        return self.name

    template = "_e = self._call('{name}')"


class RuleGrammar(NamedGrammar):
    def __init__(self, name, exp, ast_name=None):
        if iskeyword(name):
            name += '_'
        super(RuleGrammar, self).__init__(name, exp, False)
        self.ast_name = ast_name

    def parse(self, ctx):
        ctx._rule_stack.append(self.name)
        ctx.push_ast()
        log.debug('%s \n\t%s', ctx.rulestack(), ctx.buf.lookahead())
        try:
            if self.name[0].islower():
                ctx.next_token()
            _tree, newpos = self._invoke_rule(self.name, ctx, ctx.pos)
            ctx.goto(newpos)
            log.debug('SUCCESS %s \n\t%s', ctx.rulestack(), ctx.buf.lookahead())
            if self.ast_name:
                return AST({self.ast_name:ctx.ast})
            else:
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
        if self.ast_name:
            ast_name_clause = 'self.ast = AST(%s=self.ast)\n' % self.ast_name
        else:
            ast_name_clause = ''
        fields.update(
                      exp=indent(render(self.exp)),
                      ast_name_clause=ast_name_clause
                      )

    template = '''
                def _{name}_(self):
                    _e = None
                {exp}
                    {ast_name_clause}
                '''

class Grammar(Renderer):
    def __init__(self, name, rules):
        super(Grammar, self).__init__()
        assert isinstance(rules, list), str(rules)
        self.name = name
        self.rules = rules
        self._validate()
        self._first_sets = self._calc_first_sets()

    def _validate(self):
        ruledict = {r.name for r in self.rules}
        for rule in self.rules:
            rule._validate(ruledict)

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
                ctx.add_ast_node(start, tree, False)
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
                #
                # CAVEAT UTILITOR
                # This file was automatically generated by Grako.
                #    https://bitbucket.org/apalala/grako/
                # Any changes you make to it will be overwritten the next time the file is generated.
                #

                from __future__ import print_function, division, absolute_import, unicode_literals
                from grako.parsing import * # @UnusedWildImport
                from grako.exceptions import * # @UnusedWildImport

                class {name}ParserRoot(Parser):
                {rules}


                class Abstract{name}Parser(AbstractParserMixin, {name}ParserRoot):
                    pass


                class {name}ParserBase({name}ParserRoot):
                {abstract_rules}

                '''
