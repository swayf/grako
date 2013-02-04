# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import logging
logging.basicConfig()
import grako
from regexp_parser import translate

def main():
    grammar = translate('(a|b)*')
    model = grako.parse('Regexp', grammar)
    open('genparser.py', 'w').write(model.render())
    model.parse('S0', 'aaabbaba')
    try:
        model.parse('S0', 'aaaCbbaba')
        raise Exception('Should not have parsed!')
    except grako.FailedParse:
        pass
    print(grammar)


if __name__ == '__main__':
    main()
