import logging
from grako.bootstrap import GrakoGrammar
logging.basicConfig()
logging.getLogger().setLevel(logging.ERROR)

def main():
    text = open('grammar/grako.ebnf').read()
    g = GrakoGrammar()
    result = g.parse('grammar', text)
    print len(result), result
    print g.ast()

if __name__ == '__main__':
    main()
