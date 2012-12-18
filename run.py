import logging
from grako.bootstrap import *
logging.basicConfig()
logging.getLogger().setLevel(logging.ERROR)

def main():
    text = open('etc/grako.ebnf').read()
    g = GrakoGrammar()
    try:
        _result = g.parse('grammar', text)
    #    print len(result), result
        print g.ast
        print '------------'
    except Exception as e:
        print e
        raise

if __name__ == '__main__':
    main()
