import logging
from grako.bootstrap import * #@UnusedWildImport
logging.basicConfig()
logging.getLogger().setLevel(logging.ERROR)

def main():
    print '-' * 40, 'phase 0'
    text = open('etc/grako.ebnf').read()
    g = GrakoGrammar()
    _result = g.parse('grammar', text)
    print g.ast
    open('0.ebnf', 'w').write(text)

    print '-' * 40, 'phase 1'
    text = open('0.ebnf').read()
    g = GrakoParserGenerator()
    g.parse('grammar', text)
    generated_grammar = str(g.ast['grammar'][0])
    print generated_grammar
    open('1.ebnf', 'w').write(generated_grammar)


    print '-' * 40, 'phase 2'
    text = open('1.ebnf').read()
    g = GrakoParserGenerator()
    g.parse('grammar', text)
    generated_grammar2 = str(g.ast['grammar'][0])
    print generated_grammar2
    open('2.ebnf', 'w').write(generated_grammar2.decode('string-escape'))

    print '-' * 40, 'phase 3'
    text = open('2.ebnf').read()
    g = GrakoParserGenerator()
    g.parse('grammar', text)
    generated_grammar3 = str(g.ast['grammar'][0])
    print generated_grammar3
    assert generated_grammar2 == generated_grammar3
    open('3.ebnf', 'w').write(generated_grammar3.decode('string-escape'))

if __name__ == '__main__':
    main()
