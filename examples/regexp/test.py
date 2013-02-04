# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import logging
logging.basicConfig()
import grako
import regexp_parser

PARSER_FILENAME = 'genparser.py'

def main():
    grammar = regexp_parser.translate('(a|b)*')
    model = grako.parse('Regexp', grammar)
    model.parse('S0', 'aaabbaba')
    try:
        model.parse('S0', 'aaaCbbaba')
        raise Exception('Should not have parsed!')
    except grako.FailedParse:
        pass
    with open(PARSER_FILENAME, 'w') as f:
        f.write(model.render())
    print('Generated parser saved as:', PARSER_FILENAME, file=sys.stderr)
    print('Grammar:')
    print(grammar)
    print()


if __name__ == '__main__':
    main()
