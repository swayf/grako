import re
import logging
from collections import namedtuple, defaultdict
from .exceptions import *
#from .util import memoize

log = logging.getLogger('grako.parsig')

Named = namedtuple('Named', ['name', 'value'])

def check(result):
    assert isinstance(result, _Parser), str(result)

class Context(object):
    def __init__(self, rules, buf):
        self.rules = {rule.name :rule.exp for rule in rules}
        self.buf = buf
        self.buf.goto(0)


class _Parser(object):
    def parse(self, ctx, pos):
        return None, pos


class _DecoratorParser(_Parser):
    def __init__(self, exp):
        assert isinstance(exp, _Parser), str(exp)
        super(_DecoratorParser, self).__init__()
        self.exp = exp

    def parse(self, ctx, pos):
        return self.exp.parse(ctx, pos), ctx.buf.pos

    def __str__(self):
        return str(self.exp)


class GroupParser(_DecoratorParser):
    def __str__(self):
        return '(%s)' % str(self.exp)


class TokenParser(_Parser):
    def __init__(self, token):
        super(TokenParser, self).__init__()
        self.token = token

    def parse(self, ctx, pos):
        ctx.buf.goto(pos)
        result = ctx.buf.match(self.token)
        if result is None:
            raise FailedToken(ctx.buf, self.token)
        return result, ctx.buf.pos

    def __str__(self):
        return "'%s'" % self.token.replace("'", "\\'")


class PatternParser(_Parser):
    def __init__(self, pattern):
        super(PatternParser, self).__init__()
        self.pattern = pattern
        self.re = re.compile(pattern)

    def parse(self, ctx, pos):
        ctx.buf.goto(pos)
        result = ctx.buf.matchre(self.re)
        if result is None:
            raise FailedPattern(ctx.buf, self.pattern)
        return result, ctx.buf.pos

    def __str__(self):
        return '?/%s/?' % self.pattern.replace('/', '\/')


class SequenceParser(_Parser):
    def __init__(self, sequence):
        super(SequenceParser, self).__init__()
        assert isinstance(sequence, list), str(sequence)
        self.sequence = sequence

    def parse(self, ctx, pos):
        return self.parse_seq(ctx, pos, self.sequence), ctx.buf.pos

    def parse_seq(self, ctx, pos, seq):
        ctx.buf.goto(pos)
        result = []
        for i, s in enumerate(seq):
            if not isinstance(s, CutParser):
                tree, pos = s.parse(ctx, pos)
                result.append(tree)
            else:
                try:
                    result.extend(self.parse_seq(ctx, ctx.buf.pos, seq[i + 1:]))
                except FailedParse as e:
                    raise FailedCut(ctx.buf, e)
        return [r for r in result if r is not None]

    def __str__(self):
        return ' '.join(str(s) for s in self.sequence)


class ChoiceParser(_Parser):
    def __init__(self, options):
        super(ChoiceParser, self).__init__()
        assert isinstance(options, list), repr(options)
        self.options = options

    def parse(self, ctx, pos):
        items = []
        for o in self.options:
            ctx.buf.goto(pos)
            try:
                return o.parse(ctx, pos), ctx.buf.pos
            except FailedCut as e:
                raise e.nested
            except FailedParse as e:
                items.append(e.item)
        raise FailedParse(ctx.buf, 'one of {%s}' % ','.join(items))

    def __str__(self):
        return ' | '.join(str(o) for o in self.options)


class RepeatParser(_DecoratorParser):
    def parse(self, ctx, pos):
        ctx.buf.goto(pos)
        result = []
        while True:
            p = ctx.buf.pos
            try:
                tree, pos = self.exp.parse(ctx, pos)
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
    def parse(self, ctx, pos):
        head, _p = self.exp.parse(ctx, pos)
        tail, pos = super(RepeatOneParser, self).parse(ctx, ctx.buf.pos)
        return [head] + tail, pos

    def __str__(self):
        return '{%s}+' % str(self.exp)


class OptionalParser(_DecoratorParser):
    def parse(self, ctx, pos):
        ctx.buf.goto(pos)
        try:
            return self.exp.parse(ctx, pos), ctx.buf.pos
        except FailedParse:
            ctx.buf.goto(pos)
            return None, pos

    def __str__(self):
        return '[%s]' % str(self.exp)


class CutParser(_Parser):
    def parse(self, ctx, pos):
        return None, pos

    def __str__(self):
        return '!'


class RuleRefParser(_Parser):
    def __init__(self, name):
        super(RuleRefParser, self).__init__()
        self.name = name

    def parse(self, ctx, pos):
        try:
            return ctx.rules[self.name].parse(ctx, pos), ctx.buf.pos
        except KeyError:
            raise FailedRef(ctx.buf, self.name)

    def __str__(self):
        return self.name


class NamedParser(_DecoratorParser):
    def __init__(self, name, exp):
        super(NamedParser, self).__init__(exp)
        assert isinstance(exp, _Parser), str(exp)
        self.name = name

    def parse(self, ctx, pos):
        tree, pos = self.exp.parse(ctx, pos)
        return Named(self.name, tree), pos

    def __str__(self):
        return '%s:%s' % (self.name, str(self.exp))


class SpecialParser(_Parser):
    def __init__(self, special):
        super(SpecialParser, self).__init__()
        self.special = special


class RuleParser(NamedParser):
    def parse(self, ctx, pos):
        ctx.buf.goto(pos)
        log.debug('enter %s %d %s', self.name, pos, ctx.buf.lookahead())
        try:
            tree, pos = self.exp.parse(ctx, pos)
            log.debug('exit %s', self.name)
        except FailedPattern:
            log.debug('failed %s', self.name)
            raise FailedParse(ctx.buf, self.name)
        except FailedParse as e:
            log.debug('failed %s', self.name)
            raise FailedMatch(ctx.buf, self.name, e.item)
        except:
            log.debug('failed %s', self.name)
            raise

        if not isinstance(tree, list):
            return tree, ctx.buf.pos
        else:
            result = defaultdict(list)
            for d in tree:
                if isinstance(d, Named):
                    result[d[0]].append(d[1])
#                elif isinstance(d, dict):
#                    result.update(d)
            for k, v in result.iteritems():
                if len(v) == 1:
                    result[k] = v[0]
            return result, ctx.buf.pos

    def __str__(self):
        return '%s = %s ;' % (self.name, str(self.exp))

class GrammarParser(object):
    def __init__(self, start, rules):
        super(GrammarParser, self).__init__()
        assert isinstance(rules, list), str(rules)
        self.rules = rules
        self.start = start

    def parse(self, buf):
        log.info('enter grammar')
        try:
            tree, _p = self.start.parse(Context(self.rules, buf), 0)
            return tree
        except:
            log.info('failed grammar')
            raise
        else:
            log.info('exit grammar')

    def _resolve(self, rules):
        for r in rules.values():
            r.resolve(rules)

    def __str__(self):
        return '\n\n'.join(str(rule) for rule in self.rules)

