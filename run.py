import logging
from grako.bootstrap import *
logging.basicConfig()
logging.getLogger().setLevel(logging.ERROR)

def main():
    text = open('etc/grako.ebnf').read()
    g = GrakoGrammar()
    _result = g.parse('grammar', text)
    print g.ast

if __name__ == '__main__':
    main()
