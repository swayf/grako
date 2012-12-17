import logging
from grako.bootstrap import GrakoGrammar
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

def main():
    text = open('grammar/grako.ebnf').read()
    g = GrakoGrammar()
    g.parse('grammar', text)

if __name__ == '__main__':
    main()
