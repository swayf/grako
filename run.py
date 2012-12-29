from grako.bootstrap import *  # @UnusedWildImport
import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger('grako.buffering').setLevel(logging.WARNING)
logging.getLogger('grako.grammar').setLevel(logging.WARNING)
logging.getLogger('grako.parsing').setLevel(logging.INFO)

def main():
    print '-' * 40, 'phase 0'
    text = open('etc/grako.ebnf').read()
    g = GrakoGrammar(text)
    g.parse('grammar')
#    print g.ast
#    generated_grammar0 = str(g.ast['grammar'][0])
    open('0.ebnf', 'w').write(text)

    print '-' * 40, 'phase 1'
    text = open('0.ebnf').read()
    g = GrakoParserGenerator(text)
    g.parse('grammar')
    generated_grammar1 = str(g.ast['grammar'][0])
    open('1.ebnf', 'w').write(generated_grammar1)
#    print generated_grammar1


    print '-' * 40, 'phase 2'
    text = open('1.ebnf').read()
    g = GrakoParserGenerator(text)
    g.parse('grammar')
    generated_grammar2 = str(g.ast['grammar'][0])
#    print generated_grammar2
    open('2.ebnf', 'w').write(generated_grammar2)
    assert generated_grammar2 == generated_grammar1

    print '-' * 40, 'phase 3'
    text = open('2.ebnf').read()
    g = GrakoParserGenerator(text)
    g.parse('grammar')
    g.parse('grammar')
    generated_grammar3 = str(g.ast['grammar'][0])
#    print generated_grammar3
    open('3.ebnf', 'w').write(generated_grammar3)
    assert generated_grammar3 == generated_grammar2

    print '-' * 40, 'phase 4'
    text = open('3.ebnf').read()
    g = GrakoParserGenerator(text)
    g.parse('grammar')
    parser = g.ast['grammar'][0]
    generated_grammar4 = str(parser)
#    print generated_grammar4
    open('4.ebnf', 'w').write(generated_grammar4)
    assert generated_grammar4 == generated_grammar3

    print '-' * 40, 'phase 5'
    text = open('4.ebnf').read()
    _result = parser.parse('grammar', text)
#    print _result

    print '-' * 40, 'phase 6'
    print parser.render()


if __name__ == '__main__':
    main()
