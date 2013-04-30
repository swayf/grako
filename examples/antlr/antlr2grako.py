#!/usr/env/bin python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
from os import path
from antlr_parser import ANTLRParser as ANTLRParserBase


COMMENTS_RE = r'/\*(?:(?!\*/).)*?\*/|//[^\n]*?\n'


class ANTLRParser(ANTLRParserBase):
    def __init__(self, **kwargs):
        super(ANTLRParser, self).__init__(comments_re=COMMENTS_RE, **kwargs)

    def parse(self, text, filename=None, **kwargs):
        super(ANTLRParser, self).parse(text,
                                       'grammar',
                                       filename=filename,
                                       **kwargs)


def main(filename, trace):
    parser = ANTLRParser()
    with open(filename) as f:
        model = parser.parse(f.read(), filename=filename, trace=trace)
        print(model.gencode())

if __name__ == '__main__':
    if len(sys.argv) < 2:
        thisprog = path.basename(sys.argv[0])
        print(thisprog)
        print('Usage:')
        print('\t', thisprog, 'FILENAME.g [--trace]')
        sys.exit(1)
    main(sys.argv[1], '--trace' in sys.argv)
