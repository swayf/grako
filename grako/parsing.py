import re
import logging
from .util import memoize, simplify, indent
from .rendering import Renderer, render
from .buffering import Buffer
from .exceptions import *  # @UnusedWildImport
from .ast import AST

log = logging.getLogger('grako.parsing')

def check(result):
    assert isinstance(result, _Parser), str(result)

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

class _Parser(Renderer):

    def parse(self, ctx):
        return None

class EOFParser(_Parser):
    def parse(self, ctx):
        if not ctx.buf.atend():
            raise FailedParse(ctx.buf, '<EOF>')

    template = 'self._eol()'


class _DecoratorParser(_Parser):
    def __init__(self, exp):
        assert isinstance(exp, _Parser), str(exp)
        super(_DecoratorParser, self).__init__()
        self.exp = exp

    def parse(self, ctx):
        return self.exp.parse(ctx)

    def __str__(self):
        return str(self.exp)


class GroupParser(_DecoratorParser):
    def __str__(self):
        return '(%s)' % str(self.exp).strip()

    template = '({exp})'

class TokenParser(_Parser):
    def __init__(self, token):
        super(TokenParser, self).__init__()
        self.token = token

    def parse(self, ctx):
        log.debug('token <%s>\n\t%s', self.token, ctx.buf.lookahead())
        result = ctx.buf.match(self.token)
        if result is None:
            raise FailedToken(ctx.buf, self.token)
        return result

    def __str__(self):
        if "'" in self.token:
            if '"' in self.token:
                return "'%s'" % self.token.encode('string-escape')
            else:
                return '"%s"' % self.token
        return "'%s'" % self.token

    template = '''\
                self._token("{token}")
                '''


class PatternParser(_Parser):
    def __init__(self, pattern):
        super(PatternParser, self).__init__()
        self.pattern = pattern
        self._re = re.compile(pattern)

    def parse(self, ctx):
        log.debug('pattern <%s>\n\t%s', self.pattern, ctx.buf.lookahead())
        result = ctx.buf.matchre(self._re)
        if result is None:
            raise FailedPattern(ctx.buf, self.pattern)
        return result

    def __str__(self):
        return '?/%s/?' % self.pattern

    template = '''\
                self._pattern("{pattern}")
                '''


class SequenceParser(_Parser):
    def __init__(self, sequence):
        super(SequenceParser, self).__init__()
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
#            if not isinstance(s, CutParser):
#                tree = s.parse(ctx)
#                result.append(tree)
#            else:
#                try:
#                    result.extend(self.parse_seq(ctx, seq[i + 1:]))
#                except FailedParse as e:
#                    raise FailedCut(ctx.buf, e)
        return [r for r in result if r is not None]

    def __str__(self):
        return ' '.join(str(s).strip() for s in self.sequence)


class ChoiceParser(_Parser):
    def __init__(self, options):
        super(ChoiceParser, self).__init__()
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
                raise
            except FailedParse as e:
                items.append(e.item)
        raise FailedParse(ctx.buf, 'one of {%s}' % ','.join(items))

    def __str__(self):
        return ' | '.join(str(o).strip() for o in self.options)


class RepeatParser(_DecoratorParser):
    def parse(self, ctx):
        log.debug('repeat %s', str(self.exp))
        result = []
        while True:
            p = ctx.buf.pos
            try:
                tree = self.exp.parse(ctx)
                result.append(tree)
            except FailedCut:
                raise
            except FailedParse:
                ctx.buf.goto(p)
                break
        return simplify(result)

    def __str__(self):
        return '{%s}' % str(self.exp)


class RepeatOneParser(RepeatParser):
    def parse(self, ctx):
        head = self.exp.parse(ctx)
        return simplify([head] + super(RepeatOneParser, self).parse(ctx))

    def __str__(self):
        return '{%s}+' % str(self.exp)


class OptionalParser(_DecoratorParser):
    def parse(self, ctx):
        p = ctx.pos
        try:
            return self.exp.parse(ctx)
        except FailedParse:
            ctx.goto(p)
            return None

    def __str__(self):
        return '[%s]' % str(self.exp)


class CutParser(_Parser):
    def parse(self, ctx):
        return None

    def __str__(self):
        return '!'


class NamedParser(_DecoratorParser):
    def __init__(self, name, exp):
        super(NamedParser, self).__init__(exp)
        assert isinstance(exp, _Parser), str(exp)
        self.name = name

    def parse(self, ctx):
        value = self.exp.parse(ctx)
        ctx.add_ast_node(self.name, value)
        return value

    def __str__(self):
        return '%s:%s' % (self.name, str(self.exp))

    template = '''\
                exp = {exp}
                self.ast["{name}"] = exp
                '''


class SpecialParser(_Parser):
    def __init__(self, special):
        super(SpecialParser, self).__init__()
        self.special = special

    def __str__(self):
        return '?/%s/?' % self.pattern


class RuleRefParser(_Parser):
    def __init__(self, name):
        super(RuleRefParser, self).__init__()
        self.name = name

    def parse(self, ctx):
        try:
            rule = ctx.rules[self.name]
            return rule.parse(ctx)
        except KeyError:
            raise FailedRef(ctx.buf, self.name)
        except FailedParse:
            raise

    def __str__(self):
        return self.name

    template = 'self.call_("{name}")'


class RuleParser(NamedParser):
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

    def __str__(self):
        return '%s = %s ;' % (self.name, str(self.exp).strip())

    def render_fields(self, fields):
        fields.update(exp=indent(render(self.exp)))

    template = '''
                def _{name}_(self):
                {exp}

                '''


class GrammarParser(Renderer):
    def __init__(self, name, rules):
        super(GrammarParser, self).__init__()
        assert isinstance(rules, list), str(rules)
        self.name = name
        self.rules = rules

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
        fields.update(rules=indent(render(self.rules)))

    template = '''\
                class {name}ParserBase(Grammar):
                {rules}

                '''
