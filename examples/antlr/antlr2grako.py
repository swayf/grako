#!/usr/env/bin python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
from os import path
from grako.buffering import Buffer
from antlr_parser import ANTLRParser as ANTLRParserBase


#COMMENTS_RE = r'/\*.*?\*/|//[^\n]*?\n'
COMMENTS_RE = r'\/\*.*?\*\/'


class ANTLRParser(ANTLRParserBase):
    def parse(self, text, filename=None, **kwargs):
        super(ANTLRParser, self).parse(text,
                                       'grammar',
                                       filename=filename,
                                       **kwargs)


def main(filename, trace):
    parser = ANTLRParser()
    with open(filename) as f:
        buffer = Buffer(f.read(),
                        filename=filename,
                        comments_re=COMMENTS_RE,
                        trace=True)
        model = parser.parse(buffer, filename=filename, trace=trace)
        print(model.gencode())

if __name__ == '__main__':
    if len(sys.argv) < 2:
        thisprog = path.basename(sys.argv[0])
        print(thisprog)
        print('Usage:')
        print('\t', thisprog, 'FILENAME.g [--trace]')
        sys.exit(1)
    main(sys.argv[1], '--trace' in sys.argv)
