#FIXME: There could be a file buffer using random access
import re
from bisect import bisect
from collections import namedtuple
import logging
log = logging.getLogger('grako.buffering')

RE = type(re.compile('.'))

PosLine = namedtuple('PosLine', ['pos', 'line'])
LineInfo = namedtuple('LineInfo', ['pos', 'line', 'col', 'text'])

class Buffer(object):
    def __init__(self, text, whitespace=None):
        self.text = text
        self.pos = 0
        self.marks = []
        self.whitespace = set(whitespace) if whitespace else []
        self.linecache = self._build_line_cache()

    def atend(self):
        return self.pos >= len(self.text)

    def current(self):
        if self.atend():
            return None
        return self.text[self.pos]

    def lookahead(self):
        if self.atend():
            return ''
        p = bisect(self.linecache, PosLine(self.pos, 0))
        start, _line = self.linecache[p]
        return self.text[self.pos:start]

    def next(self):
        if self.atend():
            return None
        c = self.current()
        self.pos += 1
        return c

    def goto(self, p):
        self.pos = max(0, min(len(self.text), p))

    def move(self, n):
        self.goto(self.pos + n)

    def eatwhites(self):
        while self.current() in self.whitespace:
            self.next()

    def mark(self):
        self.marks.push(self.pos)
        return len(self.marks) - 1

    def unmark(self):
        return self.marks.pop()

    def goback(self, i=None):
        if i is None:
            self.pos = self.unmark()
        else:
            self.pos = self.marks[i]
            del self.marks[i:]

    def match(self, token):
        self.eatwhites()
        if self.atend():
            return token is None

        p = self.pos
        if all(c == self.next() for c in token):
            log.debug("matched '%s' at %d - %s", token, self.pos, self.lookahead())
            return token
        else:
            self.goto(p)

    def matchre(self, re):
        self.eatwhites()
        log.debug("matching'%s' at %d - %s", re.pattern, self.pos, self.lookahead())
        matched = re.match(self.text, self.pos)
        if matched:
            token = matched.group()
            log.debug("matched '%s' at %d - %s", token, self.pos, self.lookahead())
            self.move(len(token))
            return token

    def _build_line_cache(self):
        cache = [PosLine(0, 0)]
        n = 0
        for i in xrange(len(self.text)):
            if self.text[i] == '\n':
                n += 1
                cache.append(PosLine(i, n))
        cache.append(PosLine(len(self.text), n + 1))
        return cache

    def line_info(self, pos=None):
        if pos is None:
            pos = self.pos
        p = bisect(self.linecache, PosLine(pos, 0))
        start, line = self.linecache[p - 1]
        col = pos - start
        text = self.text[start:self.linecache[p].pos]
        return LineInfo(pos, line, col, text)
