# FIXME: There could be a file buffer using random access
import re as regexp
from bisect import bisect as bisect
from collections import namedtuple
import logging
log = logging.getLogger('grako.buffering')

__all__ = ['Buffer']

RE = type(regexp.compile('.'))

PosLine = namedtuple('PosLine', ['pos', 'line'])
LineInfo = namedtuple('LineInfo', ['line', 'col', 'text'])

class Buffer(object):
    def __init__(self, text, whitespace=None):
        self.text = text
        self.pos = 0
        self.col = 0
        self.line = 0
        self.linecache = self._build_line_cache()
        self.whitespace = set(whitespace if whitespace else '\t \r\n')

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, p):
        self.goto(p)

    def atend(self):
        return self.pos >= len(self.text)

    def ateol(self):
        return self.atend() or self.current() in '\r\n'

    def current(self):
        if self.atend():
            return None
        return self.text[self.pos]

    def lookahead(self):
        if self.atend():
            return ''
        return self.text[self.pos:self.pos + 20].encode('string-escape') + '...'
#        p = bisect(self.linecache, PosLine(self.pos, 0))
#        start, _line = self.linecache[p]
#        return self.text[self.pos:start]

    def next(self):
        if self.atend():
            return None
        c = self.current()
        self._pos += 1
        if c == '\n':
            self.col = 0
            self.line += 1
        return c

    def goto(self, p):
        self._pos = max(0, min(len(self.text), p))
        self.line, self.col = self.line_info(p)

    def move(self, n):
        self.goto(self.pos + n)

    def eatwhitespace(self):
        while not self.atend() and self.current() in self.whitespace:
            self.next()

    def match(self, token, ignorecase=False):
        self.eatwhitespace()
        if self.atend():
            if token is None:
                return True
            return None

        p = self.pos
        if ignorecase:
            result = all(c == self.next().lower() for c in token.lower())
        else:
            result = all(c == self.next() for c in token)
        if result:
            log.debug("matched '%s' at %d - %s", token, self.pos, self.lookahead())
            return token
        else:
            self.goto(p)

    def matchre(self, pattern, ignorecase=False):
        self.eatwhitespace()
        if isinstance(pattern, basestring):
            re = regexp.compile(pattern, regexp.IGNORECASE if ignorecase else 0)
        else:
            re = pattern
        log.debug("matching'%s' at %d - %s", re.pattern, self.pos, self.lookahead())
        matched = re.match(self.text, self.pos)
        if matched:
            token = matched.group()
            log.debug("matched '%s' at %d - %s", token, self.pos, self.lookahead())
            self.move(len(token))
            return token

    def _build_line_cache(self):
        cache = [PosLine(-1, 0)]
        n = 0
        for i in xrange(len(self.text)):
            if self.text[i] == '\n':
                n += 1
                cache.append(PosLine(i , n))
        cache.append(PosLine(len(self.text), n + 1))
        return cache

    def line_info(self, pos=None):
        if pos is None:
            pos = self.pos
        p = bisect(self.linecache, PosLine(pos, 0))
        start, line = self.linecache[p - 1]
        col = pos - start - 1
        text = self.text[start:self.linecache[p].pos]
        return LineInfo(line, col, text)
