Grako
=====

.. code :: python

**Grako** (for *grammar compiler*) is a tool that takes grammars in a variation of EBNF_ as input, and outputs a memoizing_ PEG_ parser in Python_.

.. _EBNF: http://en.wikipedia.org/wiki/Ebnf 
.. _memoizing: http://en.wikipedia.org/wiki/Memoization 
.. _PEG: http://en.wikipedia.org/wiki/Parsing_expression_grammar 
.. _Python: http://python.org

The generated parser consists of two classes:

* A base class derived from ``Parser`` wich implements the parser using one method for each grammar rule. The per-rule methods are named enclosing the rule's name with underscores to emphasize that they should not be tampered with (called, overriden, etc)::
 
    def _myrulename_(self):

* An abstract class with one method per grammar rule. Each method receives the as its single parameter the *Abstract Syntax Tree* (AST) built from the rule invocation::

    def myrulename(self, ast):
        return ast

The methods in the abstract parser class return the same AST received as parameter, but derived classes can override the methods to have them return something different (like a *Concrete Syntax Tree*).
       
The ASTs are dictionary-like objects that contain one keyed item for every named element in the original grammar rule. Items can be accessed through the standard dict syntax, ``ast['key']``, or as attributes, ``ast.key``.



Using the Tool
==============

**Grako** is run from the commandline like this::

    $ python -m grako

The *-h* and *--help* parameters provide full usage information::

    $ python -m grako --help
    Parse and translate an EBNF grammar into a Python parser for 
    the described language.

    Usage: grako <grammar.ebnf> [<name>] [options]
           grako (-h|--help)

    Arguments:
        <grammar.ebnf>  The EBNF grammar to generate a parser for.
        <name>          Optional name. It defaults to the base name
                        of the grammar file.

    Options:
        -o <filename>   write output to <filename>
        -v              produce verbose output
        -h, --help      show this help
    $



Using The Generated Parser
==========================

To use the generated parser, subclass the abstract parser, create an instance of it passing the text to parse, and invoke its ``parse`` method passing the starting rule's name as parameter::

    class MyParser(MyAbstractParser):
        pass

    parser = MyParser('text to parse')
    result = parser.parse('start')
    print result


The EBNF Grammar Syntax
=======================

**Grako** uses a small variation over standard EBNF_. A grammar consists of a sequence of one or more rules of the form:

    ``name = expre ;``

The expressions, in reverse order of precedence, can be:

    ``e1 | e2``
        Match either ``e1`` or ``e2``.

    ``e1 e2`` 
        Match ``e1`` and then match ``e2``.

    ``( e )``
        Grouping. Match ``e``.

    ``[ e ]``
        Optionally match ``e``.

    ``{ e }`` or ``{ e }*``
        Match ``e`` zero or more times.

    ``{ e }+`` or ``{ e }-``
        Match ``e`` one or more times.

    ``'<text>'`` or ``"<text>"``
        Match the text within the quotation marks.

    ``?/<regexp>/?``
        Match the Python_ regular expression ``<regexp>`` at the current text position. These
        matches do not consume spaces or comments. For that, place the ``regexp`` as the 
        only term in their own rule.

    ``rulename``
        Invoke the rule named ``rulename``. Note that rules that begin with an uppercase character
        don't advance the input over whitespace and comments.

    ``()``
        The empty expression. Match nothing.

    ``!``
        The cut expression. Prevent other options to be evaluated
        after this point.

    ``name:e``
        Add the result of ``e`` to the AST using ``name`` as key. If more than one item is
        added with the same ``name``, the entry is converted to a list.
    
    ``namei+:e``
        Add the result of ``e`` to the AST using ``name`` as key. Force the entry to be 
        a list even if only one element is added.

    ``<EOF>```
        Verify thad the end of the input text has been reached.

     ``(*`` comment ``*)``
        Comments may appear anywhere in the text.

**Warning**::

    Only elements that have a name assigned will be part of the generated
    AST. Other elements are simply discarded after they have been parsed.


Whitespace
==========

By default, **Grako** generated parsers skip the usual whitespace charactes (``\t`` ``\v`` ``\n`` ``\r`` and the space), but you can change that behaviour by passing a ``whitespace`` parameter to your parser::

    parser = MyParser(text, whitespace='\t ')

If you pass no whitespace characters::

    parser = MyParser(text, whitespace='')

then you will have to handle whitespace in your grammar as it's often done in PEG_.



Case Sensitivity
================

If your language is case insensitive, you can tell your parser so using the ``ignorecase`` parameter::

    parser = MyParser(text, ignorecase=True)

The change will affect both token and pattern matching.


Comments
========

There's no support for dealing with comments in this version of **Grako**.


Semantic Actions
================

There are no constructs for semantic actions in **Grako** grammars. This is on purpose, as we believe that semantic actions obscure the declarative nature of grammars, and provide for poor modularization from the parser execution perspective.

The overridable per-rule methods in the generated abstract parser provide enough opportunity to do post-processing, checks (like for inadecuate use of keywords), and AST transformation.

For finer-grained control it is enough to declare more rules, as the impact on the parsing times will be minimal.

If pre-processing is required, one can place invocations of empty rules where appropiate::

    myrule = first_part preproc {second_part} ;

    preproc = () ;

The abstract parser will contain a rule of of the form::

    def preproc(self, ast):
        return ast



License
=======

**Grako** is copyright 2012-2013 by `ResQSoft Inc.`_ and  `Juancarlo Añez`_

.. _`ResQSoft Inc.`:  http://www.resqsoft.com/
.. _`Juancarlo Añez`: mailto:apalala@gmail.com

You may use the tool under the terms of the `GNU General Public License (GPL) version 3`_ as described in the enclosed **LICENSE.txt** file.

.. _`GNU General Public License (GPL) version 3`:  http://www.gnu.org/licenses/gpl.html

The tool uses the docopt_ 0.5.0 library for command-line argument processing, and that is copyright 2012 by **Vladimir Keleshev**, and used under an `MIT License`_.

.. _docopt: https://github.com/halst/docopt/
.. _`MIT License`:  http://mit-license.org/


Credits
=======

These must be mentioned as contributors of thoughts, ideas, or code to the **Grako** project:

    **William Thompson** inspired the use of context managers with his `blog post`_ that I knew about through the invaluable `Python Weekly`_ nesletter, curated by **Rahul Chaudhary**

.. _`blog post`: http://dietbuddha.blogspot.com/2012/12/52python-encapsulating-exceptions-with.html 
.. _`Python Weekly`: http://www.pythonweekly.com/ 

There are several more, which will dutifully be credited, in time.

-------------------------

