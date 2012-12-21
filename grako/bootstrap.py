from grammar import * #@UnusedWildImport
from parsing import * #@UnusedWildImport

__all__ = ['GrakoGrammar', 'GrakoParserGenerator']

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
        self._call('word', 'call')

    def _pattern_(self):
        self._token('?/')
        self._pattern(r'(.*?)(?=/\?)', 'pattern')
        self._token('/?')

    def _cut_(self):
        self._token('!', 'cut')

    def _subexp_(self):
        self._token('(')
        self._call('expre', 'exp')
        self._token(')')

    def _optional_(self):
        self._token('[')
        self._call('expre', 'optional')
        self._token(']')

    def _plus_(self):
        if not self._try('-', 'symbol'):
            self._token('+', 'symbol')

    def _repeat_(self):
        self._token('{')
        self._call('expre', 'repeat')
        self._token('}')
        try:
            self._call('plus', 'plus')
        except FailedParse:
            pass

    def _special_(self):
        self._token('?(')
        self._pattern(r'(.*)\)?', 'special')

    def _atom_(self):
        p = self._pos
        try:
            self._call('void', 'atom')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._call('cut', 'atom')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._call('token', 'atom')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._call('call', 'atom')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._call('pattern', 'atom')
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
            self._call('atom', 'term')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._call('subexp', 'term')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._call('repeat', 'term')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._call('optional', 'term')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._call('special', 'term')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        raise FailedParse(self._buffer, 'term')

    def _named_(self):
        self._call('word', 'name')
        self._token(':')
        try:
            self._call('term', 'value')
            return
        except FailedParse as e:
            raise FailedCut(self._buffer, e)

    def _element_(self):
        p = self._pos
        try:
            self._call('named', 'element')
            return
        except FailedCut as e:
            raise e.nested
        except FailedParse:
            pass
        self._goto(p)
        try:
            self._call('term', 'element')
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
#            self._call('element', 'sequence')
#        except FailedParse:
#            self._goto(p)
#            raise
        while True:
            p = self._pos
            try:
                self._call('element', 'sequence')
            except FailedCut:
                self._goto(p)
                raise
            except FailedParse:
                self._goto(p)
                break


    def _choice_(self):
        self._call('sequence', 'options')
        while True:
            p = self._pos
            try:
                self._token('|')
                self._call('sequence', 'options')
            except FailedCut as e:
                self._goto(p)
                raise e.nested
            except FailedParse:
                self._goto(p)
                break

    def _expre_(self):
        self._call('choice', 'expre')

    def _rule_(self):
        self._call('word', 'name')
        self._token('=')
        self._call('expre', 'rhs')
        if not self._try(';'):
            self._token('.')

    def _grammar_(self):
        self._call('rule', 'rules')
        while True:
            p = self._pos
            try:
                self._call('rule', 'rules')
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
        return ast.term

    def named(self, ast):
        return ast

    def element(self, ast):
        return ast

    def sequence(self, ast):
        return ast

    def choice(self, ast):
        return ast

    def expre(self, ast):
        return ast

    def rule(self, ast):
        return ast

    def grammar(self, ast):
        return ast


def _simplify(x):
    if isinstance(x, list) and len(x) == 1:
        return _simplify(x[0])
    return x


class GrakoGrammar(AbstractGrakoGrammar):

    def token(self, ast):
        return ast

    def word(self, ast):
        return ast

    def call(self, ast):
        return ast

    def pattern(self, ast):
        return ast

    def cut(self, ast):
        return ast

    def subexp(self, ast):
        return _simplify(ast.exp)

    def optional(self, ast):
        return ast

    def plus(self, ast):
        return ast

    def repeat(self, ast):
        return ast

    def special(self, ast):
        return ast

    def atom(self, ast):
        return _simplify(ast.atom[0])

    def term(self, ast):
        return _simplify(ast.term[0])

    def named(self, ast):
        return ast

    def element(self, ast):
        return _simplify(ast.element)

    def sequence(self, ast):
        return _simplify(ast.sequence)

    def choice(self, ast):
        if len(ast.options) == 1:
            return _simplify(ast.options)
        return ast

    def expre(self, ast):
        return _simplify(ast.expre)

    def rule(self, ast):
        return ast

    def grammar(self, ast):
        return ast


class GrakoParserGenerator(AbstractGrakoGrammar):
    def token(self, ast):
        return TokenParser(ast.token[0])

    def word(self, ast):
        return ast.word[0]

    def call(self, ast):
        return RuleRefParser(ast.call[0])

    def pattern(self, ast):
        return PatternParser(ast.pattern[0])

    def cut(self, ast):
        return CutParser()

    def subexp(self, ast):
        return GroupParser(ast.exp[0])

    def optional(self, ast):
        return OptionalParser(ast.optional[0])

    def plus(self, ast):
        return ast

    def repeat(self, ast):
        if 'plus' in ast:
            return RepeatOneParser(ast.repeat[0])
        return RepeatParser(ast.repeat[0])

    def special(self, ast):
        return SpecialParser(ast.special[0])

    def atom(self, ast):
        return ast.atom[0]

    def term(self, ast):
        return ast.term[0]

    def named(self, ast):
        return NamedParser(ast.name[0], ast.value[0])

    def element(self, ast):
        return ast.element[0]

    def sequence(self, ast):
        if len(ast.sequence) == 1:
            return _simplify(ast.sequence)
        return SequenceParser(ast.sequence)

    def choice(self, ast):
        if len(ast.options) == 1:
            return ast.options[0]
        return ChoiceParser(ast.options)

    def expre(self, ast):
        return ast.expre[0]

    def rule(self, ast):
        return RuleParser(ast.name[0], ast.rhs[0])

    def grammar(self, ast):
        return GrammarParser(ast.rules)

