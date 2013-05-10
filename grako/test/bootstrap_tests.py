# -*- coding: utf-8 -*-
"""
This awkward set of tests tries to make Grako bang its head against iself.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
sys.path.append('tmp')
import os
import json
import pickle
from grako.rendering import NodeVisitor
from grako.bootstrap import (GrakoParser,
                             GrakoGrammarGenerator,
                             GrakoSemantics,
                             COMMENTS_RE
                             )


def main():
    if not os.path.isdir('tmp'):
        os.mkdir('tmp')
    print('-' * 20, 'phase 00 - parse using the bootstrap grammar')
    text = open('etc/grako.ebnf').read()
    g = GrakoParser('Grako', parseinfo=False)
    g.parse(text)
    open('tmp/00.ebnf', 'w').write(text)

    print('-' * 20, 'phase 01 - parse with parser generator')
    text = open('tmp/00.ebnf').read()
    g = GrakoGrammarGenerator('Grako', parseinfo=False)
    g.parse(text)
    generated_grammar1 = str(g.ast['grammar'])
    open('tmp/01.ebnf', 'w').write(generated_grammar1)

    print('-' * 20, 'phase 02 - parse previous output with the parser generator')
    text = open('tmp/01.ebnf').read()
    g = GrakoGrammarGenerator('Grako')
    g.parse(text)
    generated_grammar2 = str(g.ast['grammar'])
    open('tmp/02.ebnf', 'w').write(generated_grammar2)
    assert generated_grammar2 == generated_grammar1

    print('-' * 20, 'phase 03 - repeat')
    text = open('tmp/02.ebnf').read()
    g = GrakoParser('Grako', parseinfo=False)
    ast3 = g.parse(text)
    open('tmp/03.ast', 'w').write(json.dumps(ast3, indent=2))

    print('-' * 20, 'phase 04 - repeat')
    text = open('tmp/02.ebnf').read()
    g = GrakoGrammarGenerator('Grako')
    g.parse(text)
    parser = g.ast['grammar']
#    pprint(parser.first_sets, indent=2, depth=3)
    generated_grammar4 = str(parser)
    open('tmp/04.ebnf', 'w').write(generated_grammar4)
    assert generated_grammar4 == generated_grammar2

    print('-' * 20, 'phase 05 - parse using the grammar model')
    text = open('tmp/04.ebnf').read()
    ast5 = parser.parse(text)
    open('tmp/05.ast', 'w').write(json.dumps(ast5, indent=2))

    print('-' * 20, 'phase 06 - generate parser code')
    gencode6 = parser.codegen()
    open('tmp/g06.py', 'w').write(gencode6)

    print('-' * 20, 'phase 07 - import generated code')
    from g06 import GrakoParser as GenParser  # @UnresolvedImport

    print('-' * 20, 'phase 08 - compile using generated code')
    parser = GenParser(trace=False)
    result = parser.parse(text, 'grammar')
    assert result == parser.ast['grammar']
    ast8 = parser.ast['grammar']
    json8 = json.dumps(ast8, indent=2)
    open('tmp/08.ast', 'w').write(json8)
    assert ast5 == ast8
#    assert json8 == open('etc/check.js').read()

    print('-' * 20, 'phase 09 - Generate parser with semantics')
    text = open('etc/grako.ebnf').read()
    parser = GrakoGrammarGenerator('Grako')
    g9 = parser.parse(text)
    generated_grammar9 = str(g9)
    open('tmp/09.ebnf', 'w').write(generated_grammar9)
    assert generated_grammar9 == generated_grammar1

    print('-' * 20, 'phase 10 - Parse with a model using a semantics')
    g10 = g9.parse(text,
                   start_rule='grammar',
                   semantics=GrakoSemantics('Grako'),
                   comments_re=COMMENTS_RE
                   )
    generated_grammar10 = str(g10)
    open('tmp/10.ebnf', 'w').write(generated_grammar10)
    gencode10 = g10.codegen()
    open('tmp/g10.py', 'w').write(gencode10)

    print('-' * 20, 'phase 11 - Pickle the model and try again.')
    with open('tmp/11.grako', 'wb') as f:
        pickle.dump(g10, f, protocol=2)
    with open('tmp/11.grako', 'rb') as f:
        g11 = pickle.load(f)
    r11 = g11.parse(text,
                    start_rule='grammar',
                    semantics=GrakoSemantics('Grako'),
                    comments_re=COMMENTS_RE
                    )
    open('tmp/11.ebnf', 'w').write(str(110))
    gencode11 = r11.codegen()
    open('tmp/g11.py', 'w').write(gencode11)

    print('-' * 20, 'phase 12 - Visitor')

    class PrintNameVisitor(NodeVisitor):
        def __init__(self):
            self.visited = []

        def visit(self, o):
            self.visited.append(o.__class__.__name__)
            super(PrintNameVisitor, self).visit(o)

    v = PrintNameVisitor()
    g11.accept(v)
    open('tmp/12.txt', 'w').write('\n'.join(v.visited))

    print('-' * 20, 'phase 13 - Graphics')
    try:
        from grako.diagrams import draw
    except:
        print('PyGraphViz not found!')
    else:
        draw('tmp/13.jpg', g11)


if __name__ == '__main__':
    main()
