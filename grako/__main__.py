# coding: utf-8

from .bootstrap import grako_parser, WHITESPACE
from .buffering import Buffer
import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.FATAL)

def main():
    parser = grako_parser()
    grammar = str(parser)
#    print grammar
    g = grammar.replace('\n\n', '¶\n\n')
    tree = parser.parse(Buffer(g, WHITESPACE))
    print tree

if __name__ == '__main__':
    main()
