# -*- coding: utf-8 -*-
"""
This awkward set of tests tries to make Grako bang its head against iself.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
sys.path.append('tmp')
import os
import json
import logging
logging.basicConfig()
from grako.bootstrap import GrakoParser, GrakoGrammarGenerator
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger('grako.buffering').setLevel(logging.WARNING)
logging.getLogger('grako.grammar').setLevel(logging.WARNING)
logging.getLogger('grako.parsing').setLevel(logging.WARNING)

def main():
    if not os.path.isdir('tmp'):
        os.mkdir('tmp')
    print('-' * 20, 'phase 0 - parse using the bootstrap grammar')
    text = open('etc/grako.ebnf').read()
    g = GrakoParser('Grako')
    g.parse(text)
#    print(g.ast)
#    generated_grammar0 = str(g.ast['grammar'])
    open('tmp/0.ebnf', 'w').write(text)

    print('-' * 20, 'phase 1 - parse with parser generator')
    text = open('tmp/0.ebnf').read()
    g = GrakoGrammarGenerator('Grako')
    g.parse(text)
    generated_grammar1 = str(g.ast['grammar'])
    open('tmp/1.ebnf', 'w').write(generated_grammar1)
#    print(generated_grammar1)


    print('-' * 20, 'phase 2 - parse previous output with the parser generator')
    text = open('tmp/1.ebnf').read()
    g = GrakoGrammarGenerator('Grako')
    g.parse(text)
    generated_grammar2 = str(g.ast['grammar'])
#    print(generated_grammar2)
    open('tmp/2.ebnf', 'w').write(generated_grammar2)
    assert generated_grammar2 == generated_grammar1

    print('-' * 20, 'phase 3 - repeat')
    text = open('tmp/2.ebnf').read()
    g = GrakoGrammarGenerator('Grako')
    g.parse(text)
    generated_grammar3 = str(g.ast['grammar'])
#    print(generated_grammar3)
    open('tmp/3.ebnf', 'w').write(generated_grammar3)
    assert generated_grammar3 == generated_grammar2

    print('-' * 20, 'phase 4 - repeat')
    text = open('tmp/3.ebnf').read()
    g = GrakoGrammarGenerator('Grako')
    g.parse(text)
    parser = g.ast['grammar']
#    pprint(parser.first_sets, indent=2, depth=3)
    generated_grammar4 = str(parser)
#    print(generated_grammar4)
    open('tmp/4.ebnf', 'w').write(generated_grammar4)
    assert generated_grammar4 == generated_grammar3

    print('-' * 20, 'phase 5 - parse using the grammar model')
    text = open('tmp/4.ebnf').read()
    ast5 = parser.parse(text)
    open('tmp/5.ast', 'w').write(json.dumps(ast5, indent=2))
#    print(ast5)

    print('-' * 20, 'phase 6 - generate parser code')
    gencode6 = parser.render()
    open('tmp/gencode6.py', 'w').write(gencode6)

    print('-' * 20, 'phase 7 - import generated code')
    from gencode6 import GrakoParserBase as GenParser  # @UnresolvedImport
    print('-' * 20, 'phase 8 - compile using generated code')
    parser = GenParser(trace=False)
    result = parser.parse(text, 'grammar')
    assert result == parser.ast['grammar']
    open('tmp/8.ast', 'w').write(json.dumps(parser.ast.json, indent=2))
#    print(ast5)
#    print('=' * 20)
#    print(result)
#    assert result == ast5


if __name__ == '__main__':
    main()
