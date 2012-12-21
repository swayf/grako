import re
import logging
from collections import namedtuple
from .buffering import Buffer
from .exceptions import *
from .ast import AST

log = logging.getLogger('grako.parsing')

Named = namedtuple('Named', ['name', 'value'])

def check(result):
    assert isinstance(result, _Parser), str(result)

class Context(object):
    def __init__(self, rules, text):
        self.rules = {rule.name :rule.exp for rule in rules}
        self.buf = Buffer(text)
        self.buf.goto(0)


class _Parser(object):

    def parse(self, ctx):
        result, newpos = self._parse(ctx, ctx.buf.pos)
        ctx.buf.goto(newpos)
        return result

    def _parse(self, ctx, pos):
        return None, pos


class EOFParser(_Parser):
    def _parse(self, ctx, pos):
        ctx.buf.goto(pos)
        if not ctx.buf.atend():
            raise FailedParse(ctx.buf, '<EOF>')
        return None, ctx.buf.pos


class _DecoratorParser(_Parser):
    def __init__(self, exp):
        assert isinstance(exp, _Parser), str(exp)
        super(_DecoratorParser, self).__init__()
        self.exp = exp

    def _parse(self, ctx, pos):
        return self.exp.parse(ctx), ctx.buf.pos

    def __str__(self):
        return str(self.exp)


class GroupParser(_DecoratorParser):
    def __str__(self):
        return '(%s)' % str(self.exp).strip()


class TokenParser(_Parser):
    def __init__(self, token):
        super(TokenParser, self).__init__()
        self.token = token

    def _parse(self, ctx, pos):
        log.info('token %s\n\t%s', self.token, ctx.buf.lookahead())
        ctx.buf.goto(pos)
        result = ctx.buf.match(self.token)
        if result is None:
            raise FailedToken(ctx.buf, self.token)
        return result, ctx.buf.pos

    def __str__(self):
        return "'%s'" % self.token.encode('string-escape')


class PatternParser(_Parser):
    def __init__(self, pattern):
        super(PatternParser, self).__init__()
        self.pattern = pattern
        self.re = re.compile(pattern)

    def _parse(self, ctx, pos):
        log.info('pattern %s\n\t%s', self.pattern, ctx.buf.lookahead())
        ctx.buf.goto(pos)
        result = ctx.buf.matchre(self.re)
        if result is None:
            raise FailedPattern(ctx.buf, self.pattern)
        print 'newpos', ctx.buf.pos, ctx.buf.lookahead()
        return result, ctx.buf.pos

    def __str__(self):
        return '?/%s/?' % self.pattern


class SequenceParser(_Parser):
    def __init__(self, sequence):
        super(SequenceParser, self).__init__()
        assert isinstance(sequence, list), str(sequence)
        self.sequence = sequence

    def _parse(self, ctx, pos):
        return self.parse_seq(ctx, pos, self.sequence), ctx.buf.pos

    def parse_seq(self, ctx, pos, seq):
        log.debug('sequence %s', str([type(s) for s in self.sequence]))
        ctx.buf.goto(pos)
        result = []
        for i, s in enumerate(seq):
            if not isinstance(s, CutParser):
                tree = s.parse(ctx)
                result.append(tree)
            else:
                try:
                    result.extend(self.parse_seq(ctx, ctx.buf.pos, seq[i + 1:]))
                except FailedParse as e:
                    raise FailedCut(ctx.buf, e)
        return result  # [r for r in result if r is not None]

    def __str__(self):
        return ' '.join(str(s).strip() for s in self.sequence)


class ChoiceParser(_Parser):
    def __init__(self, options):
        super(ChoiceParser, self).__init__()
        assert isinstance(options, list), repr(options)
        self.options = options

    def _parse(self, ctx, pos):
        items = []
        for o in self.options:
            ctx.buf.goto(pos)
            try:
                return o.parse(ctx), ctx.buf.pos
            except FailedCut as e:
                raise e.nested
            except FailedParse as e:
                items.append(e.item)
        raise FailedParse(ctx.buf, 'one of {%s}' % ','.join(items))

    def __str__(self):
        return ' | '.join(str(o).strip() for o in self.options)


class RepeatParser(_DecoratorParser):
    def _parse(self, ctx, pos):
        log.info('repeat %s', str(self.exp))
        ctx.buf.goto(pos)
        result = []
        while True:
            p = ctx.buf.pos
            try:
                tree = self.exp.parse(ctx)
                result.append(tree)
            except FailedCut:
                ctx.buf.goto(p)
                raise
            except FailedParse:
                ctx.buf.goto(p)
                break
        return result, ctx.buf.pos

    def __str__(self):
        return '{%s}' % str(self.exp)


class RepeatOneParser(RepeatParser):
    def _parse(self, ctx, pos):
        head = self.exp.parse(ctx)
        tail = super(RepeatOneParser, self).parse(ctx)
        return [head] + tail, ctx.buf.pos

    def __str__(self):
        return '{%s}+' % str(self.exp)


class OptionalParser(_DecoratorParser):
    def _parse(self, ctx, pos):
        ctx.buf.goto(pos)
        try:
            return self.exp.parse(ctx), ctx.buf.pos
        except FailedParse:
            ctx.buf.goto(pos)
            return None, pos

    def __str__(self):
        return '[%s]' % str(self.exp)


class CutParser(_Parser):
    def _parse(self, ctx, pos):
        return None, pos

    def __str__(self):
        return '!'


class RuleRefParser(_Parser):
    def __init__(self, name):
        super(RuleRefParser, self).__init__()
        self.name = name

    def _parse(self, ctx, pos):
        log.info('ref %s %d %s', self.name, pos, ctx.buf.lookahead())
        try:
            rule = ctx.rules[self.name]
            return rule.parse(ctx), ctx.buf.pos
        except KeyError:
            raise FailedRef(ctx.buf, self.name)

    def __str__(self):
        return self.name


class NamedParser(_DecoratorParser):
    def __init__(self, name, exp):
        super(NamedParser, self).__init__(exp)
        assert isinstance(exp, _Parser), str(exp)
        self.name = name

    def _parse(self, ctx, pos):
        tree = self.exp.parse(ctx)
        return Named(name=self.name, value=tree), ctx.buf.pos

    def __str__(self):
        return '%s:%s' % (self.name, str(self.exp))


class SpecialParser(_Parser):
    def __init__(self, special):
        super(SpecialParser, self).__init__()
        self.special = special

    def __str__(self):
        return '?/%s/?' % self.pattern

class RuleParser(NamedParser):
    def _parse(self, ctx, pos):
        ctx.buf.goto(pos)
        log.info('enter %s %d %s', self.name, pos, ctx.buf.lookahead())
        try:
            tree, pos = self.exp.parse(ctx)
            log.info('exit %s', self.name)
        except FailedPattern:
            log.info('failed %s', self.name)
            raise FailedParse(ctx.buf, self.name)
        except FailedParse as e:
            log.info('failed %s', self.name)
            raise FailedMatch(ctx.buf, self.name, e.item)
        except:
            log.info('failed %s', self.name)
            raise

        if not isinstance(tree, list):
            return tree, ctx.buf.pos
        else:
            result = AST()
            for d in tree:
                if isinstance(d, Named):
                    result[d.name] = d.value
            return result, ctx.buf.pos

    def __str__(self):
        return '%s = %s ;' % (self.name, str(self.exp).strip())


class GrammarParser(object):
    def __init__(self, rules):
        super(GrammarParser, self).__init__()
        assert isinstance(rules, list), str(rules)
        self.rules = rules

    def parse(self, start, text):
        log.info('enter grammar')
        try:
            ctx = Context(self.rules, text)
            start_rule = ctx.rules[start]
            tree, _p = start_rule.parse(ctx)
            if not ctx.buf.atend():
                raise FailedParse(ctx.buf, '<EOF>')
            return tree
        except:
            log.info('failed grammar')
            raise
        else:
            log.info('exit grammar')

    def __str__(self):
        return '\n\n'.join(str(rule) for rule in self.rules) + '\n'

