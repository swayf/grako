# -*- coding: utf-8 -*-
"""
Elements for a model of a parsed Grako grammar.

A model constructed with these elements, and rooted in a Grammar instance is
able to parse the language defined by the grammar, but the main purpose of
the model is the generation of independent, top-down, verbose, and debugable
parsers through the inline templates from the .rendering module.

Models calculate the LL(k) FIRST function to aid in providing more significant
error messages when a choice fails to parse. FOLLOW(k) and LA(k) should be
computed, but they are not.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import re
from copy import deepcopy
from keyword import iskeyword
import time
from .util import indent, trim
from .rendering import Renderer, render
from .buffering import Buffer
from .contexts import ParseContext, ParseInfo
from .exceptions import (FailedParse,
                         FailedToken,
                         FailedPattern,
                         FailedRef,
                         FailedSemantics,
                         GrammarError)


def check(result):
    assert isinstance(result, _Model), str(result)


def dot(x, y, k):
    return set([(a + b)[:k] for a in x for b in y])


def urepr(obj):
    return repr(obj).lstrip('u')


class ModelContext(ParseContext):
    def __init__(self, rules, buffer=None, semantics=None, trace=False, **kwargs):
        super(ModelContext, self).__init__(buffer=buffer,
                                           semantics=semantics,
                                           trace=trace,
                                           **kwargs)
        self.rules = {rule.name: rule for rule in rules}
        self._buffer.goto(0)

    @property
    def pos(self):
        return self._buffer.pos

    @property
    def buf(self):
        return self._buffer

    def _find_rule(self, name):
        return self.rules[name]


class _Model(Renderer):
    def __init__(self):
        super(_Model, self).__init__()
        self._first_set = None

    def parse(self, ctx):
        return None

    @property
    def firstset(self, k=1):
        if self._first_set is None:
            self._first_set = self._first(k, {})
        return self._first_set

    def _validate(self, rules):
        return True

    def _first(self, k, F):
        return set()


class Void(_Model):
    def __str__(self):
        return '()'

    template = 'pass'


class Fail(_Model):
    def __str__(self):
        return '!()'

    template = 'self._fail()'


class Comment(_Model):
    def __init__(self, text):
        super(Comment, self).__init__()
        self.text = text.strip()

    def __str__(self):
        return self.render()

    template = '''
        (* {text} *)

        '''


class EOF(_Model):
    def parse(self, ctx):
        ctx._next_token()
        if not ctx.buf.atend():
            raise FailedParse(ctx.buf, 'Expecting end of text.')

    def __str__(self):
        return '$'

    template = 'self._check_eof()'


class _Decorator(_Model):
    def __init__(self, exp):
        assert isinstance(exp, _Model), str(exp)
        super(_Decorator, self).__init__()
        self.exp = exp

    def parse(self, ctx):
        return self.exp.parse(ctx)

    def _validate(self, rules):
        return self.exp._validate(rules)

    def _first(self, k, F):
        return self.exp._first(k, F)

    def __str__(self):
        return str(self.exp)

    template = '{exp}'


class Group(_Decorator):
    def parse(self, ctx):
        with ctx._group():
            return self.exp.parse(ctx)

    def __str__(self):
        template = '(%s)'
        if isinstance(self.exp, Choice):
            template = '\n' + trim(self.str_template)
        return template % str(self.exp)

    template = '''\
                with self._group() as _e:
                {exp:1::}
                    _e = self.cst
                '''

    str_template = '''
            (
            %s
            )
            '''


class Token(_Model):
    def __init__(self, token):
        super(Token, self).__init__()
        self.token = token
        if not self.token:
            raise GrammarError('invalid token %s' % self.token)

    def parse(self, ctx):
        ctx._next_token()
        token = ctx.buf.match(self.token)
        if token is None:
            raise FailedToken(ctx.buf, self.token)

        ctx._trace_match(self.token, None)
        ctx._add_cst_node(token)
        return token

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


class Pattern(_Model):
    def __init__(self, pattern):
        super(Pattern, self).__init__()
        self.pattern = pattern
        self._re = re.compile(pattern)

    def parse(self, ctx):
        token = ctx.buf.matchre(self._re)
        if token is None:
            raise FailedPattern(ctx.buf, self.pattern)
        ctx._trace_match(token, self.pattern)
        ctx._add_cst_node(token)
        return token

    def _first(self, k, F):
        return set([(self.pattern,)])

    def __str__(self):
        return '?/%s/?' % self.pattern

    def render_fields(self, fields):
        fields.update(pattern=urepr(self.pattern))

    template = '_e = self._pattern({pattern})'


class Lookahead(_Decorator):
    def __str__(self):
        return '&' + str(self.exp)

    def parse(self, ctx):
        with ctx._if():
            super(Lookahead, self).parse(ctx)

    template = '''\
                with self._if():
                {exp:1::}\
                '''


class LookaheadNot(_Decorator):
    def __str__(self):
        return '!' + str(self.exp)

    def parse(self, ctx):
        with ctx._ifnot():
            super(LookaheadNot, self).parse(ctx)

    template = '''\
                with self._ifnot():
                {exp:1::}\
                '''


class Sequence(_Model):
    def __init__(self, sequence):
        super(Sequence, self).__init__()
        assert isinstance(sequence, list), str(sequence)
        self.sequence = sequence
        for s in self.sequence:
            assert isinstance(s, _Model), str(s)

    def parse(self, ctx):
        result = []
        for s in self.sequence:
            tree = s.parse(ctx)
            if tree is not None:
                result.append(tree)
        return result

    def _validate(self, rules):
        return all(s._validate(rules) for s in self.sequence)

    def _first(self, k, F):
        result = {()}
        for s in self.sequence:
            result = dot(result, s._first(k, F), k)
        return result

    def __str__(self):
        return ' '.join(str(s).strip() for s in self.sequence)

    def render_fields(self, fields):
        fields.update(seq='\n'.join(render(s) for s in self.sequence))

    template = '''
                {seq}\
                '''


class Choice(_Model):
    def __init__(self, options):
        super(Choice, self).__init__()
        assert isinstance(options, list), urepr(options)
        self.options = options
        for o in self.options:
            assert isinstance(o, _Model), str(o)

    def parse(self, ctx):
        with ctx._choice_context():
            for o in self.options:
                with ctx._option():
                    return o.parse(ctx)
            firstset = ' '.join(str(urepr(f[0])) for f in self.firstset if f)
            if firstset:
                raise FailedParse(ctx.buf, 'one of {%s}' % firstset)
            raise FailedParse(ctx.buf, 'no available options')

    def _validate(self, rules):
        return all(o._validate(rules) for o in self.options)

    def _first(self, k, F):
        result = set()
        for o in self.options:
            result |= o._first(k, F)
        return result

    def __str__(self):
        return '  ' + '\n| '.join(str(o).strip() for o in self.options)

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

    def render(self, **fields):
        if len(self.options) == 1:
            return render(self.options[0], **fields)
        else:
            return super(Choice, self).render(**fields)

    option_template = '''\
                    with self._option() as _e:
                    {option}
                        return _e\
                    '''

    template = '''\
                @self._choice
                def choice{n}():
                {options}
                    self._error({error})
                _e = choice{n}() \
                '''


class Repeat(_Decorator):
    def parse(self, ctx):
        f = lambda: self.exp.parse(ctx)
        return ctx._repeat(f)

    def _first(self, k, F):
        efirst = self.exp._first(k, F)
        result = {()}
        for _i in range(k):
            result = dot(result, efirst, k)
        return {()} | result

    def __str__(self):
        template = '{%s}'
        if isinstance(self.exp, Choice):
            template = trim(self.str_template)
        return template % str(self.exp)

    def render_fields(self, fields):
        fields.update(n=self.counter())

    def render(self, **fields):
        if {()} in self.exp.firstset:
            raise GrammarError('may repeat empty sequence')
        return super(Repeat, self).render(**fields)

    template = '''
                @self._closure
                def closure{n}():
                {exp:1::}
                    return _e
                _e = closure{n}()\
                '''

    str_template = '''
            {
            %s
            }
            '''


class RepeatPlus(Repeat):
    def parse(self, ctx):
        f = lambda: self.exp.parse(ctx)
        return ctx._repeat(f, plus=True)

    def _first(self, k, F):
        efirst = self.exp._first(k, F)
        result = {()}
        for _i in range(k):
            result = dot(result, efirst, k)
        return result

    def __str__(self):
        return super(RepeatPlus, self).__str__() + '+'

    def render_fields(self, fields):
        fields.update(n=self.counter())

    template = '''
                @self._closure_plus
                def closure{n}():
                {exp:1::}
                    return _e
                _e = closure{n}()\
                '''


class Optional(_Decorator):

    def parse(self, ctx):
        with ctx._optional():
            return self.exp.parse(ctx)

    def _first(self, k, F):
        return {()} | self.exp._first(k, F)

    def __str__(self):
        exp = str(self.exp)
        template = '[%s]'
        if isinstance(self.exp, Choice):
            template = trim(self.str_template)
        elif isinstance(self.exp, Group):
            exp = self.exp.exp
        return template % exp

    template = '''\
                with self._optional() as _e:
                {exp:1::}\
                '''

    str_template = '''
            {
            %s
            }
            '''


class Cut(_Model):
    def parse(self, ctx):
        ctx._cut()
        return None

    def _first(self, k, F):
        return {('>>',)}

    def __str__(self):
        return '>>'

    template = 'self._cut()'


class Named(_Decorator):
    def __init__(self, name, exp, force_list):
        super(Named, self).__init__(exp)
        assert isinstance(exp, _Model), str(exp)
        self.name = name
        self.force_list = force_list

    def parse(self, ctx):
        value = self.exp.parse(ctx)
        ctx._add_ast_node(self.name, value, self.force_list)
        return value

    def __str__(self):
        if self.force_list:
            return '%s+:%s' % (self.name, str(self.exp))
        return '%s:%s' % (self.name, str(self.exp))

    def render_fields(self, fields):
        name = self.name
        if iskeyword(name):
            name += '_'
        fields.update(n=self.counter(),
                      name=name,
                      force_list=', force_list=True' if self.force_list else ''
                      )

    template = '''
                {exp}
                self.ast.add('{name}', _e{force_list})\
                '''


class Override(_Decorator):
    def parse(self, ctx):
        result = super(Override, self).parse(ctx)
        ctx._add_ast_node('@', result)
        return result

    def __str__(self):
        return '@%s' % str(self.exp)

    template = '''
                {exp}
                self._add_ast_node('@', _e)\
                '''


class Special(_Model):
    def __init__(self, special):
        super(Special, self).__init__()
        self.special = special

    def _first(self, k, F):
        return set([(self.special,)])

    def __str__(self):
        return '?%s?' % self.special


class RuleRef(_Model):
    def __init__(self, name):
        super(RuleRef, self).__init__()
        self.name = name

    def parse(self, ctx):
        try:
            rule = ctx._find_rule(self.name)
            if self.name[0].islower():
                ctx._next_token()
            node = rule.parse(ctx)
            ctx._add_cst_node(node)
            return node
        except KeyError:
            raise FailedRef(ctx.buf, self.name)
        except FailedParse:
            raise

    def _validate(self, rules):
        if self.name not in rules:
            print("Reference to unknown rule '%s'." % self.name, file=sys.stderr)
            return False
        return True

    def _first(self, k, F):
        self._first_set = F.get(self.name, set())
        return self._first_set

    def __str__(self):
        return self.name

    def render_fields(self, fields):
        name = self.name
        if iskeyword(name):
            name += '_'
        fields.update(name=name)

    template = "_e = self._call('{name}')"


class Rule(Named):
    def __init__(self, name, exp, ast_name=None):
        super(Rule, self).__init__(name, exp, False)
        self.ast_name = ast_name

    def parse(self, ctx):
        ctx._rule_stack.append(self.name)
        try:
            if self.name[0].islower():
                ctx._next_token()
            ctx._trace_event('ENTER ')
            node, newpos = self._invoke_rule(self.name, ctx)
            ctx.goto(newpos)
            ctx._trace_event('SUCCESS')
            return node
        except FailedParse:
            ctx._trace_event('FAILED')
            raise
        finally:
            ctx._rule_stack.pop()

    def _invoke_rule(self, name, ctx):
        key = (ctx.pos, name)
        cache = ctx._memoization_cache

        if key in cache:
            return cache[key]

        pos = ctx._pos
        ctx._push_ast()
        try:
            self.exp.parse(ctx)
            node = ctx.ast
            if not node:
                node = ctx.cst
            elif '@' in node:
                node = node['@']
            elif ctx.parseinfo:
                node.add('parseinfo', ParseInfo(ctx._buffer, name, pos, ctx._pos))
#            if self.ast_name:
#                node = AST([(self.ast_name, node)])
            semantic_rule = ctx._find_semantic_rule(name)
            if semantic_rule:
                try:
                    node = semantic_rule(node)
                except FailedSemantics as e:
                    ctx._error(str(e), FailedParse)
        finally:
            ctx._pop_ast()
        result = (node, ctx.pos)
        cache[key] = result
        return result

    def _first(self, k, F):
        if self._first_set:
            return self._first_set
        return self.exp._first(k, F)

    def __str__(self):
        return trim(self.str_template) % (self.name, indent(str(self.exp)))

    def render_fields(self, fields):
        self.reset_counter()
        name = self.name
        if iskeyword(name):
            name += '_'
        if self.ast_name:
            ast_name_clause = '\nself.ast = AST(%s=self.ast)\n' % self.ast_name_
        else:
            ast_name_clause = ''
        fields.update(name=name,
                      ast_name_clause=ast_name_clause
                      )

    template = '''
                def _{name}_(self):
                    _e = None
                {exp:1::}{ast_name_clause}

                '''
    str_template = '''\
                %s
                    =
                %s
                    ;
                '''


class Grammar(Renderer):
    def __init__(self, name, rules):
        super(Grammar, self).__init__()
        assert isinstance(rules, list), str(rules)
        self.name = name
        self.rules = rules
        if not self._validate({r.name for r in self.rules}):
            raise GrammarError('Unknown rules, no parser generated.')
        self._first_sets = self._calc_first_sets()

    def _validate(self, ruleset):
        return all(rule._validate(ruleset) for rule in self.rules)

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

    def parse(self, text,
                    start=None,
                    filename=None,
                    semantics=None,
                    trace=False,
                    **kwargs):
        if not isinstance(text, Buffer):
            text = Buffer(text, filename=filename, **kwargs)
        ctx = ModelContext(self.rules,
                           buffer=text,
                           semantics=semantics,
                           trace=trace, **kwargs)
        start_rule = ctx._find_rule(start) if start else self.rules[0]
        with ctx._choice_context():
            return start_rule.parse(ctx)

    def codegen(self):
        return self.render()

    def __str__(self):
        return '\n\n'.join(str(rule) for rule in self.rules) + '\n'

    def render_fields(self, fields):
        abstract_template = trim(self.abstract_rule_template)
        abstract_rules = [abstract_template.format(name=rule.name) for rule in self.rules]
        abstract_rules = indent('\n'.join(abstract_rules))
        fields.update(rules=indent(render(self.rules)),
                      abstract_rules=abstract_rules,
                      version=time.strftime('%y.%j.%H.%M.%S', time.gmtime())
                      )

    abstract_rule_template = '''
            def {name}(self, ast):
                return ast
            '''

    template = '''\
                #!/usr/env/bin python
                # -*- coding: utf-8 -*-
                #
                # CAVEAT UTILITOR
                # This file was automatically generated by Grako.
                #    https://bitbucket.org/apalala/grako/
                # Any changes you make to it will be overwritten the
                # next time the file is generated.
                #

                from __future__ import print_function, division, absolute_import, unicode_literals
                from grako.parsing import * # @UnusedWildImport
                from grako.exceptions import * # @UnusedWildImport

                __version__ = '{version}'

                class {name}Parser(Parser):
                {rules}


                class {name}SemanticParser(CheckSemanticsMixin, {name}Parser):
                    pass


                class {name}Semantics(object):
                {abstract_rules}

                def main(filename, startrule):
                    import json
                    with open(filename) as f:
                        text = f.read()
                    parser = {name}Parser(parseinfo=False)
                    ast = parser.parse(text, startrule, filename=filename)
                    print('AST:')
                    print(ast)
                    print()
                    print('JSON:')
                    print(json.dumps(ast, indent=2))
                    print()

                if __name__ == '__main__':
                    import sys
                    if '-l' in sys.argv:
                        print('Rules:')
                        for r in {name}Parser.rule_list():
                            print(r)
                        print()
                    elif len(sys.argv) == 3:
                        main(sys.argv[1], sys.argv[2])
                    else:
                        print('Usage:')
                        program = sys.argv[0].split('/')[-1]
                        print(program, ' <filename> <startrule>')
                        print(program, ' -l') # list rules
                        print(program, ' -h')

                '''
