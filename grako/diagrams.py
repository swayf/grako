# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import itertools
import pygraphviz as pgv
from .visitors import GrammarVisitor


class GraphvizVisitor(GrammarVisitor):
    def __init__(self):
        super(GraphvizVisitor, self).__init__()
        self.top_graph = pgv.AGraph(directed=True,
                                    rankdir='LR',
                                    packMode='clust',
                                    splines='true'
                                    )
        self.stack = [self.top_graph]
        self.node_count = 0

    @property
    def graph(self):
        return self.stack[-1]

    def draw(self, filename):
        self.graph.layout(prog='dot')
        # WARNING: neato generated graphics hang my GPU
        # self.graph.layout(prog='neato')
        self.graph.draw(filename)

    def push_graph(self, name=None):
        if name is None:
            self.node_count += 1
            name = 'g%d' % self.node_count
        self.stack.append(self.graph.add_subgraph(name))
        return self.graph

    def pop_graph(self):
        self.stack.pop()
        pass

    def node(self, name, id=None, **attr):
        if id is None:
            self.node_count += 1
            id = 'n%d' % self.node_count
        else:
            try:
                return self.graph.get_node(id)
            except KeyError:
                pass
        self.graph.add_node(id, **attr)
        n = self.graph.get_node(id)
        n.attr['label'] = name
#        n.attr['shape'] = 'circle'
        return n

    def tnode(self, name, **attr):
        return self.node(name, **attr)

    def dot(self):
        n = self.node('')
        n.attr['shape'] = 'point'
        n.attr['size'] = 0.0000000001
        n.attr['label'] = ''
        return n

    def start_node(self):
        return self.dot()

    def ref_node(self, name):
        n = self.node(name)
        n.attr['shape'] = 'box'
        return n

    def rule_node(self, name, **attr):
        n = self.node(name, **attr)
        n.attr['shape'] = 'parallelogram'
        return n

    def end_node(self):
        n = self.node('')
        n.attr['shape'] = 'point'
        n.attr['width'] = 0.2
        return n

    def edge(self, s, e, **attr):
        self.graph.add_edge(s, e, **attr)
        edge = self.graph.get_edge(s, e)
        # edge.attr['arrowhead'] = 'normal'
        edge.attr['arrowhead'] = 'none'
        return edge

    def redge(self, s, e):
        edge = self.edge(s, e)
        edge.attr['dir'] = 'back'
        return edge

    def zedge(self, s, e):
        edge = self.edge(s, e, len=0.000001)
        return edge

    def nedge(self, s, e):
        return self.edge(s, e, style='invisible', dir='none')

    def path(self, p):
        self.graph.add_path(p)

    def subgraph(self, name, bunch):
        self.top_graph.add_subgraph(name)

    def concat(*args):
        return list(itertools.chain(*args))

    def _visit_decorator(self, d):
        return d.exp.accept(self)

    def visit_grammar(self, g):
        self.push_graph(g.name + '0')
        try:
            vrules = [r.accept(self) for r in reversed(g.rules)]
        finally:
            self.pop_graph()
        self.push_graph(g.name + '1')
        try:
            # link all rule starting nodes with invisible edges
            starts = [self.node(r.name, id=r.name) for r in g.rules]
            for n1, n2 in zip(starts, starts[1:]):
                # self.nedge(n1, n2)
                pass
        finally:
            self.pop_graph()
        s, t = vrules[0][0], vrules[-1][1]
        return (s, t)

    def visit_rule(self, r):
        self.push_graph(r.name)
        try:
            i, e = self._visit_decorator(r)
            s = self.rule_node(r.name, id=r.name)
            self.edge(s, i)
            t = self.end_node()
            self.edge(e, t)
            return (s, t)
        finally:
            self.pop_graph()

    def visit_ruleref(self, rr):
        n = self.ref_node(rr.name)
        return (n, n)

    def visit_special(self, s):
        n = self.node(s.special)
        return (n, n)

    def visit_override(self, o):
        return self._visit_decorator(o)

    def visit_named(self, n):
        return self._visit_decorator(n)

    def visit_cut(self, c):
        # c = self.node('>>')
        # return (c, c)
        return None

    def visit_optional(self, o):
        i, e = self._visit_decorator(o)
        ni = self.dot()
        ne = self.dot()
        self.zedge(ni, i)
        self.edge(ni, ne)
        self.zedge(e, ne)
        return (ni, ne)

    def visit_repeat(self, r):
        g = self.push_graph()
        g.graph_attr['rankdir'] = 'TB'
        try:
            i, e = self._visit_decorator(r)
            ni = self.dot()
            self.edge(ni, i)
            self.edge(e, ni)
            return (ni, ni)
        finally:
            self.pop_graph()

    def visit_repeatplus(self, r):
        i, e = self._visit_decorator(r)
        if i == e:
            self.redge(e, i)
        else:
            self.edge(e, i)
        return (i, e)

    def visit_group(self, g):
        return self._visit_decorator(g)

    def visit_choice(self, c):
        vopt = [o.accept(self) for o in c.options]
        ni = self.dot()
        ne = self.dot()
        for i, e in vopt:
            self.edge(ni, i)
            self.edge(e, ne)
        return (ni, ne)

    def visit_sequence(self, s):
        vseq = [x.accept(self) for x in s.sequence]
        vseq = [x for x in vseq if x is not None]
        i, _ = vseq[0]
        _, e = vseq[-1]
        if i != e:
            bunch = zip([a for _, a in vseq[:-1]],
                        [b for b, _ in vseq[1:]])
            for n, n1 in bunch:
                self.edge(n, n1)
        return (i, e)

    def visit_lookahead(self, l):
        i, e = self._visit_decorator(l)
        n = self.node('&')
        self.edge(n, e)
        return (n, e)

    def visit_lookahead_not(self, l):
        i, e = self._visit_decorator(l)
        n = self.node('!')
        self.edge(n, e)
        return (n, e)

    def visit_pattern(self, p):
        n = self.tnode(p.pattern)
        return (n, n)

    def visit_token(self, t):
        n = self.tnode(t.token)
        return (n, n)

    def visit_void(self, v):
        n = self.dot()
        return (n, n)

    def visit_eof(self, v):
        # n = self.node('$')
        # return (n, n)
        return None


def draw(filename, grammar):
    visitor = GraphvizVisitor()
    grammar.accept(visitor)
    visitor.draw(filename)
