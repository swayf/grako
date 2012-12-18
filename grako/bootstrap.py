from grammar import * #@UnusedWildImport

__all__ = ['GrakoGrammar']

class GrakoGrammarBase(Grammar):
    def _token_(self):
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

    def _word_(self):
        return self._pattern(r'[A-Za-z0-9_]+', 'exp')

    def _pattern_(self):
        self._token('?/')
        self._pattern(r'(.*?)/\?', 'exp')

    def _cut_(self):
        self._token('!', 'exp')

    def _subexp_(self):
        self._token('(')
        self._rule('expre', 'exp')
        self._token(')')

    def _optional_(self):
        self._token('[')
        self._rule('expre')
        self._token(']')

    def _repeat_(self):
        self._token('{')
        expre = self._rule('expre')
        self._token('}')
        if not self._try('-'):
            self._try('+')
        return expre

    def _special_(self):
        p = self._pos()
        self._token('?')
        while self._buffer.next() != '?':
            if self._eof():
                raise FailedParse(self._buffer, '?')
        return self._buffer.text[p:self._pos()]

    def _atom_(self):
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


    def _term_(self):
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

    def _named_(self):
        name = self._rule('word', 'name')
        self._token(':')
        try:
            exp = self._rule('term', 'exp')
            return name, exp
        except FailedParse as e:
            raise FailedCut(self._buffer, e)

    def _element_(self):
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

    def _sequence_(self):
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


    def _option_(self):
        opts = [self._rule('sequence', 'exp')]
        while self._try('|'):
            opts.append(self._rule('sequence', 'exp'))
        return opts

    def _expre_(self):
        return self._option_()

    def _rule_(self):
        name = self._rule('word', 'name')
        self._token('=')
        expre = self._rule('expre', 'exp')
        if not self._try('.'):
            self._try(';')
        return name, expre

    def _grammar_(self):
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


class AbstractGrakoGrammar(GrakoGrammarBase):
    def token(self, ast):
        return ast

    def word(self, ast):
        return ast

    def pattern(self, ast):
        return ast

    def cut(self, ast):
        return ast

    def subexp(self, ast):
        return ast

    def optional(self, ast):
        return ast

    def repeat(self, ast):
        return ast

    def special(self, ast):
        return ast

    def atom(self, ast):
        return ast


    def term(self, ast):
        return ast

    def named(self, ast):
        return ast

    def element(self, ast):
        return ast

    def sequence(self, ast):
        return ast

    def option(self, ast):
        return ast

    def expre(self, ast):
        return ast

    def rule(self, ast):
        return ast

    def grammar(self, ast):
        return ast


class GrakoGrammar(AbstractGrakoGrammar):
    pass
