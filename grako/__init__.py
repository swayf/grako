# -*- coding: utf-8 -*-
"""
Parse and translate an EBNF grammar into a Python parser.

Usage: grako <grammar.ebnf> [<name>] [options]
       grako (-h|--help)

Arguments:
    <grammar.ebnf>  The EBNF grammar to generate a parser for.
    <name>          Optional name. It defaults to the base name
                    of the grammar file.

Options:
    -o <filename>   write output to <filename>
    -v              produce verbose output
    -h, --help      show this help
"""
from __future__ import print_function, division, absolute_import, unicode_literals
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
    outname = args['-o']
    if outname and os.path.isfile(outname):
        os.unlink(outname)
    text = open(filename, 'r').read()
    parser = GrakoGrammarGenerator(name, text, verbose=args['-v'])
    grammar = parser.parse()
    text = grammar.render()
    if outname:
        open(outname, 'w').write(text)
    else:
        print(text)

if __name__ == '__main__':
    main()
