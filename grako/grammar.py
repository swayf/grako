from .util import memoize
from .buffering import Buffer
from .exceptions import * #@UnusedWildImport
from .ast import AST
import logging
log = logging.getLogger('grako.grammar')

class Grammar(object):
    def __init__(self, whitespace=None, comments_re=None):
        self.whitespace = set(whitespace if whitespace else ' \n\r')
        self.comments_re = comments_re
        self._buffer = None
        self._ast_stack = []
        self._rule_stack = []

    def parse(self, rule_name, text):
        self._buffer = Buffer(text)
        self._push_ast()
        return self._call(rule_name, rule_name)

    @property
    def ast(self):
        return self._ast_stack[-1]

    def result(self):
        return self.ast['$'][0]

    def rulestack(self):
        return '.'.join(self._rule_stack)

    @property
    def _pos(self):
        return self._buffer.pos

    def _goto(self, pos):
        self._buffer.goto(pos)

    def _eatwhitespace(self):
        while self._buffer.current() in self.whitespace:
            self._buffer.next()

    def _eatcomments(self):
        if self.comments_re is not None:
            while self._buffer.matchre(self.comments_re):
                pass

    def _eof(self):
        self._next_token()
        if not self._buffer.atend():
            raise FailedParse(self._buffer, '<EOF>')

    def _next_token(self):
        self._eatcomments()
        self._eatwhitespace()

    def _call(self, name, node_name=None):
        self._rule_stack.append(name)
        self._next_token()
        pos = self._pos
        try:
            log.info('%s <<\n\t%s', self.rulestack(), self._buffer.lookahead())
            result, newpos = self._invoke_rule(name, pos)
            log.info('SUCCESS %s', self.rulestack())
            self._add_ast_node(node_name, result)
            self._goto(newpos)
            return result
        except FailedParse:
            log.info('FAILED %s', self.rulestack())
            self._goto(pos)
            raise
        finally:
            self._rule_stack.pop()

    @memoize
    def _invoke_rule(self, name, pos):
        rule = self._find_rule(name)
        self._push_ast()
        try:
            rule()
            node = self.ast
        finally:
            self._pop_ast()
        semantic_rule = self._find_semantic_rule(name)
        if semantic_rule:
            node = semantic_rule(node)
        return (node, self._pos)

    def _token(self, token, node_name=None):
        self._next_token()
        log.debug('match <%s> \n\t%s', token, self._buffer.lookahead())
        if self._buffer.match(token) is None:
            log.debug('failed <%s>', token)
            raise FailedToken(self._buffer, token)
        self._add_ast_node(node_name, token)
        return token

    def _try(self, token, node_name=None):
        self._next_token()
        log.debug('try <%s> \n\t%s', token, self._buffer.lookahead())
        if self._buffer.match(token) is not None:
            self._add_ast_node(node_name, token)
            return True


    def _pattern(self, pattern, node_name=None):
        self._next_token()
        log.debug('match %s\n\t%s', pattern, self._buffer.lookahead())
        token = self._buffer.matchre(pattern)
        if token is None:
            log.debug('failed %s', pattern)
            raise FailedPattern(self._buffer, pattern)
        self._add_ast_node(node_name, token)
        return token

    def _find_rule(self, name):
        rule = getattr(self, '_%s_' % name, None)
        if rule is None or not isinstance(rule, type(self._find_rule)):
            raise FailedRef(self._buffer, name)
        return rule

    def _find_semantic_rule(self, name):
        result = getattr(self, name, None)
        if result is None or not isinstance(result, type(self._find_rule)):
            return None
        return result

    def _push_ast(self):
        self._ast_stack.append(AST())

    def _pop_ast(self):
        return self._ast_stack.pop()

    def _add_ast_node(self, name, node):
        if name is not None and node:
            self.ast.add(name, node)
        return node


