# -*- coding: utf-8 -*-
"""
Parse and translate an EBNF grammar into a Python parser for
the described language.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
from . import tool
from .exceptions import FailedParse

genmodel = tool.genmodel
gencode = tool.gencode


def main():
    tool.main()

if __name__ == '__main__':
    main()
