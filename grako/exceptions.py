

class FailedParse(Exception):
    def __init__(self, buf, item):
        self.buf = buf
        self.pos = buf.pos
        self.item = item

    @property
    def message(self):
        info = self.buf.line_info(self.pos)
        template = "{}:{} failed, expecting '{}':\n{}"
        return template.format(info.line, info.col, self.item, info.text)

    def __str__(self):
        return self.message


class FailedToken(FailedParse):
    def __init__(self, buf, token):
        super(FailedToken, self).__init__(buf, token)
        self.token = token


class FailedPattern(FailedParse):
    def __init__(self, buf, pattern):
        super(FailedPattern, self).__init__(buf, pattern)


class FailedMatch(FailedParse):
    def __init__(self, buf, name, item):
        super(FailedMatch, self).__init__(buf, item)
        self.name = name

    @property
    def message(self):
        return '<{}> {}'.format(self.name, super(FailedMatch, self).message)


class FailedRef(FailedParse):
    def __init__(self, buf, name):
        super(FailedRef, self).__init__(buf, name)
        self.name = name

    @property
    def message(self):
        info = self.buf.line_info(self.pos)
        template = '{}:{} could not resolve reference to rule "{}"'
        return template.format(info.line, info.col, self.name)

class FailedCut(FailedParse):
    def __init__(self, buf, nested):
        super(FailedCut, self).__init__(buf, nested.item)
        self.nested = nested

    @property
    def message(self):
        return self.nested.message
