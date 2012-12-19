import logging
from grako.bootstrap import * #@UnusedWildImport
logging.basicConfig()
logging.getLogger().setLevel(logging.ERROR)

def main():
    print '-' * 40, 'phase 0'
    text = open('etc/grako.ebnf').read()
    g = GrakoGrammar()
    _result = g.parse('grammar', text)
#    print g.ast
    open('0.ebnf', 'w').write(text)

    print '-' * 40, 'phase 1'
    g = GrakoParserGenerator()
    g.parse('grammar', text)
    generated_grammar = str(g.ast['grammar'][0])
    print generated_grammar
    open('1.ebnf', 'w').write(generated_grammar)


    print '-' * 40, 'phase 2'
    g = GrakoParserGenerator()
    g.parse('grammar', generated_grammar)
    generated_grammar2 = open('1.ebnf', 'r').read()
    print generated_grammar2
    open('2.ebnf', 'w').write(generated_grammar2)

    print '-' * 40, 'phase 3'
    g = GrakoParserGenerator()
    g.parse('grammar', generated_grammar2)
    generated_grammar3 = open('2.ebnf', 'r').read()
    print generated_grammar3
    open('3.ebnf', 'w').write(generated_grammar3)

if __name__ == '__main__':
    main()
