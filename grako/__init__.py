# -*- coding: utf-8 -*-
"""
Parse and translate an EBNF grammar into a Python parser for
the described language.

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
import sys
import os
import argparse
from .buffering import Buffer
from .parsing import Parser
from .bootstrap import GrakoGrammarGenerator

DESCRIPTION = ('Grako (for grammar compiler) takes grammars'
               ' in a variation of EBNF as input, and outputs a memoizing'
               ' PEG parser in Python.'
               )
argparser = argparse.ArgumentParser(prog='grako',
                                    description=DESCRIPTION
                                    )

argparser.add_argument('filename',
                       metavar='grammar',
                       help='The filename of the grammar to generate a parser for'
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
argparser.add_argument('-v', '--verbose',
                       help='produce verbose output',
                       action='store_true'
                       )


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
    text = open(filename, 'r').read()
    parser = GrakoGrammarGenerator(name, text, verbose=args.verbose)
    grammar = parser.parse()
    text = grammar.render()
    if outfile:
        open(outfile, 'w').write(text)
    else:
        print(text)

if __name__ == '__main__':
    main()
