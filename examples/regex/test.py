# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import grako
import regex_parser

PARSER_FILENAME = 'genparser.py'


def main():
    grammar = regex_parser.translate('(a|b)*')
    model = grako.genmodel('Regexp', grammar)
    model.parse('aaabbaba', 'S0')
    try:
        model.parse('aaaCbbaba', 'S0')
        raise Exception('Should not have parsed!')
    except grako.FailedParse:
        pass
    print('Grammar:', file=sys.stderr)
    print(grammar)
    sys.stdout.flush()
    with open(PARSER_FILENAME, 'w') as f:
        f.write(model.render())
    print('Generated parser saved as:', PARSER_FILENAME, file=sys.stderr)
    print(file=sys.stderr)


if __name__ == '__main__':
    main()
