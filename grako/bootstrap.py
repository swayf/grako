from grammar import * #@UnusedWildImport

class GrakoGrammar(Grammar):
    def __init__(self):
        super(GrakoGrammar, self).__init__(' ')

    def token(self):
        try:
            self._token('"')
            self._pattern(r"(?:[^']|\')*?")
            self._token('"')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        try:
            self._token("'")
            self._pattern(r'(?:[^"]|\")*?')
            self._token("'")
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        raise FailedMatch(self._buffer, '<"> or' + "<'>")

    def word(self):
        self._pattern(r'[A-Za-z0-9_]+', 'exp')

    def pattern(self):
        self._token('?/')
        self._pattern(r'(?!/\?)*', 'exp')
        self._token('/?')

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
        self._rule('expre')
        self._token('}')
        if not self._try('-'):
            self._try('+')

    def special(self):
        self._token('?')
        while self._buffer.next() != '?':
            if self._eof():
                raise FailedParse(self._buffer, '?')

    def atom(self):
        try:
            return self._rule('token', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        try:
            return self._rule('word', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        try:
            return self._rule('pattern', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        raise FailedParse(self._buffer, 'atom')


    def term(self):
        try:
            return self._rule('subexp', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        try:
            return self._rule('repeat', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        try:
            return self._rule('optional', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        try:
            return self._rule('special', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        try:
            return self._rule('atom', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        raise FailedParse(self._buffer, 'term')

    def named(self):
        try:
            self._rule('word', 'name')
            self._token(':')
            self._rule('term', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        try:
            return self._rule('atom', 'exp')
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        raise FailedParse(self._buffer, 'atom')

    def sequence(self):
        seq = []
        while True:
            p = self._pos()
            try:
                if not self._try('!'):
                    seq.append(self._rule('term', 'terms'))
                    self._try(',')
                else:
                    try:
                        # insert cut node here
                        seq.append(self._rule('sequence', 'terms'))
                    except FailedParse as e:
                        raise FailedCut(self._buffer, e)
            except FailedCut:
                self._goto(p)
                raise
            except FailedParse:
                self._goto(p)
                break
        return seq


    def option(self):
        self._rule('sequence', 'exp')
        while self._try('|'):
            self._rule('sequence', 'exp')

    def expre(self):
        return self.option()

    def rule(self):
        self._rule('word', 'name')
        self._token('=')
        self._rule('expre', 'exp')
        if not self._try('.'):
            self._try(';')

    def grammar(self):
        self._rule('rule', 'rules')
        while True:
            try:
                self._rule('rule', 'rules')
            except FailedParse:
                break
        self._eof()
