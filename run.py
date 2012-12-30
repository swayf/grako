from grako.bootstrap import *  # @UnusedWildImport
import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger('grako.buffering').setLevel(logging.WARNING)
logging.getLogger('grako.grammar').setLevel(logging.WARNING)
logging.getLogger('grako.parsing').setLevel(logging.WARNING)

def main():
    print '-' * 20, 'phase 0 - parse using the bootstrap grammar'
    text = open('etc/grako.ebnf').read()
    g = GrakoParser(text)
    g.parse()
#    print g.ast
#    generated_grammar0 = str(g.ast['grammar'][0])
    open('0.ebnf', 'w').write(text)

    print '-' * 20, 'phase 1 - parse with parser generator'
    text = open('0.ebnf').read()
    g = GrakoGrammarGenerator(text)
    g.parse()
    generated_grammar1 = str(g.ast['grammar'][0])
    open('1.ebnf', 'w').write(generated_grammar1)
#    print generated_grammar1


    print '-' * 20, 'phase 2 - parse previous output with the parser generator'
    text = open('1.ebnf').read()
    g = GrakoGrammarGenerator(text)
    g.parse()
    generated_grammar2 = str(g.ast['grammar'][0])
#    print generated_grammar2
    open('2.ebnf', 'w').write(generated_grammar2)
    assert generated_grammar2 == generated_grammar1

    print '-' * 20, 'phase 3 - repeat'
    text = open('2.ebnf').read()
    g = GrakoGrammarGenerator(text)
    g.parse()
    generated_grammar3 = str(g.ast['grammar'][0])
#    print generated_grammar3
    open('3.ebnf', 'w').write(generated_grammar3)
    assert generated_grammar3 == generated_grammar2

    print '-' * 20, 'phase 4 - repeat'
    text = open('3.ebnf').read()
    g = GrakoGrammarGenerator(text)
    g.parse()
    parser = g.ast['grammar'][0]
    generated_grammar4 = str(parser)
#    print generated_grammar4
    open('4.ebnf', 'w').write(generated_grammar4)
    assert generated_grammar4 == generated_grammar3

    print '-' * 20, 'phase 5 - parse using the grammar model'
    text = open('4.ebnf').read()
    ast5 = parser.parse('grammar', text)
    open('5.ast', 'w').write(str(ast5))
#    print ast5

    print '-' * 20, 'phase 6 - generate parser code'
    gencode6 = parser.render()
    open('gencode6.py', 'w').write(gencode6)

    print '-' * 20, 'phase 7 - import generated code'
    from gencode6 import AbstractGrakoParser as GenParser
    print '-' * 20, 'phase 8 - compile using generated code'
    parser = GenParser('Test', text)
    result = parser.parse('grammar')
    assert result == parser.ast
    open('8.ast', 'w').write(str(parser.ast))
#    print ast5
#    print '=' * 20
#    print result
#    assert result == ast5


if __name__ == '__main__':
    main()
