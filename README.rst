Grako
=====

.. code :: python

**Grako** (for *grammar compiler*) is a tool that takes grammars in a variation of EBNF_ as input, and outputs a memoizing_ PEG_ parser in Python_.

.. _EBNF: http://en.wikipedia.org/wiki/Ebnf 
.. _memoizing: http://en.wikipedia.org/wiki/Memoization 
.. _PEG: http://en.wikipedia.org/wiki/Parsing_expression_grammar 
.. _Python: http://python.org

The generated parser consists of two classes:

* A base class derived from ``Parser`` wich implements the parser with one method for each grammar rule. Because the methods should not be called directly, they are named enclosing the rule's name with underscores::

    def _myrulename_(self):


* An abstract class with one method per grammar rule. Each method receives the *Abstract Syntax Tree* (AST) built for the rule as parameter. The methods in the abstract class return the same ast, but derived classes can override the methods to have them return anything they like::

    def myrulename(self, ast):
        return ast
       
The ASTs are dictionary-like objects that contain one keyed item for every named element in the original grammar rule. Items can be acced through the standard dict syntax (``ast['key']``) or as attributes (``ast.key``).

Using the Took
--------------

**Grako** is run from the commandline like this::

    $ python -m grako

The `-h` and `--help` parameters provide full usage information::

    $ python -m grako --help
    Parse and translate an EBNF grammar into a Python parser.

    Usage: grako <grammar.ebnf> [<name>]
           grako (-h|--help)

    Arguments:
        <grammar.ebnf>  The EBNF grammar to generate a parser for.
        <name>          Optional name. It defaults to the base name
                        of the grammar file.

    Options:
        -h, --help      print this help
    $

