# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from .ast import AST

class ParseContext(object):
    def __init__(self):
        self._ast_stack = []
        self._concrete_stack = [None]
        self._rule_stack = []
        self._cut_stack = [False]
        self._memoization_cache = dict()

    def _reset_context(self):
        self._ast_stack = []
        self._concrete_stack = [None]
        self._rule_stack = []
        self._cut_stack = [False]
        self._memoization_cache = dict()

    @property
    def ast(self):
        return self._ast_stack[-1]

    @ast.setter
    def ast(self, value):
        self._ast_stack[-1] = value

    def _push_ast(self):
        self._push_cst()
        self._ast_stack.append(AST())

    def _pop_ast(self):
        self._pop_cst()
        return self._ast_stack.pop()

    def _add_ast_node(self, name, node, force_list=False):
        if name is not None:  # and node:
            self.ast.add(name, node, force_list)
        return node

    @property
    def cst(self):
        return self._concrete_stack[-1]

    @cst.setter
    def cst(self, cst):
        self._concrete_stack[-1] = cst

    def _push_cst(self):
        self._concrete_stack.append(None)

    def _pop_cst(self):
        return self._concrete_stack.pop()

    def _add_cst_node(self, node):
        if node is None:
            return
        previous = self._concrete_stack[-1]
        if previous is None:
            self._concrete_stack[-1] = node
        elif previous == node:  # FIXME: Don't know how this happens, but it does
            return
        elif isinstance(previous, list):
            previous.append(node)
        else:
            self._concrete_stack[-1] = [previous, node]

    def _extend_cst(self, cst):
        if cst is None:
            return
        if self.cst is None:
            self.cst = cst
        elif isinstance(self.cst, list):
            if isinstance(cst, list):
                self.cst.extend(cst)
            else:
                self.cst.append(cst)
        elif isinstance(cst, list):
            self.cst = [self.cst] + cst
        else:
            self.cst = [self.cst, cst]

    def _is_cut_set(self):
        return self._cut_stack[-1]

    def _cut(self):
        self._cut_stack[-1] = True

    def _push_cut(self):
        self._cut_stack.append(False)

    def _pop_cut(self):
        return self._cut_stack.pop()



    def _rulestack(self):
        stack = '.'.join(self._rule_stack)
        if len(stack) > 60:
            stack = '...' + stack[-60:]
        return stack

    def _find_rule(self, name):
        return None

    def _find_semantic_rule(self, name):
        return None
