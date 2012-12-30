# coding: utf-8
"""
Parse and translate an EBNF grammar

Usage: grako [options] <grammar.ebnf>
       grako (-h|--help)

Options:
    -h, --help    print this help
"""
from docopt import docopt
from .buffering import Buffer
from .parsing import Parser
from .bootstrap import GrakoGrammarGenerator

def main():
    args = docopt(__doc__)
    filename = args['<grammar.ebnf>']
    text = open(filename, 'r').read()
    parser = GrakoGrammarGenerator(text)
    grammar = parser.parse()
    print grammar.render()

if __name__ == '__main__':
    main()
