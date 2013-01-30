# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

class GrammarError(Exception):
    pass

class ParseError(Exception):
    pass

class SemanticError(Exception):
    pass

class MissingSemanticFor(SemanticError):
    pass


class FailedParseBase(ParseError):
    def __init__(self, buf, item):
        self.buf = buf
        self.pos = buf.pos
        self.item = item

    @property
    def message(self):
        return self.item

    def __str__(self):
        info = self.buf.line_info(self.pos)
        template = "{}:{} failed {} :\n{}\n{}^"
        return template.format(info.line + 1, info.col + 1, self.message, info.text, ' ' * info.col)


class FailedParse(FailedParseBase):
    pass


class FailedToken(FailedParse):
    def __init__(self, buf, token):
        super(FailedToken, self).__init__(buf, token)
        self.token = token

    @property
    def message(self):
        return "expecting '%s'" % self.token


class FailedPattern(FailedParse):
    def __init__(self, buf, pattern):
        super(FailedPattern, self).__init__(buf, pattern)
        self.pattern = pattern

    @property
    def message(self):
        return "expecting '%s'" % self.pattern


class FailedMatch(FailedParse):
    def __init__(self, buf, name, item):
        super(FailedMatch, self).__init__(buf, item)
        self.name = name

    @property
    def message(self):
        return "expecting '%s'" % self.name


class FailedRef(FailedParseBase):
    def __init__(self, buf, name):
        super(FailedRef, self).__init__(buf, name)
        self.name = name

    @property
    def message(self):
        return "could not resolve reference to rule '%s'" % self.name


class FailedCut(FailedParse):
    def __init__(self, buf, nested):
        super(FailedCut, self).__init__(buf, nested.item)
        self.nested = nested

    @property
    def message(self):
        return self.nested.message


class FailedChoice(FailedParse):
    @property
    def message(self):
        return 'no viable option'


class FailedReservedWord(FailedParse):
    @property
    def message(self):
        return "'%s' is a reserved word" % self.item


class FailedLookahead(FailedParse):
    @property
    def message(self):
        return 'failed lookahead'

