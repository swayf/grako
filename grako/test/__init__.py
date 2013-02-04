# -*- coding: utf-8 -*-
"""
The Grako test suite.
"""
from __future__ import print_function, division, absolute_import, unicode_literals

if __name__ == '__main__':
    from . import bootstrap_tests
    from . import  buffering_test

    bootstrap_tests.main()
    buffering_test.main()
