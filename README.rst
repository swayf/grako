Grako
=====

**Grako** (for *grammar compiler*) is a tool that takes grammars in a variation of EBNF_ as input, and outputs a memoizing_ PEG_ parser in Python_.

.. _EBNF: http://en.wikipedia.org/wiki/Ebnf 
.. _memoizing: http://en.wikipedia.org/wiki/Memoization 
.. _PEG: http://en.wikipedia.org/wiki/Parsing_expression_grammar 
.. _Python: http://python.org

The generated parser consists of two classes:

*    A base class derived from ``Parser`` wich implements the parser with one method for each grammar rule. Because the methods should not be called directly, they are named enclosing the rule's name with underscores::

    def _myrulename_(self):

* An abstract class with one method per grammar rule. Each method receives the *Abstract Syntax Tree* (AST) built for the rule as parameter. The methods in the abstract class return the same ast, but derived classes can override the methods to have them return anything they like:

.. code :: python

    def myrulename(self, ast):
        return ast
