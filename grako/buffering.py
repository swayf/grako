# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
# FIXME: There could be a file buffer using random access
import re as regexp
from bisect import bisect as bisect
from collections import namedtuple

__all__ = ['Buffer']

RETYPE = type(regexp.compile('.'))

PosLine = namedtuple('PosLine', ['pos', 'line'])
LineInfo = namedtuple('LineInfo', ['line', 'col', 'text'])

class Buffer(object):
    def __init__(self, text, whitespace=None, verbose=False):
        self.text = text
        self.linecache = self._build_line_cache()
        self.whitespace = set(whitespace if whitespace else '\t \r\n')
        self.verbose = verbose
        self.pos = 0
        self.col = 0
        self.line = 0

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
        return self.text[self.pos:self.pos + 20] + '...'
#        p = bisect(self.linecache, PosLine(self.pos, 0))
#        start, _line = self.linecache[p]
#        return self.text[self.pos:start]

    def next(self):
        if self.atend():
            return None
        c = self.current()
        self._pos += 1
        if c != '\n':
            self.col += 1
        else:
            self.col = 0
            self.line += 1
        return c

    def goto(self, p):
        self._pos = max(0, min(len(self.text), p))
        self.line, self.col, _ = self.line_info(p)

    def move(self, n):
        self.goto(self.pos + n)

    def eatwhitespace(self):
        while not self.atend() and self.current() in self.whitespace:
            self.next()

    def match(self, token, ignorecase=False):
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
            return token
        else:
            self.goto(p)

    def matchre(self, pattern, ignorecase=False):
        if isinstance(pattern, RETYPE):
            re = pattern
        else:
            re = regexp.compile(pattern, regexp.IGNORECASE if ignorecase else 0)
        matched = re.match(self.text, self.pos)
        if matched:
            token = matched.group()
            self.move(len(token))
            return token

    def _build_line_cache(self):
        cache = [PosLine(-1, 0)]
        n = 0
        for i, c in enumerate(self.text):
            if c == '\n':
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
