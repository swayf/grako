# -*- coding: utf-8 -*-
"""
Parse and translate an EBNF grammar into a Python parser for
the described language.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import os
import argparse
from .buffering import Buffer
from .parsing import Parser
from .bootstrap import GrakoGrammarGenerator
from .exceptions import *

DESCRIPTION = ('Grako (for grammar compiler) takes grammars'
               ' in a variation of EBNF as input, and outputs a memoizing'
               ' PEG parser in Python.'
               )
argparser = argparse.ArgumentParser(prog='grako',
                                    description=DESCRIPTION
                                    )

argparser.add_argument('filename',
                       metavar='grammar',
                       help='The filename of the grammar to gencode( a parser for'
                       )
argparser.add_argument('-m', '--name',
                       nargs=1,
                       metavar='name',
                       help="An optional name for the grammar. It defaults to the basename of the grammar file's name"
                       )
argparser.add_argument('-o', '--outfile',
                       metavar='outfile',
                       help='specify where the output should go (default is stdout)'
                       )
argparser.add_argument('-t', '--trace',
                       help='produce verbose parsing output',
                       action='store_true'
                       )

def genmodel(name, grammar, trace=False, filename=None):
    parser = GrakoGrammarGenerator(name, trace=trace)
    return parser.parse(grammar, filename=filename)

def gencode(name, grammar, trace=False, filename=None):
    model = genmodel(name, grammar, trace=trace, filename=filename)
    return model.render()


def main():
    try:
        args = argparser.parse_args()
    except Exception as e:
        print(e)
        sys.exit(1)
    filename = args.filename
    outfile = args.outfile
    name = args.name
    if name is None:
        name = os.path.splitext(os.path.basename(filename))[0]
    if outfile and os.path.isfile(outfile):
        os.unlink(outfile)
    grammar = open(filename, 'r').read()
    try:
        parser = gencode(name, grammar, trace=args.trace, filename=filename)
        if outfile:
            dirname = os.path.dirname(outfile)
            if dirname and not os.path.isdir(dirname):
                os.makedirs(dirname)
            open(outfile, 'w').write(parser)
        else:
            print(parser)
    except GrakoException as e:
        print(e)

if __name__ == '__main__':
    main()
