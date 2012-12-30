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
       
The ASTs are dictionary-like objects that contain one keyed item for every named element in the original grammar rule. Items can be acced through the standard dict syntax, ``ast['key']``, or as attributes, ``ast.key``.

Using the Tool
--------------

**Grako** is run from the commandline like this::

    $ python -m grako

The *-h* and *--help* parameters provide full usage information::

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

Using The Generated Parser
--------------------------

To use the generated parser, subclass the abstract parser, create an instance of it passing the text to parse, and invoke its ``parse`` method passing the starting rule name::

    class MyParser(MyAbstractParser):
        pass

    parser = MyParser('text to parse')
    result = parser.parse('start')
    print result

The EBNF Grammar Syntax
-----------------------

**Grako** uses a small variation over standard EBNF_. A grammar consists of a sequence of one or more rules of the form::

    name = expre ;

The expressions, in reverse order of precedence, can be:

    ``e1 | e2``
        Match either ``e1`` or ``e2``.

    ``e1 e2`` 
        Match ``e1`` and then match ``e2``.

    ``( e )``
        Grouping. Match ``e``.

    ``[ e ]``
        Optionally match ``e``.

    ``{ e }``
|
    ``{ e }*``
        Match ``e`` zero or more times.

    ``{ e }+``
    |
    ``{ e }-``
        Match ``e`` one or more times.

    ``'<text>'``
    |
    ``"<text>"``
        Match the text within the quotation marks.

    ``?/<regexp>/?``
        Match the Python_ regular expression ``<regexp>``.

    ``()``
        The empty expression. Match nothing.

    ``!``
        The cut expression. Prevent other options to be evaluated
        after this point.

    ``name:e``
        At the result of ``e`` to the AST using name ``name``.

