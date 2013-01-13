# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
# FIXME: There could be a file buffer using random access
import re as regexp
from bisect import bisect as bisect
from collections import namedtuple

__all__ = ['Buffer']

RETYPE = type(regexp.compile('.'))

PosLine = namedtuple('PosLine', ['pos', 'line'])
LineInfo = namedtuple('LineInfo', ['line', 'col', 'start', 'text'])

class Buffer(object):
    def __init__(self, text, filename='unknown', whitespace=None, verbose=False):
        self.original_text = text
        self.text = text
        self.filename = filename
        self.whitespace = set(whitespace if whitespace else '\t \r\n')
        self.verbose = verbose
        self._fileinfo = self.get_fileinfo(text, filename)
        self._linecache = []
        self._preprocess()
        self._len = len(self.text)
        self._build_line_cache()
        self._pos = 0

    def _preprocess(self):
        pass

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, p):
        self._pos = max(0, min(len(self.text), p))

    @property
    def line(self):
        return self.line_info().line

    @property
    def col(self):
        return self.line_info().col

    def goto(self, p):
        self._pos = max(0, min(len(self.text), p))

    def atend(self):
        return self._pos >= self._len

    def ateol(self):
        return (
                self._pos >= self._len
                or self.text[self._pos] in '\r\n'
                )

    def current(self):
        if self.atend():
            return None
        return self.text[self._pos]

    def lookahead(self):
        if self.atend():
            return ''
        txt = (self.text[self._pos:self._pos + 80].split('\n')[0]).encode('unicode-escape')
        return '<%d:%d>%s' % (self.line + 1, self.col + 1, txt)

    def next(self):
        if self._pos >= self._len:
            return None
        try:
            return self.text[self._pos]
        finally:
            self._pos += 1

    def move(self, n):
        self.goto(self._pos + n)

    def eatwhitespace(self):
        while (self._pos < self._len
               and self.current() in self.whitespace
               ):
            self.next()

    def match(self, token, ignorecase=False):
        if self.atend():
            if token is None:
                return True
            return None

        p = self._pos
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
        matched = re.match(self.text, self._pos)
        if matched:
            token = matched.group()
            self.move(len(token))
            return token

    def get_fileinfo(self, text, filename):
        return [filename] * len(text.splitlines())

    def _build_line_cache(self):
        cache = [PosLine(-1, 0)]
        n = 0
        for i, c in enumerate(self.text):
            if c == '\n':
                n += 1
                cache.append(PosLine(i , n))
        cache.append(PosLine(len(self.text), n + 1))
        self._linecache = cache

    def line_info(self, pos=None):
        if pos is None:
            pos = self._pos
        n = bisect(self._linecache, PosLine(pos, 0))
        start, line = self._linecache[n - 1]
        col = pos - start - 1
        text = self.text[start:self._linecache[n].pos]
        return LineInfo(line, col, start, text)

    def get_line(self, n=None):
        if n is None:
            n = self.line
        start, line = self._linecache[n][:2]
        assert line == n
        end, _ = self._linecache[n + 1]
        return self.text[start + 1:end]
