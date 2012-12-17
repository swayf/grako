from grammar import * #@UnusedWildImport

__all__ = ['GrakoGrammar']

class GrakoGrammar(Grammar):
    def __init__(self):
        super(GrakoGrammar, self).__init__(' \n\r')

    def token(self):
        p = self._pos()
        try:
            self._token("'")
            result = self._pattern(r"(?:[^'\\]|\\')*")
            self._token("'")
            return result
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._token('"')
            result = self._pattern(r'(?:[^"\\]|\\")*')
            self._token('"')
            return result
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        raise FailedParse(self._buffer, '<"> or' + "<'>")

    def word(self):
        return self._pattern(r'[A-Za-z0-9_]+', 'exp')

    def pattern(self):
        self._token('?/')
        self._pattern(r'(.*?)/\?', 'exp')

    def cut(self):
        self._token('!', 'exp')

    def subexp(self):
        self._token('(')
        self._rule('expre', 'exp')
        self._token(')')

    def optional(self):
        self._token('[')
        self._rule('expre')
        self._token(']')

    def repeat(self):
        self._token('{')
        expre = self._rule('expre')
        self._token('}')
        if not self._try('-'):
            self._try('+')
        return expre

    def special(self):
        p = self._pos()
        self._token('?')
        while self._buffer.next() != '?':
            if self._eof():
                raise FailedParse(self._buffer, '?')
        return self._buffer.text[p:self._pos()]

    def atom(self):
        p = self._pos()
        try:
            return self._rule('cut', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            return self._rule('token', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            return self._rule('word', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            return self._rule('pattern', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        raise FailedParse(self._buffer, 'atom')


    def term(self):
        p = self._pos()
        try:
            return self._rule('atom', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            return self._rule('subexp', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            return self._rule('repeat', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            return self._rule('optional', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            return self._rule('special', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        raise FailedParse(self._buffer, 'term')

    def named(self):
        name = self._rule('word', 'name')
        self._token(':')
        try:
            exp = self._rule('term', 'exp')
            return name, exp
        except FailedParse as e:
            raise FailedCut(self._buffer, e)

    def element(self):
        p = self._pos()
        try:
            return self._rule('named', 'name')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            return self._rule('term', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        raise FailedParse(self._buffer, 'named')

    def sequence(self):
        seq = []
        while True:
            p = self._pos()
            try:
                if not self._try('!'):
                    seq.append(self._rule('element', 'terms'))
                    self._try(',')
                else:
                    try:
                        # insert cut node here
                        seq.append(self._rule('sequence', 'terms'))
                    except FailedParse as e:
                        raise FailedCut(self._buffer, e)
            except FailedCut:
                raise
            except FailedParse:
                self._goto(p)
                break
        return seq


    def option(self):
        opts = [self._rule('sequence', 'exp')]
        while self._try('|'):
            opts.append(self._rule('sequence', 'exp'))
        return opts

    def expre(self):
        return self.option()

    def rule(self):
        name = self._rule('word', 'name')
        self._token('=')
        expre = self._rule('expre', 'exp')
        if not self._try('.'):
            self._try(';')
        return name, expre

    def grammar(self):
        rules = [self._rule('rule', 'rules')]
        while True:
            p = self._pos()
            try:
                rules.append(self._rule('rule', 'rules'))
            except FailedParse:
                self._goto(p)
                break
        self._next_token()
        self._eof()
        return rules
