# coding: utf-8
"""
Parse and translate an EBNF grammar into a Python parser.

Usage: grako <grammar.ebnf> [<name>]
       grako (-h|--help)

Arguments:
    <grammar.ebnf>  The EBNF grammar to generate a parser for.
    <name>          Optional name. It defaults to the base name
                    of the grammar file.

Options:
    -h, --help      print this help
"""
import os
from docopt import docopt
from .buffering import Buffer
from .parsing import Parser
from .bootstrap import GrakoGrammarGenerator

def main():
    args = docopt(__doc__)
    filename = args['<grammar.ebnf>']
    name = args['<name>']
    if name is None:
        name = os.path.splitext(os.path.basename(filename))[0]
    text = open(filename, 'r').read()
    parser = GrakoGrammarGenerator(name, text)
    grammar = parser.parse()
    print grammar.render()

if __name__ == '__main__':
    main()
