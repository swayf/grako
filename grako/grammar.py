from .buffering import Buffer
from .exceptions import * #@UnusedWildImport
from .util import AttributeDict, memoize
import logging
log = logging.getLogger('grako.grammar')

class Grammar(object):
    def __init__(self, whitespace, comments_re=None):
        self.whitespace = set(whitespace)
        self.comments_re = comments_re
        self._buffer = None
        self._ast_stack = []
        self._rule_stack = []

    def parse(self, rule_name, text):
        self._buffer = Buffer(text)
        self._push_ast()
        return self._rule(rule_name)

    def ast(self):
        return self._ast_stack[-1]

    def result(self):
        return self.ast()['$'][0]

    def rulestack(self):
        return '.'.join(self._rule_stack)

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

    def _rule(self, name, node_name=None):
        self._rule_stack.append(name)
        try:
            log.info('%s <<\n\t%s', self.rulestack(), self._buffer.lookahead())
            self._next_token()
            pos = self._pos()
            result, node, newpos = self._invoke_rule(name, pos)
            self._goto(newpos)
            self._add_ast_node(node_name, node)
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
            result = rule()
            node = self.ast()
            log.info('SUCCESS %s', self.rulestack())
        finally:
            self._pop_ast()
        self._add_ast_node('$', result)
        return (result, node, self._pos())

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
        return self._buffer.match(token) is not None

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
        rule = getattr(self, name, None)
        if rule is None or not isinstance(rule, type(self._find_rule)):
            raise FailedRef(self._buffer, name)
        return rule

    def _push_ast(self):
        self._ast_stack.append(AttributeDict())

    def _pop_ast(self):
        return self._ast_stack.pop()

    def _add_ast_node(self, name, node):
        if name is not None:
            self.ast()[name].append(node)
        return node


