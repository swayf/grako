from grammar import * #@UnusedWildImport

__all__ = ['GrakoGrammar']

class GrakoGrammarBase(Grammar):

    def _void_(self):
        self._token('()', 'void')

    def _token_(self):
        p = self._pos
        try:
            self._token("'")
            self._pattern(r"(?:[^'\\]|\\')*", 'token')
            self._token("'")
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._token('"')
            self._pattern(r'(?:[^"\\]|\\")*', 'token')
            self._token('"')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        raise FailedParse(self._buffer, '<"> or' + "<'>")

    def _word_(self):
        self._pattern(r'[A-Za-z0-9_]+', 'word')

    def _call_(self):
        self._rule('word', 'call')

    def _pattern_(self):
        self._token('?/')
        self._pattern(r'(.*?)(?=/\?)', 'pattern')
        self._token('/?')

    def _cut_(self):
        self._token('!', 'cut')

    def _subexp_(self):
        self._token('(')
        self._rule('expre', 'exp')
        self._token(')')

    def _optional_(self):
        self._token('[')
        self._rule('expre', 'optional')
        self._token(']')

    def _plus_(self):
        if not self._try('-', 'symbol'):
            self._token('+', 'symbol')

    def _repeat_(self):
        self._token('{')
        self._rule('expre', 'repeat')
        self._token('}')
        try:
            self._rule('plus', 'plus')
        except FailedParse:
            pass

    def _special_(self):
        p = self._pos
        self._token('?')
        while self._buffer.next() != '?':
            if self._eof():
                raise FailedParse(self._buffer, '?')
        return self._buffer.text[p:self._pos]

    def _atom_(self):
        p = self._pos
        try:
            self._rule('void', 'atom')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._rule('cut', 'atom')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._rule('token', 'atom')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._rule('call', 'atom')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._rule('pattern', 'atom')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        raise FailedParse(self._buffer, 'atom')


    def _term_(self):
        p = self._pos
        try:
            self._rule('atom', 'term')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._rule('subexp', 'term')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._rule('repeat', 'term')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._rule('optional', 'term')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._rule('special', 'term')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        raise FailedParse(self._buffer, 'term')

    def _named_(self):
        self._rule('word', 'name')
        self._token(':')
        try:
            self._rule('term', 'value')
            return
        except FailedParse as e:
            raise FailedCut(self._buffer, e)

    def _element_(self):
        p = self._pos
        try:
            self._rule('named', 'named')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._rule('term', 'element')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        raise FailedParse(self._buffer, 'element')

    def _sequence_(self):
#        p = self._pos
#        try:
#            self._rule('element', 'elements')
#        except FailedParse:
#            self._goto(p)
#            raise
        while True:
            p = self._pos
            try:
                if not self._try('!'):
                    self._try(',')
                    self._rule('element', 'elements')
                else:
                    try:
                        # insert cut node here
                        self._rule('sequence', 'elements')
                    except FailedParse as e:
                        raise FailedCut(self._buffer, e)
            except FailedCut:
                self._goto(p)
                raise
            except FailedParse:
                self._goto(p)
                break


    def _option_(self):
        self._rule('sequence', 'seq')
        while True:
            p = self._pos
            try:
                self._token('|')
                self._rule('sequence', 'opts')
            except FailedCut as e:
                self._goto(p)
                raise e.nested
            except FailedParse:
                self._goto(p)
                break

    def _expre_(self):
        self._rule('option', 'expre')

    def _rule_(self):
        self._rule('word', 'name')
        self._token('=')
        self._rule('expre', 'rhs')
        if not self._try(';'):
            self._token('.')

    def _grammar_(self):
        self._rule('rule', 'rules')
        while True:
            p = self._pos
            try:
                self._rule('rule', 'rules')
            except FailedParse:
                self._goto(p)
                break
        self._next_token()
        self._eof()


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
    def token(self, ast):
        return ast

    def word(self, ast):
        return ast.word

    def pattern(self, ast):
        return ast

    def cut(self, ast):
        return ast

    def subexp(self, ast):
        return ast.exp

    def optional(self, ast):
        return ast

    def plus(self, ast):
        return ast

    def repeat(self, ast):
        return ast

    def special(self, ast):
        return ast

    def atom(self, ast):
        return ast.atom

    def term(self, ast):
        return ast.term

    def named(self, ast):
        return ast

    def element(self, ast):
        if 'named' in ast:
            return ast
        return ast.element

    def sequence(self, ast):
        return ast.elements

    def option(self, ast):
        if 'opts' in ast:
            result = AST(opts=ast.seq)
            result.add('opts', ast.opts)
            return result
        return ast.seq

    def expre(self, ast):
        return ast.expre

    def rule(self, ast):
        return ast

    def grammar(self, ast):
        return ast

